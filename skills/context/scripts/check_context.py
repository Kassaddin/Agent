#!/usr/bin/env python3
"""Read-only validation and selected-source freshness checks for project context."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "smokes" / "scripts"))
try:
    from validate_report import AccessError, BoundaryAccess, INIT
    from check_artifacts import heading_anchors
except (ImportError, OSError, SystemExit):
    print(json.dumps({"status": "error", "read_only": True, "reason": "The sibling Smokes and Init helpers with PyYAML are required"}))
    raise SystemExit(2)


class BudgetExpired(Exception):
    pass


def relative_path(value):
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError("Paths must be nonempty relative strings")
    if "\\" in value or ":" in value or any(ord(char) < 32 for char in value):
        raise ValueError("Use portable relative paths without URIs or control characters")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Paths must remain inside their configured resource")
    return value


def unique_records(records, required, optional=()):
    if not isinstance(records, list):
        raise ValueError("Expected a record list")
    result = {}
    for record in records:
        if not isinstance(record, dict) or set(record) - set(required) - set(optional) or not set(required) <= set(record):
            raise ValueError("Record fields do not match the context contract")
        key = record["id"]
        if not isinstance(key, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", key) or key in result:
            raise ValueError("Record IDs must be unique lowercase names")
        result[key] = record
    return result


class ContextCheck:
    def __init__(self, boundaries, index=None, *, max_sources=30, max_bytes=2097152, timeout=20):
        if type(max_sources) is not int or type(max_bytes) is not int or min(max_sources, max_bytes, timeout) <= 0 or not math.isfinite(timeout):
            raise ValueError("Provide positive finite check limits")
        self.access = BoundaryAccess(boundaries)
        if self.access.data["conversation"]["investigate_within_scope"] != "act":
            raise AccessError("Investigation requires authorization")
        self.resources = {item["id"]: item for item in self.access.data["resources"]["local"]}
        self.remotes = {item["id"]: item for item in self.access.data["resources"]["remote"]}
        self.remote_ids = set(self.remotes)
        self.primary = self.access.data["project"]["primary_local_id"]
        self.root = Path(os.path.abspath(self.resources[self.primary]["path"]))
        self.index = Path(index) if index else self.root / "context/index.yaml"
        if not self.index.is_absolute():
            self.index = self.root / self.index
        self.index = Path(os.path.abspath(self.index))
        try:
            self.index.relative_to(self.root)
        except ValueError:
            raise ValueError("The context index must be in the primary project") from None
        self.max_sources, self.max_bytes = max_sources, max_bytes
        self.deadline = time.monotonic() + timeout
        self.cache = {}

    def tick(self):
        self.access.unchanged()
        if time.monotonic() >= self.deadline:
            raise BudgetExpired

    def read(self, path):
        self.tick()
        if not self.access.allowed(path):
            return {"state": "blocked", "reason": "Read permission or resolved scope is insufficient"}
        key = os.path.normcase(str(path.resolve()))
        if key in self.cache:
            return self.cache[key]
        try:
            if not path.exists():
                value = {"state": "missing", "reason": "The authorized path does not exist"}
            elif not path.is_file():
                value = {"state": "unsupported", "reason": "A regular file is required"}
            else:
                with path.open("rb") as stream:
                    raw = stream.read(self.max_bytes + 1)
                if len(raw) > self.max_bytes:
                    value = {"state": "unsupported", "reason": "File exceeds the check's byte budget"}
                elif b"\0" in raw:
                    value = {"state": "unsupported", "reason": "A format-specific text adapter is needed"}
                else:
                    value = {"state": "current", "sha256": hashlib.sha256(raw).hexdigest(), "text": raw.decode("utf-8-sig")}
        except UnicodeDecodeError:
            value = {"state": "unsupported", "reason": "UTF-8 text or an authorized format adapter is needed"}
        except OSError:
            value = {"state": "unavailable", "reason": "The authorized file could not be read"}
        self.cache[key] = value
        return value

    def validate(self, data):
        required = {"schema_version", "project", "layout", "root_view", "views", "sources", "topics"}
        if not isinstance(data, dict) or set(data) != required or type(data["schema_version"]) is not int or data["schema_version"] != 1:
            raise ValueError("Invalid context index shape or schema version")
        if data["project"] != self.access.data["project"]["name"] or data["layout"] not in ("one_view", "by_area"):
            raise ValueError("Project identity or context layout is invalid")
        views = unique_records(data["views"], {"id", "path", "source_ids"})
        sources = unique_records(data["sources"], {"id", "resource", "path", "role", "owner", "reviewed_sha256", "reviewed_at"}, {"section"})
        topics = unique_records(data["topics"], {"id", "decision_source_id", "view_ids"})
        if not isinstance(data["root_view"], str) or data["root_view"] not in views or not views or not sources:
            raise ValueError("A root view and sources are required")
        if (data["layout"] == "one_view" and len(views) != 1) or (data["layout"] == "by_area" and len(views) < 2):
            raise ValueError("Layout does not match the number of context views")
        view_paths = set()
        for view in views.values():
            path = relative_path(view["path"])
            if path in view_paths or Path(path).suffix.casefold() not in {".md", ".markdown"}:
                raise ValueError("Context views require distinct Markdown paths")
            if (view["id"] == data["root_view"] and path != "CONTEXT.md") or (view["id"] != data["root_view"] and not path.startswith("context/areas/")):
                raise ValueError("Views must use the owned CONTEXT.md or context/areas paths")
            view_paths.add(path)
            ids = view["source_ids"]
            if not isinstance(ids, list) or not ids or not all(isinstance(item, str) and item in sources for item in ids) or len(set(ids)) != len(ids):
                raise ValueError("View source references must be known and unique")
        for source in sources.values():
            relative_path(source["path"])
            if source["resource"] not in self.resources and source["resource"] not in self.remote_ids:
                raise ValueError("Source resource is not configured in boundaries")
            if source["role"] not in {"glossary", "decision_record", "documentation"} or not isinstance(source["owner"], str) or not source["owner"].strip():
                raise ValueError("Source role or owner is invalid")
            if source.get("section") is not None and (not isinstance(source["section"], str) or not source["section"].strip()):
                raise ValueError("Source sections must be nonempty anchor strings or null")
            fingerprint, checked = source["reviewed_sha256"], source["reviewed_at"]
            if fingerprint is not None and (not isinstance(fingerprint, str) or not re.fullmatch(r"[a-f0-9]{64}", fingerprint)):
                raise ValueError("Invalid reviewed content fingerprint")
            if checked is not None and (not isinstance(checked, str) or not INIT._timestamp(checked)):
                raise ValueError("Use a timezone-bearing review timestamp")
            if (fingerprint is None) != (checked is None):
                raise ValueError("A reviewed fingerprint and timestamp must be recorded together")
            if source["resource"] == self.primary and (source["path"] == "CONTEXT.md" or source["path"].startswith("context/areas/") or source["path"] in {"context/index.yaml", self.index.relative_to(self.root).as_posix()}):
                raise ValueError("Derived context files cannot be canonical context sources")
        for topic in topics.values():
            if topic["decision_source_id"] not in sources or sources[topic["decision_source_id"]]["role"] != "decision_record":
                raise ValueError("Each topic needs one designated decision-record source")
            if not isinstance(topic["view_ids"], list) or not topic["view_ids"] or not all(isinstance(item, str) and item in views for item in topic["view_ids"]):
                raise ValueError("Topic views must exist")
        roles = {sources[key]["role"] for key in views[data["root_view"]]["source_ids"]}
        if not {"glossary", "documentation"} <= roles:
            raise ValueError("The root view needs glossary and documentation sources")
        return views, sources, topics

    def run(self, *, view_ids=None, source_ids=None, changed_ids=None):
        if self.access.allowed(self.index):
            try:
                self.index.resolve().relative_to(self.root.resolve())
            except ValueError:
                raise AccessError("The index resolves outside the primary project") from None
        loaded = self.read(self.index)
        if loaded["state"] != "current":
            return {"status": "blocked" if loaded["state"] == "blocked" else "partial", "read_only": True,
                    "index": str(self.index), "index_state": loaded["state"], "views": [], "sources": [], "reason": loaded["reason"]}
        data = INIT.load_yaml(loaded["text"])
        views, sources, topics = self.validate(data)
        requested_views, explicit_sources, changed = list(view_ids or []), list(source_ids or []), set(changed_ids or [])
        if not all(item in views for item in requested_views) or not all(item in sources for item in explicit_sources + list(changed)):
            raise ValueError("Requested context view or source ID is unknown")
        affected = {key for key, view in views.items() if changed.intersection(view["source_ids"])}
        selected_views = list(dict.fromkeys((sorted(affected) if changed else [data["root_view"]]) + requested_views))
        selected_sources = list(dict.fromkeys([key for name in selected_views for key in views[name]["source_ids"]] + explicit_sources + sorted(changed)))
        view_results, source_results, warnings = [], [], []
        for key in selected_views:
            path = self.root / views[key]["path"]
            try:
                value = self.read(path)
            except BudgetExpired:
                value = {"state": "not_checked", "reason": "Time budget exhausted"}
            item = {"id": key, "path": str(path), **{k: v for k, v in value.items() if k not in {"text", "sha256"}}}
            if value["state"] == "current":
                item["word_count"] = len(value["text"].split())
                if item["word_count"] > 700:
                    warnings.append(f"View {key} exceeds the 700-word starting orientation budget; assess area views or necessary scope.")
            view_results.append(item)
        for position, key in enumerate(selected_sources):
            source = sources[key]
            item = {"id": key, "role": source["role"], "owner": source["owner"], "resource": source["resource"], "path": source["path"]}
            try:
                self.tick()
                if position >= self.max_sources:
                    value = {"state": "not_checked", "reason": "Selected-source budget exhausted"}
                elif source["resource"] in self.remote_ids:
                    remote = self.remotes[source["resource"]]
                    if remote["access"]["status"] not in {"ready", "limited"} or remote["effective_mode"] not in {"read", "write"}:
                        value = {"state": "unavailable", "reason": "The configured remote has no accepted usable read access"}
                    else:
                        value = {"state": "unsupported", "reason": "A read-only Search remote adapter is required; no remote request was made"}
                else:
                    path = Path(self.resources[source["resource"]]["path"]) / source["path"]
                    value = self.read(path)
                    if value["state"] == "current":
                        derived = [self.index, *(self.root / view["path"] for view in views.values())]
                        if any(path.resolve() == candidate.resolve() for candidate in derived):
                            raise ValueError("A source resolves to a derived context file")
                        if path.suffix.casefold() not in {".md", ".markdown", ".yaml", ".yml", ".json", ".txt"}:
                            value = {"state": "unsupported", "reason": "A format-specific adapter is required"}
                        elif source.get("section") and (path.suffix.casefold() not in {".md", ".markdown"} or source["section"] not in heading_anchors(value["text"])[0]):
                            value = {"state": "needs_review", "actual_sha256": value["sha256"], "reason": "The recorded section was not found under supported heading rules"}
                        elif source["reviewed_sha256"] != value["sha256"]:
                            value = {"state": "needs_review", "actual_sha256": value["sha256"], "reason": "Content changed since review" if source["reviewed_sha256"] else "No reviewed content fingerprint is recorded"}
                        else:
                            value = {"state": "current", "actual_sha256": value["sha256"]}
            except BudgetExpired:
                value = {"state": "not_checked", "reason": "Time budget exhausted"}
            item.update({k: v for k, v in value.items() if k not in {"text", "sha256"}})
            if item["state"] != "current":
                affected.update(name for name, view in views.items() if key in view["source_ids"])
            source_results.append(item)
        self.access.unchanged()
        complete = all(item["state"] == "current" for item in view_results + source_results)
        return {"status": "complete" if complete else "partial", "read_only": True, "project": data["project"],
                "index": str(self.index), "layout": data["layout"], "boundaries_sha256": self.access.hash,
                "selected_view_ids": selected_views, "selected_source_ids": selected_sources,
                "not_selected_source_ids": [key for key in sources if key not in selected_sources],
                "affected_view_ids": sorted(affected), "views": view_results, "sources": source_results,
                "topic_records": {key: item["decision_source_id"] for key, item in topics.items()}, "warnings": warnings,
                "coverage_note": "Only selected local text sources were checked. Unchanged content is not approval, factual proof, document readiness, or task completion."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boundaries", required=True, type=Path)
    parser.add_argument("--index", type=Path)
    parser.add_argument("--view", action="append", default=[])
    parser.add_argument("--source-id", action="append", default=[])
    parser.add_argument("--changed-source-id", action="append", default=[])
    parser.add_argument("--max-sources", type=int, default=30)
    parser.add_argument("--max-bytes", type=int, default=2097152)
    parser.add_argument("--timeout", type=float, default=20)
    args = parser.parse_args(argv)
    try:
        result = ContextCheck(args.boundaries, args.index, max_sources=args.max_sources, max_bytes=args.max_bytes, timeout=args.timeout).run(
            view_ids=args.view, source_ids=args.source_id, changed_ids=args.changed_source_id)
        print(json.dumps(result, ensure_ascii=False))
        return 1 if result["status"] == "blocked" else 0
    except AccessError:
        print(json.dumps({"status": "blocked", "read_only": True, "reason": "Current boundaries do not authorize this check"}))
        return 1
    except (OSError, ValueError, TypeError, KeyError, INIT.yaml.YAMLError, BudgetExpired):
        print(json.dumps({"status": "error", "read_only": True, "reason": "Context index, dependency, input, or check budget is invalid or unavailable"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
