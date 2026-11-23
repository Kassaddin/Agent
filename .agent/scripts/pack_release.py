#!/usr/bin/env python3
"""Build a skills-only Agents/ release without copying active project state."""
from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/update/scripts"))
from release_format import MANIFEST, make_manifest, json_bytes

PACKAGES = ("backlog", "context", "create-skill", "fix", "glossary", "implement", "init", "refine", "search", "setup", "smokes", "to-document", "to-tasks", "update")
EXCLUDED = {"__pycache__", ".pytest_cache", ".git", ".venv", "node_modules"}
EXTENSIONS = {".md", ".yaml", ".yml", ".json", ".py", ".txt"}


def build(project_root, version):
    root = Path(project_root).resolve()
    payload, captured = {}, {}
    for name in PACKAGES:
        package = root / ".agent/skills" / name
        if not (package / "SKILL.md").is_file():
            raise ValueError(f"Missing skill: {name}")
        for source in sorted(package.rglob("*")):
            if any(part in EXCLUDED for part in source.relative_to(package).parts):
                continue
            if source.is_symlink() or not source.resolve().is_relative_to(package.resolve()):
                raise ValueError("Release sources cannot cross symlinks or junctions")
            if not source.is_file():
                continue
            if source.suffix.lower() not in EXTENSIONS or source.name.startswith("."):
                raise ValueError(f"Review this file before adding it to the release allowlist: {source.name}")
            raw = source.read_bytes()
            raw.decode("utf-8-sig")
            if source.suffix == ".py":
                ast.parse(raw, filename=str(source))
            payload["Agents/" + source.relative_to(root).as_posix()] = raw
            captured[source] = raw
    guidance = {
        "Agents/README.md": root / ".agent/assets/release-README.md",
        "Agents/docs/guide.md": root / "docs/guide.md",
        "Agents/.agent/instructions.md": root / ".agent/assets/external-instructions.md",
        "Agents/.gitignore": root / ".agent/assets/release.gitignore",
    }
    for name, source in guidance.items():
        if not source.resolve().is_relative_to(root):
            raise ValueError("Guidance must stay within the selected repository")
        raw = source.read_bytes()
        captured[source] = raw
        payload[name] = raw.replace(b"(../../docs/guide.md)", b"(docs/guide.md)") if name == "Agents/README.md" else raw
    for name, raw in payload.items():
        for marker in (b"C:/Users/", b"C:\\Users\\", b"G:/VAULT/", b"Kassaddin/Agent"):
            if marker.lower() in raw.lower():
                if marker == b"Kassaddin/Agent" and name in {
                    "Agents/.agent/skills/setup/SKILL.md",
                    "Agents/.agent/skills/setup/references/setup-contract.md",
                    "Agents/.agent/skills/setup/scripts/setup_kit.py",
                }:
                    continue  # User-approved fixed release source; no other identity exception.
                raise ValueError("A project-specific path or repository identity needs review before sharing")
    manifest = make_manifest({name.removeprefix("Agents/"): raw for name, raw in payload.items()}, version)
    payload["Agents/" + MANIFEST] = json_bytes(manifest)
    memory = io.BytesIO()
    with zipfile.ZipFile(memory, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, raw in sorted(payload.items()):
            item = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.create_system = 3
            item.external_attr = 0o100644 << 16
            archive.writestr(item, raw, compresslevel=9)
    raw = memory.getvalue()
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if archive.testzip() is not None or set(archive.namelist()) != set(payload):
            raise ValueError("Release integrity verification failed")
        if any(archive.read(name) != content for name, content in payload.items()):
            raise ValueError("Release bytes differ from reviewed source bytes")
    if any(source.read_bytes() != content for source, content in captured.items()):
        raise ValueError("Sources changed while building; review and rebuild")
    output = root / "releases"
    if not output.resolve().is_relative_to(root):
        raise ValueError("The releases folder resolves outside the selected repository")
    output.mkdir(exist_ok=True)
    archive = output / "agent-skills.zip"
    checksum = output / "agent-skills.zip.sha256"
    for path in (archive, checksum):
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError("A release output resolves outside the selected repository")
    archive.write_bytes(raw)
    fingerprint = hashlib.sha256(raw).hexdigest()
    checksum.write_text(f"{fingerprint}  agent-skills.zip\n", encoding="ascii")
    return {"archive": str(archive), "sha256": fingerprint, "version": version, "manifest_sha256": hashlib.sha256(json_bytes(manifest)).hexdigest(), "skills": len(PACKAGES),
            "skill_files": len(payload) - len(guidance) - 1, "archive_entries": len(payload), "bytes": len(raw)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--version", required=True, help="Published release tag, for example v1.1.0")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(build(args.project_root, args.version)))
        return 0
    except (OSError, ValueError, SyntaxError, zipfile.BadZipFile) as exc:
        print(json.dumps({"status": "error", "reason": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
