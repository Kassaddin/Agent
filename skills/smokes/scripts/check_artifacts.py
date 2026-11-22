#!/usr/bin/env python3
"""Audit selected local artifacts without repairing them; optionally save a new report."""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import string
import sys
import time
from urllib.parse import unquote, urlsplit
import uuid

sys.dont_write_bytecode = True
from validate_report import (AccessError, BoundaryAccess, INIT, digest, finalize,
                             render_markdown, strict_json, validate_report)


class AuditLimit(Exception):
    pass


class UnsupportedFormat(ValueError):
    pass


class UniqueYamlLoader(INIT.yaml.SafeLoader):
    pass


def _yaml_mapping(loader, node, deep=False):
    seen = set()
    for key_node, _ in node.value:
        if key_node.tag == "tag:yaml.org,2002:merge":
            continue
        key = loader.construct_object(key_node, deep=True)
        try:
            if key in seen:
                raise ValueError("Duplicate explicit YAML mapping key")
            seen.add(key)
        except TypeError:
            raise UnsupportedFormat("Complex YAML mapping keys require a format-specific adapter") from None
    loader.flatten_mapping(node)
    return INIT.yaml.SafeLoader.construct_mapping(loader, node, deep=deep)


UniqueYamlLoader.add_constructor(INIT.yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _yaml_mapping)


def inline_code_spans(line):
    """Find closed code spans without accepting part of a longer closing run."""
    position = 0
    while match := re.search(r"`+", line[position:]):
        start, end = position + match.start(), position + match.end()
        backslashes, before = 0, start - 1
        while before >= 0 and line[before] == "\\":
            backslashes, before = backslashes + 1, before - 1
        if backslashes % 2:
            position = end
            continue
        closing = re.search(r"(?<!`)" + re.escape(line[start:end]) + r"(?!`)", line[end:])
        if closing is None:
            position = end
            continue
        close_start, close_end = end + closing.start(), end + closing.end()
        yield start, close_end, end, close_start
        position = close_end


def mask_inline_code(line, keep_text=False):
    pieces, position = [], 0
    for start, end, content_start, content_end in inline_code_spans(line):
        pieces.extend([line[position:start], line[content_start:content_end] if keep_text else " " * (end - start)])
        position = end
    return "".join(pieces) + line[position:]


def mask_html_comments(line, in_comment):
    spans = {start: end for start, end, _, _ in inline_code_spans(line)}
    visible, position = list(line), 0
    while position < len(line):
        if in_comment:
            closing = line.find("-->", position)
            end = len(line) if closing < 0 else closing + 3
            visible[position:end] = " " * (end - position)
            position = end
            if closing >= 0:
                in_comment = False
        elif position in spans:
            position = spans[position]
        elif line.startswith("<!--", position):
            in_comment = True
        else:
            position += 1
    return "".join(visible), in_comment


def visible_markdown(text, keep_inline_text=False):
    lines, marker, length, in_comment = [], None, 0, False
    for raw in text.split("\n"):
        line = raw
        fence = re.match(r"^\s*(?:(?:[-+*]|\d+[.)])\s+)?(`{3,}|~{3,})(.*)$", line)
        if marker:
            if fence and fence[1][0] == marker and len(fence[1]) >= length and not fence[2].strip():
                marker = None
            lines.append("")
        elif fence and not in_comment:
            marker, length = fence[1][0], len(fence[1])
            lines.append("")
        else:
            line, in_comment = mask_html_comments(raw, in_comment)
            lines.append(mask_inline_code(line, keep_text=keep_inline_text))
    return lines


