#!/usr/bin/env python3
"""Read-only, bounded local search using the active Init boundary contract."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

# Importing a helper must not create caches in a source or installed skill.
sys.dont_write_bytecode = True
INIT = Path(__file__).resolve().parents[2] / "init" / "scripts" / "validate_boundaries.py"
SPEC = importlib.util.spec_from_file_location("search_init_validator", INIT)
if SPEC is None or SPEC.loader is None:
    raise SystemExit("The sibling Init validator is required.")
BOUNDARIES = importlib.util.module_from_spec(SPEC)
try:
    SPEC.loader.exec_module(BOUNDARIES)
except (OSError, ImportError, SystemExit):
    raise SystemExit("The sibling Init skill and its PyYAML dependency are required.")


GENERATED = {"node_modules", "dist", "build", ".next", ".venv", "venv", "__pycache__", "coverage"}


def worker_permission(data):
    decision = data["conversation"]["delegate_work"]
    if decision == "never":
        return False, "Delegation is never; standing approval cannot override it."
    if decision == "act":
        return True, "Delegation is permitted for this bounded read-only worker."
    if data["approvals"].get("allow_read_only_search_worker", False):
        return True, "Standing approval permits one bounded read-only Search worker."
    return False, "Delegation requires explicit approval; direct authorized search is still possible."


class StopSearch(Exception):
    pass


class LocalSearch:
    def __init__(self, boundary_file, query, *, mode="auto", case_sensitive=False,
                 regex=False, sources=None, max_results=20, max_files=10000,
                 max_file_bytes=1048576, timeout=20, include_generated=False,
                 include_git_internals=False, source_notes=None):
        if not query or not query.strip() or any(character in query for character in ("\x00", "\n", "\r")):
            raise ValueError("A non-empty, single-line query without NUL is required.")
        if mode not in ("auto", "filename", "path", "content"):
            raise ValueError("Unsupported search mode.")
        if any(value <= 0 for value in (max_results, max_files, max_file_bytes, timeout)) or not math.isfinite(timeout):
            raise ValueError("Search limits must be positive.")
        self.boundary_file = Path(boundary_file)
        raw = self.boundary_file.read_bytes()
        self.policy_digest = hashlib.sha256(raw).digest()
        self.data = BOUNDARIES.load_yaml(raw.decode("utf-8-sig"))
        errors, warnings = BOUNDARIES.validate_document(self.data, require_active=True)
        if errors:
            raise ValueError("Invalid active boundaries: " + "; ".join(errors))
        self.query, self.mode, self.case_sensitive, self.regex = query, mode, case_sensitive, regex
        self.max_results, self.max_files, self.max_file_bytes = max_results, max_files, max_file_bytes
        self.timeout = timeout
        self.deadline = time.monotonic() + timeout
        self.include_generated, self.include_git_internals = include_generated, include_git_internals
        self.local = self.data["resources"]["local"]
        self.remote = self.data["resources"]["remote"]
        self.by_id = {source["id"]: source for source in self.local + self.remote}
        self.selected = set(sources) if sources else set(self.by_id)
        if not self.selected.issubset(self.by_id):
            raise ValueError("Unknown source ID in search scope.")
        self.source_notes = source_notes or {}
        if not set(self.source_notes).issubset(self.by_id):
            raise ValueError("Source notes contain an unknown source ID.")
        self.keys = [(BOUNDARIES._path_key(source["path"]), source) for source in self.local]
        self.rg = shutil.which("rg") if regex else None
        if regex and not self.rg:
            raise ValueError("Regex search requires rg; literal search needs no external search engine.")
        self.matches, self.match_keys, self.warnings = [], set(), list(warnings)
        self.visited_dirs, self.visited_files = set(), set()
        self.file_count = 0
        self.truncated, self.stop_reason = False, "scope_completed"
        self.attempted = False
        self.coverage = {}
        for source in self.local + self.remote:
            selected = source["id"] in self.selected
            self.coverage[source["id"]] = {
                "source_id": source["id"], "status": "pending" if selected else "not_selected",
                "files_searched": 0, "excluded_default": 0, "unsupported": 0,
                "blocked": 0, "errors": 0, "limits": 0,
                "notes": self.source_notes.get(source["id"], ""),
            }
        # A selected recursive tree includes its configured descendant sources.
        for key, source in self.keys:
            if any(parent["id"] in self.selected and self._covers(parent_key, parent, key)
                   for parent_key, parent in self.keys):
                self.selected.add(source["id"])
                self.coverage[source["id"]]["status"] = "pending"
        if regex:
            try:
                self._regex_lines("", path_match=True)  # Reject invalid patterns before traversal.
            except StopSearch:
                raise ValueError("Search budget expired while validating the regex query.") from None

    @staticmethod
    def _covers(key, source, candidate):
        if key == candidate:
            return True
        if source["kind"] != "directory" or not source["recursive"] or key[0] != candidate[0]:
            return False
        separator = "\\" if key[0] == "windows" else "/"
        return candidate[1].startswith(key[1].rstrip(separator) + separator)

    def _matching(self, path):
        key = BOUNDARIES._path_key(str(path))
        return [source for source_key, source in self.keys if self._covers(source_key, source, key)]

    def _decision(self, path):
        matching = self._matching(path)
        decisions = [source["permissions"]["read"] for source in matching]
        if not decisions:
            return self.data["defaults"]["unmatched_resource"]
        return "never" if "never" in decisions else "ask" if "ask" in decisions else "act"

    def _allowed(self, path):
        # Do not even resolve a lexically forbidden path to inspect its target.
        if self._decision(path) != "act":
            return False
        try:
            resolved = path.resolve(strict=True)
        except (OSError, RuntimeError):
            return False
        if ".git" in {part.casefold() for part in path.parts + resolved.parts}:
            if self.data["version_control"]["operations"]["inspect"] != "act":
                return False
        # Unknown resolved targets are not silently authorized by an act default.
        in_scope = any(source["id"] in self.selected for source in self._matching(resolved))
        return in_scope and self._decision(resolved) == "act"

    def _owners(self, path):
        sources = self._matching(path)
        try:
            if self._decision(path) == "act":
                sources += self._matching(path.resolve(strict=True))
        except (OSError, RuntimeError):
            pass
        return list({source["id"]: source for source in sources if source["id"] in self.selected}.values())

    def _bump(self, path, field):
        for source in self._owners(path):
            item = self.coverage[source["id"]]
            item[field] += 1
            if item["status"] == "pending":
                item["status"] = "searched"

    def _tick(self):
        if time.monotonic() >= self.deadline:
            self.truncated, self.stop_reason = True, "time_limit"
            raise StopSearch
        if hashlib.sha256(self.boundary_file.read_bytes()).digest() != self.policy_digest:
            self.truncated, self.stop_reason = True, "boundaries_changed"
            raise StopSearch

    def _excluded(self, path):
        try:
            parts = {part.casefold() for part in path.parts} | {part.casefold() for part in path.resolve().parts}
        except (OSError, RuntimeError):
            parts = {part.casefold() for part in path.parts}
        return ((not self.include_git_internals and ".git" in parts)
                or (not self.include_generated and bool(GENERATED & parts)))

    def _regex_lines(self, text, *, path_match=False):
        self._tick()
        command = [self.rg, "--no-config", "--color", "never", "--no-heading", "--no-filename",
                   "--line-number", "--max-count", str(self.max_results + 1),
                   "--max-columns", "300", "--max-columns-preview", "--text"]
        if not self.case_sensitive:
            command.append("--ignore-case")
        if path_match:
            command.append("--null-data")
        command.extend([f"--regexp={self.query}", "--", "-"])
        try:
            result = subprocess.run(command, input=text + ("\0" if path_match else ""),
                                    text=True, encoding="utf-8", errors="replace", capture_output=True,
                                    timeout=max(0.001, self.deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            self.truncated, self.stop_reason = True, "time_limit"
            raise StopSearch
        if result.returncode not in (0, 1):
            raise ValueError("Regex engine rejected the query or could not search it.")
        if path_match:
            return [1] if result.returncode == 0 else []
        lines = []
        for output_line in result.stdout.splitlines():
            number, separator, _ = output_line.partition(":")
            if separator and number.isdigit():
                lines.append(int(number))
        return lines

    def _matches_text(self, text):
        if self.regex:
            return bool(self._regex_lines(text, path_match=True))
        return self.query in text if self.case_sensitive else self.query.casefold() in text.casefold()

    def _add(self, path, kind, *, line=None, excerpt=None):
        self._tick()
        if not self._allowed(path):
            self._bump(path, "blocked")
            return
        key = (os.path.normcase(str(path.resolve())), kind, line)
        if key in self.match_keys:
            return
        owners = self._owners(path)
        if not owners:
            return
        actual_owners = [source for source in self._matching(path.resolve()) if source["id"] in self.selected]
        owner = max(actual_owners or owners, key=lambda source: len(BOUNDARIES._path_key(source["path"])[1]))
        match = {"kind": kind, "source_id": owner["id"], "path": str(path.absolute())}
        if line is not None:
            match["line"] = line
        if excerpt is not None:
            match["excerpt"] = excerpt[:240]
            match["excerpt_truncated"] = len(excerpt) > 240
        notes = [self.source_notes[source["id"]] for source in owners if self.source_notes.get(source["id"])]
        if notes:
            match["source_notes"] = list(dict.fromkeys(notes))
        self.matches.append(match)
        self.match_keys.add(key)
        if len(self.matches) >= self.max_results:
            self.truncated, self.stop_reason = True, "result_limit"
            raise StopSearch

    def _content(self, path):
        if not self._allowed(path):
            self._bump(path, "blocked")
            return
        if path.stat().st_size > self.max_file_bytes:
            self._bump(path, "limits")
            return
        # Bounded bytes are decoded locally, never copied wholesale to the caller.
        with path.open("rb") as stream:
            raw = stream.read(self.max_file_bytes + 1)
        if len(raw) > self.max_file_bytes:
            self._bump(path, "limits")
            return
        if b"\0" in raw:
            self._bump(path, "unsupported")
            return
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            self._bump(path, "unsupported")
            return
        lines = [line.removesuffix("\r") for line in text.split("\n")]
        if self.regex:
            numbers = self._regex_lines(text)
            for number in numbers:
                if 1 <= number <= len(lines):
                    self._add(path, "content", line=number, excerpt=lines[number - 1])
        else:
            needle = self.query if self.case_sensitive else self.query.casefold()
            for number, line in enumerate(lines, 1):
                if number % 128 == 0:
                    self._tick()
                haystack = line if self.case_sensitive else line.casefold()
                if needle in haystack:
                    self._add(path, "content", line=number, excerpt=line)

    def _walk(self, path, root):
        self._tick()
        if not self._allowed(path):
            self._bump(path, "blocked")
            return
        if self._excluded(path):
            self._bump(path, "excluded_default")
            return
        canonical = os.path.normcase(str(path.resolve()))
        is_directory = path.is_dir()
        visited = self.visited_dirs if is_directory else self.visited_files
        if canonical in visited:
            return
        visited.add(canonical)
        self.attempted = True
        for source in self._owners(path):
            if self.coverage[source["id"]]["status"] == "pending":
                self.coverage[source["id"]]["status"] = "searched"
        if not is_directory:
            if self.file_count >= self.max_files:
                self.truncated, self.stop_reason = True, "file_limit"
                raise StopSearch
            self.file_count += 1
            self._bump(path, "files_searched")
        candidate = str(path) if self.mode == "path" else path.name
        if self.mode == "auto":
            try:
                candidate = str(path.relative_to(root)) if path != root else path.name
            except ValueError:
                candidate = path.name
        if self.mode in ("auto", "path", "filename") and not (self.mode == "filename" and is_directory) and self._matches_text(candidate):
            self._add(path, "path" if is_directory or self.mode == "path" else "filename")
            path_hit = True
        else:
            path_hit = False
        if is_directory:
            # A nonrecursive source permits its own directory, not its descendants.
            if not any(source["id"] in self.selected and source["kind"] == "directory" and source["recursive"] for source in self._matching(path)):
                return
            with os.scandir(path) as entries:
                for entry in entries:
                    try:
                        self._walk(Path(entry.path), root)
                    except (OSError, RuntimeError):
                        self._bump(Path(entry.path), "errors")
            return
        if not path.is_file():
            self._bump(path, "unsupported")
            return
        if self.mode in ("content", "auto") and not path_hit:
            self._content(path)

    def plan(self):
        allowed, reason = worker_permission(self.data)
        sources = []
        for source in self.local + self.remote:
            if source["id"] not in self.selected:
                continue
            if "path" in source:
                readable = self._allowed(Path(source["path"]))
            else:
                readable = source["access"]["status"] in ("ready", "limited") and source["effective_mode"] in ("read", "write")
            sources.append({"source_id": source["id"], "kind": source["kind"], "read_authorized": readable})
        return {"worker_allowed": allowed, "worker_reason": reason, "sources": sources,
                "investigation": self.data["conversation"]["investigate_within_scope"]}

    def run(self):
        if self.data["conversation"]["investigate_within_scope"] != "act":
            for item in self.coverage.values():
                if item["status"] == "pending":
                    item.update(status="blocked", reason="Investigation requires authorization or is prohibited.")
            return self._result()
        # Parents first; visited canonical paths deduplicate nested roots and links.
        roots = sorted((source for source in self.local if source["id"] in self.selected), key=lambda source: len(source["path"]))
        try:
            for source in roots:
                item = self.coverage[source["id"]]
                path = Path(source["path"])
                if self._decision(path) != "act":
                    item.update(status="blocked", reason="Read permission is not act.")
                    continue
                try:
                    if not path.exists():
                        item.update(status="unavailable", reason="Local source is not accessible as a filesystem entry.")
                        continue
                    self._walk(path, path if source["kind"] == "directory" else path.parent)
                except (OSError, RuntimeError):
                    item["errors"] += 1
                    item.update(status="partial", reason="A source could not be completely read.")
        except StopSearch:
            pass
        # Detect policy replacement even when the final result was found quickly.
        if hashlib.sha256(self.boundary_file.read_bytes()).digest() != self.policy_digest:
            self.truncated, self.stop_reason = True, "boundaries_changed"
        for source in self.remote:
            item = self.coverage[source["id"]]
            if item["status"] != "pending":
                continue
            if source["access"]["status"] not in ("ready", "limited") or source["effective_mode"] not in ("read", "write"):
                item.update(status="unavailable", reason="Remote source has no verified usable read access.")
            else:
                item.update(status="unsupported", reason="Remote source requires the read-only connector adapter.")
        return self._result()

    def _result(self):
        gaps = False
        for item in self.coverage.values():
            if item["status"] == "pending":
                item.update(status="not_searched", reason=self.stop_reason)
            if item["status"] == "searched" and (self.truncated or any(item[field] for field in ("unsupported", "blocked", "errors", "limits"))):
                item["status"] = "partial"
            if item["source_id"] in self.selected and item["status"] != "searched":
                gaps = True
        status = "partial" if gaps or self.truncated else "complete" if self.matches else "no_matches"
        selected_states = {item["status"] for item in self.coverage.values() if item["source_id"] in self.selected}
        if not self.attempted and gaps and not self.truncated and selected_states.issubset({"blocked", "unavailable"}):
            status = "blocked"
        allowed, reason = worker_permission(self.data)
        return {
            "status": status, "query": self.query, "case_sensitive": self.case_sensitive,
            "regex": self.regex, "mode": self.mode,
            "matches": sorted(self.matches, key=lambda item: (item["path"], item.get("line", 0), item["kind"])),
            "coverage": list(self.coverage.values()), "truncated": self.truncated,
            "stop_reason": self.stop_reason, "queries_tried": [self.query], "warnings": self.warnings,
            "worker_allowed": allowed, "worker_reason": reason,
            "filters": {"generated_excluded": not self.include_generated,
                        "git_internals_excluded": not self.include_git_internals,
                        "auto_skips_content_on_path_hit": self.mode == "auto",
                        "text_encoding": "UTF-8", "max_file_bytes": self.max_file_bytes},
        }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boundaries", required=True, type=Path)
    parser.add_argument("--query", required=True)
    parser.add_argument("--mode", choices=("auto", "filename", "path", "content"), default="auto")
    parser.add_argument("--case-sensitive", action="store_true")
    parser.add_argument("--regex", action="store_true")
    parser.add_argument("--source", action="append", dest="sources")
    parser.add_argument("--max-results", type=int, default=20)
    parser.add_argument("--max-files", type=int, default=10000)
    parser.add_argument("--max-file-bytes", type=int, default=1048576)
    parser.add_argument("--timeout", type=float, default=20)
    parser.add_argument("--include-generated", action="store_true")
    parser.add_argument("--include-git-internals", action="store_true")
    parser.add_argument("--source-note", action="append", default=[])
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args(argv)
    options = vars(args).copy()
    boundary_file, query = options.pop("boundaries"), options.pop("query")
    plan, notes = options.pop("plan"), options.pop("source_note")
    try:
        parsed_notes = {}
        for note in notes:
            source_id, separator, text = note.partition("=")
            if not separator or not text:
                raise ValueError("Source notes must use source-id=note syntax.")
            parsed_notes[source_id] = text
        options["source_notes"] = parsed_notes
        search = LocalSearch(boundary_file, query, **options)
        result = search.plan() if plan else search.run()
    except (ValueError, OSError, RuntimeError, BOUNDARIES.yaml.YAMLError) as exc:
        # Error details omit file contents and YAML parser snippets.
        message = str(exc) if isinstance(exc, ValueError) and not isinstance(exc, BOUNDARIES.yaml.YAMLError) else "A source, dependency, or configuration could not be read."
        print(json.dumps({"status": "error", "matches": [], "coverage": [], "reason": message}))
        return 2
    print(json.dumps(result, ensure_ascii=False))
    return 0 if plan or result["status"] in ("complete", "no_matches", "partial") else 1


if __name__ == "__main__":
    sys.exit(main())
