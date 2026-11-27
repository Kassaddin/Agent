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
import re
from bundle_setup import bundle

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/update/scripts"))
from release_format import MANIFEST, make_manifest, json_bytes

PACKAGES = ("backlog", "project-context", "create-skill", "elevated-rights", "fix", "glossary", "google", "implement", "init", "orchestrator", "refine", "search", "setup", "smokes", "to-document", "to-tasks", "update")
EXCLUDED = {"__pycache__", ".pytest_cache", ".git", ".venv", "node_modules"}
EXTENSIONS = {".md", ".yaml", ".yml", ".json", ".py", ".txt"}
SETUP_PATH = "Agents/.agents/skills/setup/"
SETUP_DOCUMENT_REPOSITORY = re.compile(rb"`https://github\.com/Kassaddin/Agents`")
SETUP_REPOSITORY_REFERENCES = {
    SETUP_PATH + 'SKILL.md': (SETUP_DOCUMENT_REPOSITORY,),
    SETUP_PATH + 'references/setup-contract.md': (SETUP_DOCUMENT_REPOSITORY,),
    SETUP_PATH + 'scripts/setup_kit.py': (
        re.compile(rb"^REPOSITORY = 'Kassaddin/Agents'\r?$", re.M),
    ),
    SETUP_PATH + 'tests/test_setup.py': (
        re.compile(
            rb"^ {8}policy\['resources'\]\['remote'\] = \[\{'id': 'kit', "
            rb"'url': 'https://github\.com/Kassaddin/Agents\.git',", re.M,
        ),
        re.compile(rb"^ {8}self\.source\.repository = 'Kassaddin/Agents'\r?$", re.M),
        re.compile(rb"^ {8}self\.source\.repository = 'Kassaddin/Agent'\r?$", re.M),
    ),
}


def build(project_root, version):
    root = Path(project_root).resolve()
    bundle(root)
    payload, captured = {}, {}
    for name in PACKAGES:
        package = root / ".agents/skills" / name
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
        "Agents/README.md": root / ".agents/assets/release-README.md",
        "Agents/docs/guide.md": root / "docs/guide.md",
        "Agents/.agents/instructions.md": root / ".agents/assets/external-instructions.md",
        "Agents/.gitignore": root / ".agents/assets/release.gitignore",
    }
    for name, source in guidance.items():
        if not source.resolve().is_relative_to(root):
            raise ValueError("Guidance must stay within the selected repository")
        raw = source.read_bytes()
        captured[source] = raw
        if name == 'Agents/.agents/instructions.md':
            rows = []
            for skill in PACKAGES:
                entry = (root / '.agents/skills' / skill / 'SKILL.md').read_text(encoding='utf-8-sig')
                description = re.search(r'^description: (.+)$', entry, re.M).group(1)
                rows.append(f'| `${skill}` | {description} | [Load](skills/{skill}/SKILL.md) |')
            raw = raw.replace(b'<!-- generated-skill-catalog -->', ('| Skill | When to use | Instructions |\n| --- | --- | --- |\n' + '\n'.join(rows)).encode())
        payload[name] = raw.replace(b"(../../docs/guide.md)", b"(docs/guide.md)") if name == "Agents/README.md" else raw
    for name, raw in payload.items():
        scrutinized = raw
        approvals = SETUP_REPOSITORY_REFERENCES.get(name, ())
        for approved in approvals:
            scrutinized = approved.sub(b'', scrutinized, count=1)
        if any(marker.lower() in scrutinized.lower() for marker in (
            b"C:/Users/", b"C:\\Users\\", b"G:/VAULT/", b"Kassaddin/Agent",
        )):
            raise ValueError(f"A project-specific path or repository identity needs review before sharing: {name}")
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
    standalone = output / 'setup.zip'
    for path in (standalone, output / 'setup.zip.sha256'):
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError('A standalone release output resolves outside this repository')
    with zipfile.ZipFile(standalone, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive_file:
        for name, content in sorted(payload.items()):
            prefix = 'Agents/.agents/skills/setup/'
            if name.startswith(prefix):
                item = zipfile.ZipInfo('setup/' + name[len(prefix):], date_time=(1980, 1, 1, 0, 0, 0))
                item.compress_type = zipfile.ZIP_DEFLATED
                archive_file.writestr(item, content)
    standalone_hash = hashlib.sha256(standalone.read_bytes()).hexdigest()
    (output / 'setup.zip.sha256').write_text(f'{standalone_hash}  setup.zip\n', encoding='ascii')
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