def heading_anchors(text):
    anchors, titles = set(), set()
    visible = visible_markdown(text, keep_inline_text=True)
    html_visible = visible_markdown(text)
    for index, line in enumerate(visible):
        heading = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        title = heading[1] if heading else None
        if not title and index + 1 < len(visible) and line.strip() and re.fullmatch(r"\s{0,3}(?:=+|-+)\s*", visible[index + 1]):
            title = line.strip()
        if title:
            explicit = re.search(r"\s*\{#([^}]+)\}\s*$", title)
            if explicit:
                anchors.add(explicit[1])
                title = title[:explicit.start()]
            title = re.sub(r"!?\[([^\]]+)\]\([^)]+\)", r"\1", title)
            title = re.sub(r"<[^>]+>", "", title)
            titles.add(re.sub(r"[*~]", "", title).casefold())
            slug = re.sub(r"[^\w\-\s]", "", title.lower())
            slug = re.sub(r"\s", "-", slug.strip())
            candidate, number = slug, 1
            while candidate in anchors:
                candidate, number = f"{slug}-{number}", number + 1
            anchors.add(candidate)
        anchors.update(re.findall(r"<(?:a|span)\b[^>]*\bid=[\"']([^\"']+)[\"']", html_visible[index], re.I))
    return anchors, titles


def _destination(value):
    value = value.strip()
    if value.startswith("<"):
        end = value.find(">")
        return value[1:end] if end >= 0 else None
    match = re.match(r"((?:\\.|[^\s])+)(.*)$", value)
    if not match:
        return None
    tail = match[2].strip()
    if tail and not ((tail[0] in "\"'" and tail[-1] == tail[0]) or (tail[0] == "(" and tail[-1] == ")")):
        return None
    return re.sub(r"\\([()\[\] <>])", r"\1", match[1])


def is_escaped(text, position):
    before = position - 1
    while before >= 0 and text[before] == "\\":
        before -= 1
    return (position - before - 1) % 2 == 1


def reference_key(label):
    label = re.sub(r"\\([" + re.escape(string.punctuation) + r"])", r"\1", label)
    return " ".join(label.split()).casefold()


def markdown_links(text):
    lines = visible_markdown(text)
    definitions = {}
    label_pattern = r"(?:\\.|[^\\\]\n])+"
    definition_pattern = re.compile(r"^\s{0,3}\[(" + label_pattern + r")\]:\s*(.+)$")
    for line in lines:
        match = definition_pattern.match(line)
        if match:
            definitions[reference_key(match[1])] = _destination(match[2])
    for number, line in enumerate(lines, 1):
        if definition_pattern.match(line):
            continue
        for match in re.finditer(r"!?\[\[(" + label_pattern + r")\]\]", line):
            if not is_escaped(line, match.start(1) - 2):
                yield number, match[1].split("|", 1)[0], "wiki"
        consumed_until = 0
        for match in re.finditer(r"!?\[(" + label_pattern + r")\]", line):
            if match.start() < consumed_until or is_escaped(line, match.start(1) - 1):
                continue
            end = match.end()
            if end < len(line) and line[end] == "(":
                depth, quote, angle, escaped, position = 1, None, False, False, end + 1
                while position < len(line) and depth:
                    char = line[position]
                    if escaped:
                        escaped = False
                    elif char == "\\":
                        escaped = True
                    elif quote:
                        if char == quote:
                            quote = None
                    elif angle:
                        if char == ">":
                            angle = False
                    elif char == "<" and (position == end + 1 or line[position - 1].isspace()):
                        angle = True
                    elif char in "\"'" and position > end + 1 and line[position - 1].isspace():
                        quote = char
                    elif char == "(":
                        depth += 1
                    elif char == ")":
                        depth -= 1
                    position += 1
                if depth == 0:
                    target = _destination(line[end + 1:position - 1])
                    if target is not None:
                        consumed_until = position
                        yield number, target, "markdown"
            elif end < len(line) and line[end] == "[":
                reference = re.match(r"\[(" + label_pattern + r")?\]", line[end:])
                if reference:
                    label = reference[1] or match[1]
                    key = reference_key(label)
                    consumed_until = end + reference.end()
                    yield number, definitions.get(key) or label, "markdown" if key in definitions else "undefined_reference"
            else:
                key = reference_key(match[1])
                if key in definitions and definitions[key]:
                    yield number, definitions[key], "markdown"
        for target in re.findall(r"<(?:a|img)\b[^>]*(?:href|src)=[\"']([^\"']+)[\"']", line, re.I):
            yield number, target, "markdown"


