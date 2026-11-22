#!/usr/bin/env python3
"""Validate project boundaries offline; never inspect sources or grant permissions."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
import json
import ntpath
from pathlib import Path
import posixpath
import re
import sys
from urllib.parse import urlsplit

try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML 6.x is required; validation was not performed.")


SCHEMA_PATH = Path(__file__).resolve().parents[1] / "references" / "boundaries.schema.json"


class StrictLoader(yaml.SafeLoader):
    """Safe YAML with unique string keys and JSON-style boolean resolution."""


StrictLoader.yaml_implicit_resolvers = deepcopy(yaml.SafeLoader.yaml_implicit_resolvers)
for _initial, _resolvers in StrictLoader.yaml_implicit_resolvers.items():
    StrictLoader.yaml_implicit_resolvers[_initial] = [
        (tag, pattern)
        for tag, pattern in _resolvers
        if tag not in ("tag:yaml.org,2002:bool", "tag:yaml.org,2002:timestamp")
    ]
StrictLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool", re.compile(r"^(?:true|false)$"), list("tf")
)


def _mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        if key_node.tag == "tag:yaml.org,2002:merge":
            raise ValueError("YAML merge keys are not supported")
        key = loader.construct_object(key_node, deep=True)
        if not isinstance(key, str):
            raise ValueError("YAML mapping keys must be strings")
        if key in result:
            raise ValueError(f"Duplicate YAML key {key!r} at line {key_node.start_mark.line + 1}")
        result[key] = loader.construct_object(value_node, deep=True)
    return result


StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def load_yaml(text):
    for token in yaml.scan(text):
        if isinstance(token, (yaml.tokens.AnchorToken, yaml.tokens.AliasToken, yaml.tokens.TagToken)):
            raise ValueError("YAML anchors, aliases, and explicit tags are not supported")
    return yaml.load(text, Loader=StrictLoader)


def _is_type(value, kind):
    return {
        "object": lambda: isinstance(value, dict),
        "array": lambda: isinstance(value, list),
        "string": lambda: isinstance(value, str),
        "integer": lambda: type(value) is int,
        "boolean": lambda: type(value) is bool,
        "null": lambda: value is None,
    }[kind]()


def _check_schema(value, rule, root, path, errors):
    """Evaluate exactly the JSON Schema keywords used by our bundled schema."""
    supported = {
        "$schema", "title", "$defs", "$ref", "type", "const", "enum",
        "required", "properties", "additionalProperties", "items", "minItems",
        "uniqueItems", "minLength", "pattern",
    }
    if set(rule) - supported:
        raise ValueError("The bundled schema uses an unsupported validation keyword")
    if "$ref" in rule:
        target = root
        for part in rule["$ref"].removeprefix("#/").split("/"):
            target = target[part]
        _check_schema(value, target, root, path, errors)
        return
    kinds = rule.get("type")
    if kinds is not None:
        kinds = kinds if isinstance(kinds, list) else [kinds]
        if not any(_is_type(value, kind) for kind in kinds):
            errors.append(f"{path}: expected {' or '.join(kinds)}")
            return
    if "const" in rule and (type(value) is not type(rule["const"]) or value != rule["const"]):
        errors.append(f"{path}: expected {rule['const']!r}")
    if "enum" in rule and not any(type(value) is type(item) and value == item for item in rule["enum"]):
        errors.append(f"{path}: expected one of {rule['enum']!r}")
    if isinstance(value, dict):
        for key in rule.get("required", []):
            if key not in value:
                errors.append(f"{path}.{key}: required field is missing")
        properties = rule.get("properties", {})
        for key, child in value.items():
            if key in properties:
                _check_schema(child, properties[key], root, f"{path}.{key}", errors)
            elif rule.get("additionalProperties") is False:
                errors.append(f"{path}.{key}: unknown field")
    if isinstance(value, list):
        if len(value) < rule.get("minItems", 0):
            errors.append(f"{path}: not enough entries")
        if rule.get("uniqueItems") and len({json.dumps(item, sort_keys=True) for item in value}) != len(value):
            errors.append(f"{path}: duplicate entries")
        for index, item in enumerate(value):
            if "items" in rule:
                _check_schema(item, rule["items"], root, f"{path}[{index}]", errors)
    if isinstance(value, str):
        if len(value.strip()) < rule.get("minLength", 0):
            errors.append(f"{path}: value is empty")
        if "pattern" in rule and re.search(rule["pattern"], value) is None:
            errors.append(f"{path}: invalid value format")


def _path_key(value):
    """Normalize syntax only, without touching any resource on disk."""
    if value != value.strip() or re.search(r"[\x00-\x1f*?]|\$[A-Za-z_{]|%[^%]+%", value) or value.startswith("~"):
        raise ValueError("use a literal absolute path without wildcards or environment variables")
    windows = bool(re.match(r"^[A-Za-z]:", value) or value.startswith("\\\\") or value.startswith("//"))
    module = ntpath if windows else posixpath
    if not module.isabs(value) or (windows and not ntpath.splitdrive(value)[0]):
        raise ValueError("path must be absolute, including a Windows drive or UNC share")
    if windows and value.startswith(("\\\\", "//")):
        drive = ntpath.splitdrive(value)[0].replace("/", "\\")
        if len([part for part in drive.split("\\") if part]) != 2:
            raise ValueError("UNC paths require both server and share")
    if not windows and "\\" in value:
        raise ValueError("use an absolute Windows path or POSIX separators")
    return ("windows" if windows else "posix", module.normpath(value).casefold() if windows else module.normpath(value))


def _remote_key(value):
    if value != value.strip() or re.search(r"\s|[\x00-\x1f]", value):
        raise ValueError("URL contains whitespace")
    scp = re.fullmatch(r"([^@:/]+)@([^:/]+):(.+)", value)
    if scp and "://" not in value:
        if "?" in value or "#" in value or "@" in scp[1]:
            raise ValueError("query, fragment, or malformed SSH address")
        return f"{scp[1]}@{scp[2].lower()}:{scp[3].rstrip('/')}"
    parsed = urlsplit(value)
    if parsed.scheme not in ("https", "http", "ssh") or not parsed.hostname:
        raise ValueError("use an HTTP(S), SSH, or SCP-style remote URL")
    if parsed.query or parsed.fragment or parsed.password:
        raise ValueError("queries, fragments, and passwords are not allowed in source URLs")
    if parsed.scheme in ("http", "https") and parsed.username:
        raise ValueError("HTTP source URLs must not contain credentials")
    parsed.port  # Validate a malformed port without connecting.
    user = f"{parsed.username}@" if parsed.username else ""
    port = f":{parsed.port}" if parsed.port is not None else ""
    return f"{parsed.scheme}://{user}{parsed.hostname.lower()}{port}{parsed.path.rstrip('/')}"


def _timestamp(value):
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
        return "T" in value and parsed.tzinfo is not None and parsed.utcoffset() is not None
    except (TypeError, ValueError):
        return False


def validate_document(data, require_active=False):
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors, warnings = [], []
    _check_schema(data, schema, schema, "$", errors)
    if errors:
        return errors, warnings
    if require_active and data["state"] != "active":
        errors.append("$.state: active configuration required")
    if data["approvals"].get("allow_read_only_search_worker", False) and data["conversation"]["delegate_work"] == "never":
        warnings.append("Search-worker standing approval is inactive because delegation is never")
    vcs = data["version_control"]
    if vcs["workflow"] == "local_current_branch":
        for operation in ("create_branch", "create_worktree", "switch_revision", "publish_changes", "overwrite_remote_history", "create_pull_request"):
            if vcs["operations"][operation] in ("act", "ask"):
                errors.append(f"version_control.operations.{operation}: incompatible with local_current_branch workflow")

    local = data["resources"]["local"]
    remotes = data["resources"]["remote"]
    ids, paths, urls = set(), {}, set()
    for source in local + remotes:
        if source["id"] in ids:
            errors.append(f"resources: duplicate source ID {source['id']!r}")
        ids.add(source["id"])
    local_ids = {item["id"] for item in local}
    primary = next((item for item in local if item["id"] == data["project"]["primary_local_id"]), None)
    if primary is None or primary["kind"] != "directory":
        errors.append("project.primary_local_id: must identify a local directory")
    for source in local:
        label = f"local[{source['id']}]"
        try:
            key = _path_key(source["path"])
            if key in paths:
                errors.append(f"{label}.path: duplicates another normalized local path")
            paths[key] = source
        except ValueError as exc:
            errors.append(f"{label}.path: {exc}")
        if source["kind"] == "file" and source["recursive"]:
            errors.append(f"{label}: a file cannot be recursive")
    entries = list(paths.items())
    for index, ((kind, path), source) in enumerate(entries):
        for (other_kind, other_path), other in entries[index + 1:]:
            if kind != other_kind:
                continue
            module = ntpath if kind == "windows" else posixpath
            try:
                common = module.commonpath([path, other_path])
            except ValueError:
                continue
            parent = source if common == path else other if common == other_path else None
            if parent and parent["kind"] == "directory" and parent["recursive"]:
                warnings.append(f"Local scopes {source['id']!r} and {other['id']!r} overlap; all matching restrictions apply")

    for source in remotes:
        label = f"remote[{source['id']}]"
        try:
            key = _remote_key(source["url"])
            if key in urls:
                errors.append(f"{label}.url: duplicate remote source")
            urls.add(key)
        except ValueError as exc:
            errors.append(f"{label}.url: {exc}")
        if not set(source["local_ids"]).issubset(local_ids):
            errors.append(f"{label}.local_ids: contains an unknown local source ID")
        access = source["access"]
        status, capability, mode = access["status"], access["capability"], source["effective_mode"]
        for field, value in (("access.checked_at", access["checked_at"]), ("trust_granted_at", source["trust_granted_at"])):
            if value is not None and not _timestamp(value):
                errors.append(f"{label}.{field}: use an ISO 8601 timestamp with timezone")
        if status == "unchecked" and (mode != "none" or capability != "unknown" or access["checked_at"] is not None):
            errors.append(f"{label}: unchecked sources require mode none, capability unknown, and no check timestamp")
        if status == "unavailable" and mode != "none":
            errors.append(f"{label}: unavailable sources require effective mode none")
        if status in ("limited", "unavailable") and not access["reason"]:
            errors.append(f"{label}: {status} sources require a reason")
        if status in ("ready", "limited"):
            if access["checked_at"] is None:
                errors.append(f"{label}: usable sources require an actual access-check timestamp")
            if mode == "none" or capability not in ("read", "write") or (mode == "write" and capability != "write"):
                errors.append(f"{label}: effective mode exceeds verified capability")
        if status == "ready" and mode != source["requested_mode"]:
            errors.append(f"{label}: ready mode must match requested mode")
        if status == "limited" and (source["requested_mode"] != "write" or mode != "read"):
            errors.append(f"{label}: limited means an accepted read-only fallback for requested write access")
        if source["write_approval"] == "trusted_for_source":
            if status != "ready" or mode != "write" or source["trust_granted_at"] is None:
                errors.append(f"{label}: trust requires ready write access and an explicit grant timestamp")
            if source["kind"] in ("git_repository", "version_control_repository"):
                warnings.append(f"{label}: remote-write trust does not override version-control restrictions")
        elif source["trust_granted_at"] is not None:
            errors.append(f"{label}: ask_each_time requires trust_granted_at null")
        if status in ("unchecked", "unavailable"):
            warnings.append(f"{label}: source cannot be used while {status}")

    return errors, warnings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--require-active", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    try:
        data = load_yaml(args.file.read_text(encoding="utf-8-sig"))
        errors, warnings = validate_document(data, args.require_active)
    except (OSError, UnicodeError, ValueError, yaml.YAMLError) as exc:
        # Do not echo parser snippets: malformed input can contain credentials.
        if isinstance(exc, yaml.YAMLError):
            message = "Invalid or unsupported YAML syntax"
        elif isinstance(exc, OSError):
            message = "Could not read the configuration or bundled schema"
        else:
            message = str(exc)
        errors, warnings = [message], []
    if args.as_json:
        print(json.dumps({"valid": not errors, "errors": errors, "warnings": warnings}))
    else:
        for message in errors:
            print(f"ERROR: {message}")
        for message in warnings:
            print(f"WARNING: {message}")
        print("Boundary file is invalid." if errors else "Boundary file is valid (offline checks only).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
