#!/usr/bin/env python3
"""Validate Smokes reports and optionally inspect current snapshot drift; never fix."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import html
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
INIT_PATH = Path(__file__).resolve().parents[2] / "init" / "scripts" / "validate_boundaries.py"
SPEC = importlib.util.spec_from_file_location("smokes_init_validator", INIT_PATH)
if SPEC is None or SPEC.loader is None:
    raise SystemExit("The sibling Init skill is required.")
INIT = importlib.util.module_from_spec(SPEC)
try:
    SPEC.loader.exec_module(INIT)
except (OSError, ImportError, SystemExit):
    raise SystemExit("The sibling Init skill and PyYAML are required.")

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "references" / "report.schema.json"
SEVERITIES = ("critical", "high", "medium", "low")
PRIORITIES = ("P0", "P1", "P2", "P3")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON object key")
        result[key] = value
    return result


def _constant(value):
    raise ValueError("Non-finite JSON values are not supported")


def strict_json(text):
    return json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant)


class AccessError(ValueError):
    pass


class BoundaryAccess:
    def __init__(self, file):
        self.file = Path(file).absolute()
        raw = self.file.read_bytes()
        self.hash = digest(raw)
        self.data = INIT.load_yaml(raw.decode("utf-8-sig"))
        errors, _ = INIT.validate_document(self.data, require_active=True)
        if errors:
            raise AccessError("Active boundaries are invalid: " + "; ".join(errors))
        self.sources = self.data["resources"]["local"]
        self.keys = [(INIT._path_key(source["path"]), source) for source in self.sources]

    @staticmethod
    def covers(key, source, candidate):
        if key == candidate:
            return True
        if source["kind"] != "directory" or not source["recursive"] or key[0] != candidate[0]:
            return False
        separator = "\\" if key[0] == "windows" else "/"
        return candidate[1].startswith(key[1].rstrip(separator) + separator)

    def matching(self, path):
        candidate = INIT._path_key(str(Path(path).absolute()))
        return [source for key, source in self.keys if self.covers(key, source, candidate)]

    def decision(self, path, operation):
        sources = self.matching(path)
        values = [source["permissions"][operation] for source in sources]
        if not values:
            return self.data["defaults"]["unmatched_resource"]
        return "never" if "never" in values else "ask" if "ask" in values else "act"

    def allowed(self, path, operation="read"):
        path = Path(path).absolute()
        if self.decision(path, operation) != "act":
            return False
        try:
            target = path.resolve(strict=False)
        except (OSError, RuntimeError):
            return False
        if not self.matching(target) or self.decision(target, operation) != "act":
            return False
        if ".git" in {part.casefold() for part in path.parts + target.parts}:
            if operation != "read" or self.data["version_control"]["operations"]["inspect"] != "act":
                return False
        return True

    def require(self, path, operation="read"):
        if not self.allowed(path, operation):
            raise AccessError(f"{operation} is not authorized for the requested location")

    def unchanged(self):
        if digest(self.file.read_bytes()) != self.hash:
            raise AccessError("Boundaries changed; reload and validate before continuing")


def summary_for(report):
    findings = report["findings"]
    severity = Counter(item["severity"] for item in findings)
    priority = Counter(item["priority"] for item in findings)
    gaps = any(item["status"] != "complete" for item in report["coverage"])
    blocked = any(item["status"] == "blocked" for item in report["coverage"]) and not any(item["state"] in ("read", "missing") for item in report["scope"]["snapshots"])
    return {
        "total": len(findings), "confirmed": sum(item["certainty"] == "confirmed" for item in findings),
        "needs_review": sum(item["certainty"] == "needs_review" for item in findings),
        "by_severity": {key: severity[key] for key in SEVERITIES},
        "by_priority": {key: priority[key] for key in PRIORITIES},
        "audit_status": "blocked" if blocked else "partial" if gaps else "complete",
    }


def fingerprint(finding):
    content = {key: finding[key] for key in ("check_id", "locations", "evidence")}
    return digest(json.dumps(content, sort_keys=True, ensure_ascii=True).encode("utf-8"))


def finalize(report):
    unique = {}
    for finding in report["findings"]:
        finding["fingerprint"] = fingerprint(finding)
        unique.setdefault(finding["fingerprint"], finding)
    report["findings"] = list(unique.values())
    for number, finding in enumerate(report["findings"], 1):
        finding["id"] = f"SMK-{number:03d}"
    report["summary"] = summary_for(report)
    return report


def validate_report(report):
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = []
    INIT._check_schema(report, schema, schema, "$", errors)
    if errors:
        return errors
    if not INIT._timestamp(report["created_at"]):
        errors.append("created_at must be an ISO 8601 timestamp with timezone")
    if report["summary"] != summary_for(report):
        errors.append("Summary does not match findings and coverage")
    ids = [item["id"] for item in report["findings"]]
    if len(ids) != len(set(ids)):
        errors.append("Finding IDs are not unique")
    hashes = [item["fingerprint"] for item in report["findings"]]
    if len(hashes) != len(set(hashes)):
        errors.append("Findings contain duplicate fingerprints")
    snapshots = report["scope"]["snapshots"]
    paths = [item["path"] for item in snapshots]
    if len(paths) != len(set(paths)):
        errors.append("Snapshots contain duplicate paths")
    for item in snapshots:
        if (item["state"] == "read") != (item["sha256"] is not None):
            errors.append("Only readable snapshots may contain a content hash")
        if item["bytes"] is not None and item["bytes"] < 0:
            errors.append("Snapshot byte counts must be nonnegative")
    checked_paths = set(report["scope"]["requested"]) | set(paths) | {report["scope"]["boundaries_file"]}
    for item in report["coverage"]:
        checked_paths.update(item["paths"])
    for finding in report["findings"]:
        if finding["fingerprint"] != fingerprint(finding):
            errors.append(f"{finding['id']}: fingerprint does not match evidence")
        if finding["certainty"] == "needs_review" and finding["remediation"]["mode"] != "decision_required":
            errors.append(f"{finding['id']}: needs-review findings require a decision")
        if not set(finding["depends_on"]).issubset(ids):
            errors.append(f"{finding['id']}: unknown dependency")
        for item in finding["locations"] + finding["evidence"]:
            checked_paths.add(item["path"])
            if item["line"] is not None and item["line"] < 1:
                errors.append(f"{finding['id']}: line numbers must be positive")
        for evidence in finding["evidence"]:
            snapshot = next((item for item in snapshots if item["path"] == evidence["path"]), None)
            if snapshot is None or (evidence["kind"] == "source_excerpt" and snapshot["state"] != "read"):
                errors.append(f"{finding['id']}: evidence must refer to an appropriate captured snapshot")
    for path in checked_paths:
        try:
            INIT._path_key(path)
        except ValueError:
            errors.append("Report paths must be literal absolute paths")
    graph = {item["id"]: item["depends_on"] for item in report["findings"]}
    known_ids = set(graph)
    followers = {node: [] for node in graph}
    pending = {node: len(set(parents) & known_ids) for node, parents in graph.items()}
    for node, parents in graph.items():
        for parent in set(parents) & known_ids:
            followers[parent].append(node)
    ready = [node for node in graph if pending[node] == 0]
    visited = 0
    while ready:
        node = ready.pop()
        visited += 1
        for follower in followers[node]:
            pending[follower] -= 1
            if pending[follower] == 0:
                ready.append(follower)
    if visited != len(graph):
        errors.append("Finding dependencies contain a cycle")
    return errors


def current_state(report, access, max_bytes=2097152):
    states = []
    for snapshot in report["scope"]["snapshots"]:
        access.unchanged()
        path = Path(snapshot["path"])
        item = {"path": str(path), "state": "blocked", "modify_authorized": access.allowed(path, "modify"), "create_authorized": access.allowed(path, "create")}
        if access.allowed(path):
            try:
                if not path.exists():
                    item["state"] = "unchanged" if snapshot["state"] == "missing" else "missing"
                elif path.is_file() and path.stat().st_size <= max_bytes:
                    with path.open("rb") as stream:
                        raw = stream.read(max_bytes + 1)
                    if len(raw) > max_bytes:
                        item["state"] = "unsupported"
                    elif snapshot["sha256"] is not None:
                        item["state"] = "unchanged" if digest(raw) == snapshot["sha256"] else "changed"
                    elif snapshot["state"] == "missing":
                        item["state"] = "changed"
                    else:
                        item["state"] = "unverified"
                        item["reason"] = "The original snapshot has no comparable content hash."
                else:
                    item["state"] = "unsupported"
            except OSError:
                item["state"] = "unreadable"
        states.append(item)
    access.unchanged()
    return states


def render_markdown(report):
    summary = report["summary"]
    def safe(value):
        return html.escape(str(value).replace("\r", " ").replace("\n", " ")).replace("[", "\\[").replace("]", "\\]")
    lines = [f"# Smokes report: {safe(report['report_id'])}", "", f"Created: {safe(report['created_at'])}", "",
             f"{summary['total']} unique findings: {summary['confirmed']} confirmed; {summary['needs_review']} need review.",
             f"Coverage: {summary['audit_status']}.", "",
             "Severity: " + ", ".join(f"{key} {summary['by_severity'][key]}" for key in SEVERITIES) + ".",
             "Priority: " + ", ".join(f"{key} {summary['by_priority'][key]}" for key in PRIORITIES) + ".", ""]
    for finding in sorted(report["findings"], key=lambda item: (item["priority"], SEVERITIES.index(item["severity"]), item["id"])):
        lines.extend([f"## {finding['id']}: {safe(finding['title'])}", "",
                      f"{finding['severity']} / {finding['priority']} / {finding['certainty']}", ""])
        for location in finding["locations"]:
            suffix = f":{location['line']}" if location["line"] else ""
            lines.append(f"- Location: {safe(location['path'])}{suffix}")
        lines.extend(["", f"Impact: {safe(finding['impact'])}", "", f"Proposed correction: {safe(finding['proposed_fix'])}", "",
                      f"Acceptance check: {safe(finding['acceptance_check'])}", "",
                      f"Remediation: {finding['remediation']['mode']} — {safe(finding['remediation']['reason'])}", ""])
        for evidence in finding["evidence"]:
            lines.append(f"Evidence ({evidence['kind']}):")
            lines.append(f"> {safe(evidence['text'])}")
        if finding["depends_on"]:
            lines.extend(["", "Depends on: " + ", ".join(finding["depends_on"])])
        lines.append("")
    lines.extend(["## Check coverage", ""])
    for item in report["coverage"]:
        lines.append(f"- {safe(item['check_id'])}: {item['status']}. {safe(item['reason'])}")
    lines.extend(["", "The JSON report is authoritative. This report does not authorize fixes.", ""])
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--boundaries", required=True, type=Path)
    parser.add_argument("--check-current", action="store_true")
    args = parser.parse_args(argv)
    try:
        access = BoundaryAccess(args.boundaries)
        access.require(args.report)
        with args.report.open("rb") as stream:
            raw = stream.read(10485761)
        if len(raw) > 10485760:
            raise ValueError("Report exceeds the 10 MiB validation limit")
        report = strict_json(raw.decode("utf-8-sig"))
        errors = validate_report(report)
        result = {"valid": not errors, "errors": errors}
        if not errors and args.check_current:
            result["boundaries_changed_since_report"] = report["scope"]["boundaries_sha256"] != access.hash
            result["current"] = current_state(report, access)
        access.unchanged()
    except (OSError, ValueError, UnicodeError, INIT.yaml.YAMLError):
        result = {"valid": False, "errors": ["Report or active boundaries are invalid, inaccessible, or outside approved access."]}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