class Auditor:
    def __init__(self, boundaries, paths, *, max_files=500, max_bytes=2097152, max_findings=1000, timeout=60,
                 intentional_duplicates=None, semantic_review=None, exclude=None):
        if not paths or min(max_files, max_bytes, max_findings, timeout) <= 0 or not math.isfinite(timeout):
            raise ValueError("Provide paths and positive finite audit limits")
        self.access = BoundaryAccess(boundaries)
        if self.access.data["conversation"]["investigate_within_scope"] != "act":
            raise AccessError("Investigation is not authorized without an additional user decision")
        self.requested = list(dict.fromkeys(str(Path(os.path.abspath(path))) for path in paths))
        self.max_files, self.max_bytes = max_files, max_bytes
        self.max_findings = max_findings
        self.deadline = time.monotonic() + timeout
        self.intentional = {str(Path(os.path.abspath(path))) for path in intentional_duplicates or []}
        self.semantic_review = Path(semantic_review) if semantic_review else None
        self.excluded = [Path(os.path.abspath(path)) for path in exclude or []]
        self.files, self.raw, self.text, self.snapshots, self.coverage, self.findings = [], {}, {}, {}, [], []
        self.visited = set()

    def tick(self):
        self.access.unchanged()
        if time.monotonic() >= self.deadline:
            raise AuditLimit("Time limit reached")

    def covered(self, check, status, paths, reason=""):
        self.coverage.append({"check_id": check, "status": status, "paths": [str(path) for path in paths], "reason": reason})

    def capture(self, path):
        self.tick()
        path = Path(os.path.abspath(path))
        key = str(path)
        if key in self.snapshots:
            return self.snapshots[key]["state"]
        if len(self.snapshots) >= self.max_files:
            raise AuditLimit("File/snapshot limit reached")
        snapshot = {"path": key, "state": "blocked", "sha256": None, "bytes": None}
        self.snapshots[key] = snapshot
        if not self.access.allowed(path):
            self.covered("read_access", "blocked", [path], "Read permission is missing or a resolved target is outside the allowed sources.")
            return "blocked"
        try:
            if not path.exists():
                snapshot["state"] = "missing"
                return "missing"
            if not path.is_file():
                snapshot["state"] = "unsupported"
                self.covered("file_integrity", "unsupported", [path], "Expected a regular file.")
                return "unsupported"
            snapshot["bytes"] = path.stat().st_size
            if snapshot["bytes"] > self.max_bytes:
                snapshot["state"] = "unsupported"
                self.covered("file_integrity", "partial", [path], "File exceeds the per-file byte limit.")
                return "unsupported"
            self.access.require(path)
            with path.open("rb") as stream:
                raw = stream.read(self.max_bytes + 1)
            if len(raw) > self.max_bytes:
                snapshot["state"] = "unsupported"
                self.covered("file_integrity", "partial", [path], "File grew beyond the byte limit.")
                return "unsupported"
            snapshot.update(state="read", sha256=digest(raw), bytes=len(raw))
            self.raw[key] = raw
            try:
                self.text[key] = raw.decode("utf-8-sig") if b"\0" not in raw else None
            except UnicodeDecodeError:
                self.text[key] = None
            return "read"
        except OSError:
            self.covered("read_access", "blocked", [path], "The file could not be read with current privileges.")
            return "blocked"

    def inventory(self, path):
        self.tick()
        path = Path(os.path.abspath(path))
        if any(path == output or output in path.parents for output in self.excluded):
            return
        if not self.access.allowed(path):
            self.capture(path)
            return
        try:
            canonical = os.path.normcase(str(path.resolve()))
            if canonical in self.visited:
                return
            self.visited.add(canonical)
            if path.is_dir():
                if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
                    self.covered("scope_inventory", "skipped", [path], "Select the linked target explicitly to include its directory.")
                    return
                recursive = any(source["kind"] == "directory" and source["recursive"] for source in self.access.matching(path))
                if not recursive:
                    self.covered("scope_inventory", "skipped", [path], "Directory scope is nonrecursive.")
                    return
                with os.scandir(path) as entries:
                    for entry in entries:
                        if entry.name.casefold() in {".git", "node_modules", "__pycache__", ".venv"}:
                            self.covered("scope_inventory", "skipped", [entry.path], "Infrastructure directory excluded; select its allowed files explicitly if needed.")
                            continue
                        self.inventory(Path(entry.path))
            else:
                self.files.append(path)
                state = self.capture(path)
                if state == "missing":
                    self.find("file_missing", "integrity", path, None, "Expected artifact is missing", "The requested artifact cannot be consumed.", "Restore or generate the intended file after confirming its expected content.", "The expected file exists and its relevant checks pass.", decision=True)
        except OSError:
            self.covered("scope_inventory", "blocked", [path], "The directory could not be inspected.")

    def find(self, check, category, path, line, title, impact, proposed, acceptance, *, certainty="confirmed", severity="medium", priority="P1", decision=False, locations=None, evidence=None):
        if len(self.findings) >= self.max_findings:
            raise AuditLimit("Finding limit reached")
        key = str(path)
        location = {"path": key, "line": line, "section": None}
        if evidence is None:
            text = self.text.get(key)
            lines = text.split("\n") if text is not None else []
            actual_line = line if line and line <= len(lines) and lines[line - 1].strip() else next((number for number, value in enumerate(lines, 1) if value.strip() and value.strip() != "---"), None)
            excerpt = lines[actual_line - 1][:240] if actual_line else "Expected file is absent at the inspected location." if text is None else "The captured file is empty or has no nonblank source line."
            evidence = [{"path": key, "line": actual_line, "kind": "source_excerpt" if actual_line else "observation", "text": excerpt}]
        needs_decision = decision or certainty == "needs_review"
        writable = self.access.allowed(path, "create" if self.snapshots.get(key, {}).get("state") == "missing" else "modify")
        mode = "decision_required" if needs_decision else "agent_candidate" if writable else "user_action"
        reason = "Resolve the intended meaning or content before correction." if needs_decision else "Current local permissions permit a candidate correction." if writable else "Current boundaries do not authorize this source modification."
        if needs_decision and not writable:
            reason += " The location is also outside current write permissions."
        self.findings.append({"check_id": check, "category": category, "certainty": certainty, "severity": severity, "priority": priority,
                              "title": title, "locations": locations or [location], "evidence": evidence, "impact": impact,
                              "proposed_fix": proposed, "acceptance_check": acceptance, "depends_on": [],
                              "remediation": {"mode": mode, "reason": reason}})

    def structure(self, path):
        key, suffix = str(path), path.suffix.casefold()
        text = self.text.get(key)
        if text is None:
            if suffix in {".md", ".markdown", ".yaml", ".yml", ".json", ".txt"}:
                self.find("text_encoding", "integrity", path, None, "Expected UTF-8 text is not readable as text", "Text consumers may fail or read corrupted content.", "Restore the intended UTF-8 text without discarding meaningful data.", "The file decodes as UTF-8 and passes its format checks.", decision=True)
            self.covered("format_checks", "unsupported", [path], "A binary or non-UTF-8 format needs its own adapter.")
            return
        try:
            parsed = None
            line_offset = 0
            if suffix == ".json":
                parsed = strict_json(text)
            elif suffix in {".yaml", ".yml"}:
                parsed = INIT.load_yaml(text) if path.name == "BOUNDARIES.yaml" else INIT.yaml.load(text, Loader=UniqueYamlLoader)
                if path.name == "BOUNDARIES.yaml":
                    errors, _ = INIT.validate_document(parsed)
                    if errors:
                        raise ValueError("Boundary schema does not match the Init contract")
            elif suffix not in {".md", ".markdown", ".txt"}:
                self.covered("format_checks", "unsupported", [path], "Only file presence/hash and duplication checks are available for this format.")
                return
            if path.name == "SKILL.md":
                match = re.match(r"^---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
                if not match:
                    raise ValueError("Skill frontmatter is absent or malformed")
                line_offset = text.count("\n", 0, match.start(1))
                parsed = INIT.yaml.load(match[1], Loader=UniqueYamlLoader)
                if not isinstance(parsed, dict) or not isinstance(parsed.get("name"), str) or not isinstance(parsed.get("description"), str) or not parsed["description"].strip():
                    raise ValueError("Skill name and description must be nonempty strings")
                if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", parsed["name"]) or len(parsed["name"]) > 64:
                    raise ValueError("Skill name is invalid")
                front_lines = text[:match.end()].split("\n")
                name_line = next((number for number, value in enumerate(front_lines, 1) if re.match(r"^name\s*:", value)), None)
                description_line = next((number for number, value in enumerate(front_lines, 1) if re.match(r"^description\s*:", value)), None)
                if parsed["name"] != path.parent.name:
                    self.find("skill_name", "consistency", path, name_line, "Skill name differs from its folder", "Invocation names and package identity can diverge.", "Align the name with the intended folder identity and update related references.", "Skill name and folder agree; dependent references resolve.")
                if parsed["description"].lstrip().startswith("[TODO:"):
                    self.find("skill_placeholder", "integrity", path, description_line, "Skill description is an unfinished scaffold", "Skill selection lacks a usable description.", "Write the intended capability and invocation conditions.", "The skill description contains finished task-specific guidance.")
            if path.name == "openai.yaml" and path.parent.name == "agents" and isinstance(parsed, dict):
                interface = parsed.get("interface", {})
                if not isinstance(interface, dict):
                    raise ValueError("Skill interface must be a mapping")
                for field in ("display_name", "short_description"):
                    if field in interface and (not isinstance(interface[field], str) or not interface[field].strip()):
                        raise ValueError("Skill interface text is invalid")
                if "short_description" in interface and not 25 <= len(interface["short_description"]) <= 64:
                    raise ValueError("Skill short description is outside the supported length")
                policy = parsed.get("policy", {})
                if not isinstance(policy, dict) or ("allow_implicit_invocation" in policy and type(policy["allow_implicit_invocation"]) is not bool):
                    raise ValueError("Skill invocation policy must contain a boolean allow_implicit_invocation value")
            self.covered("format_checks", "complete", [path])
        except (UnsupportedFormat, INIT.yaml.constructor.ConstructorError):
            self.covered("format_checks", "unsupported", [path], "Custom YAML tags or complex keys need a format-specific adapter.")
        except (ValueError, INIT.yaml.YAMLError) as exc:
            mark = getattr(exc, "problem_mark", None)
            line = mark.line + 1 + line_offset if mark is not None else getattr(exc, "lineno", None)
            diagnostic = getattr(exc, "problem", None) or getattr(exc, "msg", None) or str(exc)
            diagnostic = diagnostic.split("\n", 1)[0][:240]
            self.find("structure_invalid", "structure", path, line, "Artifact structure is invalid or ambiguous", f"Format/schema diagnostic: {diagnostic}. A consumer may reject the file or interpret conflicting structure differently.", "Correct this specific format/schema defect while preserving the intended values.", "The applicable parser and schema/profile checks pass.", decision="Duplicate" in str(exc))
            self.covered("format_checks", "complete", [path], "A reproducible structural defect was found.")

    def link(self, path, line, target, kind):
        self.tick()
        if kind == "undefined_reference":
            self.find("undefined_reference", "cross_link", path, line, "Reference-link definition is absent", "The intended navigation may render as plain text.", "Confirm the intended reference and define it or use an inline link.", "The intended reference resolves.", certainty="needs_review", severity="low", priority="P2")
            return
        if re.match(r"^[A-Za-z]:[\\/]", target):
            file_part, separator, fragment = target.partition("#")
        else:
            try:
                parsed = urlsplit(target)
                if parsed.scheme in {"http", "https"}:
                    parsed.port
            except ValueError:
                self.find("link_uri_invalid", "cross_link", path, line, "Link URI has invalid syntax", "The declared link cannot be interpreted as a valid URI.", "Confirm the intended address and correct its URI syntax.", "The address parses and resolves under the intended source adapter.", decision=True)
                return
            if parsed.scheme or parsed.netloc:
                self.covered("cross_link.remote", "skipped", [path], "External URI was not fetched by the offline checker.")
                return
            if parsed.query:
                self.covered("cross_link.variant", "unsupported", [path], "Local links with query semantics need a renderer-specific adapter.")
                return
            file_part, fragment = parsed.path, parsed.fragment
        file_part, fragment = unquote(file_part), unquote(fragment)
        if fragment.startswith("^") or (kind == "wiki" and "#" in fragment):
            self.covered("cross_link.variant", "unsupported", [path], "Block or nested-heading references need a vault-specific adapter.")
            return
        destination = Path(file_part) if file_part else path
        if file_part and not destination.is_absolute():
            destination = path.parent / destination
        destination = Path(os.path.abspath(destination))
        if kind == "wiki" and file_part:
            if not destination.suffix:
                destination = destination.with_suffix(".md")
            candidates = [item for item in self.files if item.suffix.casefold() == ".md" and item.stem.casefold() == Path(file_part).stem.casefold()]
            if len(candidates) > 1 and "/" not in file_part and "\\" not in file_part:
                self.find("wiki_ambiguous", "ambiguity", path, line, "Wiki link has multiple candidate notes", "The intended note cannot be determined from its basename.", "Use a qualified vault-relative note path after confirming the intended note.", "Exactly one intended note resolves.", certainty="needs_review", severity="low", priority="P2")
                return
            if len(candidates) == 1 and "/" not in file_part and "\\" not in file_part:
                destination = candidates[0]
        if not self.access.allowed(destination):
            self.covered("cross_link.access", "blocked", [path], "The target is outside approved read access; it was not probed.")
            return
        if not destination.exists():
            if kind == "wiki":
                self.covered("cross_link.wiki", "partial", [path], "Wiki target was not resolved in this scope; vault-wide absence was not established.")
            else:
                self.find("link_missing", "cross_link", path, line, "Local link target is missing", "The generated artifact contains a navigation or dependency path that cannot resolve.", "Verify the intended destination and correct the relative target or restore the missing artifact.", "This exact link resolves to the intended accessible target.")
            return
        if fragment:
            if destination.suffix.casefold() not in {".md", ".markdown"}:
                self.covered("cross_link.anchor", "unsupported", [path], "Anchor semantics for this target format are not supported.")
                return
            if self.capture(destination) != "read" or self.text.get(str(destination)) is None:
                self.covered("cross_link.anchor", "partial", [path], "Target text could not be inspected for anchors.")
                return
            anchors, titles = heading_anchors(self.text[str(destination)])
            exists = fragment.casefold() in titles or fragment in anchors if kind == "wiki" else fragment in anchors
            if not exists:
                self.find("anchor_missing", "cross_link", path, line, "Local heading anchor is missing", "The link cannot navigate to the declared section under the supported heading rules.", "Correct the anchor or restore the intended heading; confirm renderer-specific exceptions.", "The target section resolves under the intended renderer.")

    def duplicates(self):
        groups = defaultdict(list)
        for path in self.files:
            key = str(path)
            if key not in self.intentional and self.raw.get(key):
                groups[digest(self.raw[key])].append(path)
        for files in groups.values():
            if len(files) < 2:
                continue
            locations = [{"path": str(path), "line": None, "section": None} for path in files]
            evidence = [{"path": str(path), "line": None, "kind": "observation", "text": "Captured files have identical SHA-256 content hashes."} for path in files]
            self.find("duplicate_files", "duplication", files[0], None, "Files have identical nonempty content", "Independent copies may drift if the duplication is unintended.", "Confirm whether these copies are intentional; consolidate only if their ownership and use permit it.", "The user confirms the copies are intentional or the unintended duplication is removed and references still resolve.", certainty="needs_review", severity="low", priority="P3", locations=locations, evidence=evidence)
        self.covered("duplicate_files", "complete", self.files, "Exact nonempty duplicates only; declared intentional copies are excluded and duplication is not automatically a defect.")

    def semantic(self):
        eligible = {str(path) for path in self.files if self.text.get(str(path)) is not None}
        if not self.semantic_review:
            self.covered("semantic_review", "skipped" if eligible else "complete", sorted(eligible), "An agent must review ambiguity, contradictions, and contextual consistency." if eligible else "No readable text was available for semantic review.")
            return
        self.access.require(self.semantic_review)
        with self.semantic_review.open("rb") as stream:
            raw = stream.read(self.max_bytes + 1)
        if len(raw) > self.max_bytes:
            raise ValueError("Semantic review packet exceeds the byte limit")
        packet = strict_json(raw.decode("utf-8-sig"))
        if not isinstance(packet, dict) or set(packet) != {"status", "reason", "paths", "findings"} or packet["status"] not in ("complete", "partial") or not isinstance(packet["reason"], str) or not isinstance(packet["paths"], list) or not isinstance(packet["findings"], list):
            raise ValueError("Invalid semantic review packet")
        if not all(isinstance(path, str) for path in packet["paths"]):
            raise ValueError("Semantic review paths must be strings")
        reviewed = set(packet["paths"])
        if not reviewed.issubset(eligible):
            raise ValueError("Semantic review references uncaptured or non-text files")
        for finding in packet["findings"]:
            self.tick()
            if len(self.findings) >= self.max_findings:
                raise AuditLimit("Finding limit reached")
            if not isinstance(finding, dict):
                raise ValueError("Invalid semantic finding")
            finding = dict(finding)
            finding.setdefault("depends_on", [])
            check = dict(finding, id="SMK-000", fingerprint="0" * 64)
            schema = json.loads((Path(__file__).resolve().parents[1] / "references" / "report.schema.json").read_text(encoding="utf-8"))
            packet_errors = []
            INIT._check_schema(check, schema["$defs"]["finding"], schema, "$", packet_errors)
            if packet_errors:
                raise ValueError("Semantic finding does not match the report schema")
            if finding.get("category") not in {"ambiguity", "contradiction", "consistency", "duplication"}:
                raise ValueError("Semantic findings must describe language, consistency, or duplication concerns")
            for item in finding.get("locations", []) + finding.get("evidence", []):
                if item.get("path") not in reviewed:
                    raise ValueError("Semantic finding refers outside reviewed captured files")
            for evidence in finding.get("evidence", []):
                if evidence["kind"] != "source_excerpt":
                    raise ValueError("Semantic findings require verbatim source excerpts")
                text = self.text[evidence["path"]]
                line = evidence.get("line")
                if line is not None:
                    lines = text.split("\n")
                    if type(line) is not int or not 1 <= line <= len(lines):
                        raise ValueError("Semantic evidence line is invalid")
                    text = lines[line - 1]
                if not evidence.get("text") or evidence["text"] not in text:
                    raise ValueError("Semantic evidence is not a verbatim captured excerpt")
            self.findings.append(finding)
        status = "complete" if packet["status"] == "complete" and reviewed == eligible else "partial"
        self.covered("semantic_review", status, sorted(reviewed), packet["reason"] or "Agent review supplied.")

    def run(self):
        try:
            for path in self.requested:
                self.inventory(Path(path))
            self.covered("scope_inventory", "complete", self.requested, "Requested files were enumerated; the selected report destination and semantic working packet are outside the inspected artifact scope.")
            for path in self.files:
                self.tick()
                if self.snapshots.get(str(path), {}).get("state") != "read":
                    continue
                self.structure(path)
                if path.suffix.casefold() in {".md", ".markdown"} and self.text.get(str(path)) is not None:
                    for line, target, kind in markdown_links(self.text[str(path)]):
                        self.link(path, line, target, kind)
                    self.covered("cross_links", "complete", [path], "Common local Markdown links/anchors checked; any limitations are listed separately.")
            self.duplicates()
            self.semantic()
        except AuditLimit as exc:
            self.covered("audit_limits", "partial", self.requested, str(exc))
            self.covered("semantic_review", "skipped", [], "The bounded audit ended before semantic review completed.")
        self.access.unchanged()
        report = {"schema_version": 1, "report_id": datetime.now(timezone.utc).strftime("smokes-%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:8],
                  "created_at": datetime.now(timezone.utc).isoformat(),
                  "scope": {"requested": self.requested, "boundaries_file": str(self.access.file), "boundaries_sha256": self.access.hash, "snapshots": list(self.snapshots.values())},
                  "summary": {}, "coverage": self.coverage, "findings": self.findings}
        finalize(report)
        errors = validate_report(report)
        if errors:
            raise ValueError("Generated report failed validation: " + "; ".join(errors))
        return report


def save_report(report, directory, access):
    if validate_report(report):
        raise ValueError("Refusing to save an invalid or inconsistent report")
    directory = Path(os.path.abspath(directory))
    access.require(directory, "create")
    if directory.exists():
        raise ValueError("Report destination must be a new directory; existing reports are immutable")
    for path in (directory, directory / "report.json", directory / "report.md"):
        access.require(path, "create")
    if any(Path(item["path"]) in (directory / "report.json", directory / "report.md") for item in report["scope"]["snapshots"]):
        raise ValueError("Report output cannot overwrite an inspected artifact")
    access.unchanged()
    # No code, plug-ins, commands, or remote requests are executed from report contents.
    parent = directory
    while not parent.exists():
        access.require(parent, "create")
        parent = parent.parent
    directory.mkdir(parents=True, exist_ok=False)
    with (directory / "report.json").open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    with (directory / "report.md").open("x", encoding="utf-8") as stream:
        stream.write(render_markdown(report))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boundaries", required=True, type=Path)
    parser.add_argument("--path", required=True, action="append", dest="paths")
    parser.add_argument("--report-dir", type=Path)
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--semantic-review", type=Path)
    parser.add_argument("--allow-duplicate", action="append", default=[])
    parser.add_argument("--max-files", type=int, default=500)
    parser.add_argument("--max-bytes", type=int, default=2097152)
    parser.add_argument("--max-findings", type=int, default=1000)
    parser.add_argument("--timeout", type=float, default=60)
    args = parser.parse_args(argv)
    if args.summary and not args.report_dir:
        parser.error("--summary requires --report-dir so detailed findings are retained")
    try:
        auditor = Auditor(args.boundaries, args.paths, max_files=args.max_files, max_bytes=args.max_bytes, max_findings=args.max_findings, timeout=args.timeout,
                          intentional_duplicates=args.allow_duplicate, semantic_review=args.semantic_review,
                          exclude=[args.report_dir, args.semantic_review] if args.report_dir and args.semantic_review else [args.report_dir or args.semantic_review] if args.report_dir or args.semantic_review else [])
        report = auditor.run()
        if args.report_dir:
            save_report(report, args.report_dir, auditor.access)
        output = {"report_id": report["report_id"], "summary": report["summary"], "report_dir": str(args.report_dir.absolute())} if args.summary else report
        print(json.dumps(output, ensure_ascii=False))
        return 0
    except (OSError, ValueError, RuntimeError, INIT.yaml.YAMLError):
        print(json.dumps({"status": "error", "reason": "Audit/report access, input, format, or policy validation failed; no inspected files were repaired."}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
