"""Pure data validation shared by the release producer and updater; no execution or I/O."""
from __future__ import annotations
import ast
import hashlib
import io
import json
from pathlib import PurePosixPath
import re
import stat
import zipfile

MANIFEST = ".agents/release/manifest.json"
LEGACY_MANIFEST = ".agent/release/manifest.json"
BUNDLE = "agent-skills"
PROTOCOL = 2
MAX_ARCHIVE = 32 * 1024 * 1024
MAX_FILE = 8 * 1024 * 1024
MAX_TOTAL = 64 * 1024 * 1024
GUIDANCE = {"README.md", "docs/guide.md", ".agents/instructions.md", ".gitignore"}


class ReleaseError(ValueError):
    pass


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def json_bytes(data):
    return (json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ReleaseError("Duplicate JSON key")
            result[key] = value
        return result
    try:
        return json.loads(raw.decode("utf-8-sig") if isinstance(raw, bytes) else raw, object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ReleaseError("Non-finite JSON value")))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ReleaseError("Invalid UTF-8 JSON") from exc


def version_key(version):
    match = re.fullmatch(r"v?(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?", version or "")
    if not match:
        raise ReleaseError("Release versions must be SemVer tags, optionally prefixed with v")
    identifiers = (match[4] or "").split(".") if match[4] else []
    if any(item.isdigit() and len(item) > 1 and item.startswith("0") for item in identifiers):
        raise ReleaseError("Numeric prerelease identifiers cannot have leading zeros")
    return tuple(map(int, match.group(1, 2, 3))), 0 if identifiers else 1, tuple((0, int(item)) if item.isdigit() else (1, item) for item in identifiers)


def safe_path(value):
    if not isinstance(value, str) or not value or value != value.strip() or any(c in '\\:<>"|?*' for c in value) or any(ord(c) < 32 for c in value):
        raise ReleaseError("Unsafe package path")
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value or any(part in {".", ".."} for part in path.parts):
        raise ReleaseError("Package paths must be canonical relative paths")
    for part in path.parts:
        if part.endswith((".", " ")) or re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", part):
            raise ReleaseError("Nonportable package path")
    return value


def managed_path(path):
    safe_path(path)
    if path in GUIDANCE or path == '.agent/instructions.md':
        return path
    parts = PurePosixPath(path).parts
    if len(parts) >= 4 and parts[0] in {'.agent', '.agents'} and parts[1] == 'skills' and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", parts[2]):
        if any(part in {".git", "__pycache__", ".venv", ".env"} for part in parts[3:]):
            raise ReleaseError("Private or generated package content")
        return path
    raise ReleaseError("Release inventory reaches outside distributable skill/guidance paths")


def make_manifest(payload, version):
    version_key(version)
    skills = sorted({PurePosixPath(path).parts[2] for path in payload if path.startswith((".agents/skills/", '.agent/skills/'))})
    legacy = any(path.startswith('.agent/') for path in payload)
    data = {"format_version": 1, "bundle_id": BUNDLE, "version": version, "layout_version": 2 if legacy else 3, "min_update_protocol": 1 if legacy else PROTOCOL,
            "skills": skills, "files": [{"path": path, "sha256": sha(raw), "bytes": len(raw)} for path, raw in sorted(payload.items())]}
    validate_manifest(data)
    return data


def validate_manifest(data):
    keys = {"format_version", "bundle_id", "version", "layout_version", "min_update_protocol", "skills", "files"}
    if not isinstance(data, dict) or set(data) != keys or type(data["format_version"]) is not int or data["format_version"] != 1 or data["bundle_id"] != BUNDLE:
        raise ReleaseError("Unsupported release manifest")
    version_key(data["version"])
    if type(data["layout_version"]) is not int or data["layout_version"] not in {2, 3} or type(data["min_update_protocol"]) is not int or not 1 <= data["min_update_protocol"] <= PROTOCOL or (data['layout_version'] == 3 and data['min_update_protocol'] < 2):
        raise ReleaseError("Release layout/updater compatibility is not supported")
    if not isinstance(data["skills"], list) or not data["skills"] or not all(isinstance(s, str) and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", s) for s in data["skills"]) or len(set(data["skills"])) != len(data["skills"]):
        raise ReleaseError("Invalid skill inventory")
    files = {}
    if not isinstance(data["files"], list) or not 1 <= len(data["files"]) <= 2000:
        raise ReleaseError("Invalid file inventory size")
    for entry in data["files"]:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256", "bytes"}:
            raise ReleaseError("Invalid inventory entry")
        path = managed_path(entry["path"])
        expected_area = '.agent' if data['layout_version'] == 2 else '.agents'
        if path.startswith(('.agent/', '.agents/')) and not path.startswith(expected_area + '/'):
            raise ReleaseError('Inventory mixes operational namespaces')
        if path.casefold() in {name.casefold() for name in files} or not isinstance(entry["sha256"], str) or not re.fullmatch("[a-f0-9]{64}", entry["sha256"]) or type(entry["bytes"]) is not int or not 0 <= entry["bytes"] <= MAX_FILE:
            raise ReleaseError("Duplicate or invalid inventory entry")
        files[path] = entry
    paths = set(files)
    if any(str(parent) in paths for name in paths for parent in PurePosixPath(name).parents if str(parent) != "."):
        raise ReleaseError("File/directory path collision")
    prefix = '.agent' if data['layout_version'] == 2 else '.agents'
    observed = {PurePosixPath(name).parts[2] for name in paths if name.startswith(prefix + '/skills/')}
    if observed != set(data["skills"]) or any(f"{prefix}/skills/{name}/SKILL.md" not in files for name in observed):
        raise ReleaseError("Incomplete or inconsistent skill inventory")
    return files


def unpack(raw, checksum, expected_version, *, legacy_baseline=False):
    if len(raw) > MAX_ARCHIVE:
        raise ReleaseError("Archive exceeds download limit")
    match = re.fullmatch(r"([a-f0-9]{64})  agent-skills\.zip\r?\n?", checksum.decode("ascii"))
    if not match or sha(raw) != match[1]:
        raise ReleaseError("Archive checksum does not match")
    payload = {}
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            infos = archive.infolist()
            if not 1 <= len(infos) <= 2001 or sum(item.file_size for item in infos) > MAX_TOTAL:
                raise ReleaseError("Archive inventory exceeds limits")
            names = set()
            for item in infos:
                if not item.filename.startswith("Agents/"):
                    raise ReleaseError("Release needs one Agents/ wrapper")
                name = safe_path(item.filename.removeprefix("Agents/"))
                if name.casefold() in names or item.is_dir() or stat.S_ISLNK(item.external_attr >> 16) or item.flag_bits & 1 or item.file_size > MAX_FILE:
                    raise ReleaseError("Duplicate, linked, encrypted, or oversized archive entry")
                names.add(name.casefold())
                if name not in {MANIFEST, LEGACY_MANIFEST}:
                    managed_path(name)
                payload[name] = archive.read(item)
            if archive.testzip() is not None:
                raise ReleaseError("Archive CRC mismatch")
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError) as exc:
        raise ReleaseError("Unsupported or corrupt ZIP") from exc
    manifest_raw = payload.pop(MANIFEST, None)
    legacy_raw = payload.pop(LEGACY_MANIFEST, None)
    if manifest_raw is not None and legacy_raw is not None:
        raise ReleaseError('Archive contains competing layout manifests')
    manifest_raw = manifest_raw if manifest_raw is not None else legacy_raw
    if manifest_raw is None:
        if not legacy_baseline:
            raise ReleaseError("Candidate release has no manifest")
        data = make_manifest(payload, expected_version)
        manifest_raw = json_bytes(data)
    else:
        data = strict_json(manifest_raw)
    files = validate_manifest(data)
    if data["version"] != expected_version or set(files) != set(payload):
        raise ReleaseError("Release identity or manifest membership differs from archive")
    if any(sha(payload[name]) != item["sha256"] or len(payload[name]) != item["bytes"] for name, item in files.items()):
        raise ReleaseError("Manifest content mismatch")
    for name, content in payload.items():
        if name.endswith(".py"):
            try:
                ast.parse(content, filename=name)
            except (SyntaxError, ValueError) as exc:
                raise ReleaseError("Candidate Python syntax is invalid") from exc
    return {"manifest": data, "manifest_raw": manifest_raw, "files": payload, "archive_sha256": sha(raw)}
