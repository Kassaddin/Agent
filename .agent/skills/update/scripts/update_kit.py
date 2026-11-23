#!/usr/bin/env python3
"""Update one project-local kit from published releases; default is a non-writing check."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import posixpath
import re
import sys
from urllib.parse import quote, unquote, urlsplit
import uuid

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "smokes/scripts"))
from validate_report import BoundaryAccess, AccessError, INIT
from check_artifacts import markdown_links, heading_anchors
from release_format import MANIFEST, ReleaseError, json_bytes, managed_path, safe_path, sha, strict_json, validate_manifest, version_key
from release_source import GitHubSource, NoRelease, SourceError, repository_identity

RECEIPT = ".agent/state/update/receipt.json"
PENDING = ".agent/state/update/pending.json"


class Blocked(RuntimeError):
    pass


class Conflict(RuntimeError):
    pass


class Access:
    def __init__(self, boundaries, approvals=()):
        self.policy = BoundaryAccess(boundaries)
        self.data = self.policy.data
        primary = self.data["project"]["primary_local_id"]
        self.root = Path(os.path.abspath(next(item["path"] for item in self.data["resources"]["local"] if item["id"] == primary)))
        self.approvals = []
        for value in approvals:
            op, _, relative = value.partition(":")
            if op not in {"read", "create", "modify", "delete"} or not relative:
                raise ValueError("Approvals require operation:project-relative-path")
            path = self.root if relative == "." else self.root / safe_path(relative)
            self.approvals.append((op, path))

    def require(self, path, op="read"):
        self.policy.unchanged()
        if op != "read" and self.data["conversation"]["implement_when_requested"] == "never":
            raise Blocked("Implementation is prohibited by the current conversation policy")
        path = Path(os.path.abspath(path))
        if not path.is_relative_to(self.root) or not path.resolve().is_relative_to(self.root.resolve()):
            raise Blocked("Update paths must remain within the primary project")
        granted = any(kind == op and (path == scope or path.is_relative_to(scope)) for kind, scope in self.approvals)
        for target in (path, path.resolve()):
            decision = self.policy.decision(target, op)
            if decision == "never" or decision not in {"act", "ask"} or (decision == "ask" and not granted):
                raise Blocked(f"{op} requires permission at {path.relative_to(self.root).as_posix()} ({decision})")

    def read(self, path):
        self.require(path)
        if not path.exists():
            return None
        if not path.is_file() or path.stat().st_size > 8 * 1024 * 1024:
            raise Blocked("Expected a bounded regular file")
        return path.read_bytes()

    def parents(self, path):
        parent = path.parent
        while True:
            self.require(parent)
            if parent.exists():
                break
            self.require(parent, "create")
            parent = parent.parent

    def write(self, path, raw):
        self.require(path)
        self.require(path, "modify" if path.exists() else "create")
        self.parents(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    def create(self, path, raw):
        self.require(path)
        self.require(path, "create")
        self.parents(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(raw)


def validate_content(bundle):
    files = bundle["files"]
    for name, raw in files.items():
        if name.endswith("/SKILL.md"):
            text = raw.decode("utf-8-sig")
            match = re.match(r"^---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
            front = INIT.load_yaml(match[1]) if match else None
            if not isinstance(front, dict) or front.get("name") != name.split("/")[2] or not isinstance(front.get("description"), str) or not front["description"].strip() or front["description"].startswith("[TODO:"):
                raise ReleaseError("Candidate skill metadata is incomplete")
        if name.endswith((".yaml", ".yml")):
            INIT.load_yaml(raw.decode("utf-8-sig"))
        elif name.endswith(".json"):
            strict_json(raw)
        if name.endswith(".md"):
            for _, target, _ in markdown_links(raw.decode("utf-8-sig")):
                parsed = urlsplit(target)
                if parsed.scheme or parsed.netloc:
                    continue
                if parsed.query:
                    raise ReleaseError("Candidate local query-link semantics are unsupported")
                destination = posixpath.normpath(posixpath.join(posixpath.dirname(name), unquote(parsed.path))) if parsed.path else name
                if destination not in files:
                    raise ReleaseError("Candidate local link does not resolve: " + name)
                if parsed.fragment and destination.endswith(".md") and unquote(parsed.fragment) not in heading_anchors(files[destination].decode("utf-8-sig"))[0]:
                    raise ReleaseError("Candidate heading link does not resolve: " + name)


class Updater:
    def __init__(self, boundaries, kit_root, source_id, *, approvals=(), source=None, reader_reports=None):
        self.access = Access(boundaries, approvals)
        if self.access.data["conversation"]["investigate_within_scope"] != "act":
            raise Blocked("Investigation is not currently permitted")
        self.kit = Path(os.path.abspath(kit_root))
        self.access.require(self.kit)
        if not self.kit.is_dir():
            raise Blocked("Select an existing installed project kit")
        if not self.path(".agent/skills").is_dir():
            raise Blocked("The selected folder has no installed kit skill directory")
        if self.kit == self.access.root and self.kit.name != "Agents" and self.read(MANIFEST) is None:
            raise Blocked("The primary development repository is not an installed kit; select its separate Agents workspace")
        sources = [item for item in self.access.data["resources"]["remote"] if item["id"] == source_id]
        if len(sources) != 1:
            raise Blocked("Select an explicitly configured release source through Init")
        remote = sources[0]
        self.remote_allowed = remote["kind"] == "git_repository" and remote["access"]["status"] in {"ready", "limited"} and remote["effective_mode"] in {"read", "write"} and self.access.data["version_control"]["operations"]["inspect"] == "act"
        self.source = source or GitHubSource(repository_identity(remote["url"]), authorize=self.check_remote)
        if self.source.repository.casefold() != repository_identity(remote["url"]).casefold():
            raise Blocked("Release adapter differs from the configured repository")
        self.source_id = source_id
        self.reader = Path(os.path.abspath(reader_reports)) if reader_reports else self.kit / "docs/reports/update"
        if self.reader.resolve().is_relative_to((self.kit / ".agent").resolve()):
            raise Blocked("Readable update outcomes belong outside the operational area")

    def check_remote(self):
        self.access.policy.unchanged()
        if not self.remote_allowed:
            raise Blocked("Configured repository does not have accepted read-only inspection access")

    def path(self, name):
        safe_path(name)
        path = self.kit / name
        self.access.require(path)
        parent = path
        while parent != self.kit.parent:
            if parent.is_symlink() or (hasattr(parent, "is_junction") and parent.is_junction()):
                raise Blocked("Updater does not follow kit symlinks or junctions")
            parent = parent.parent
        if not path.resolve().is_relative_to(self.kit.resolve()):
            raise Blocked("Kit path resolves outside its workspace")
        return path

    def read(self, name):
        return self.access.read(self.path(name))

    def pending(self):
        raw = self.read(PENDING)
        if raw is None:
            return None
        data = strict_json(raw)
        if not isinstance(data, dict) or set(data) != {"run"} or (data["run"] is not None and not re.fullmatch("[a-f0-9]{32}", str(data["run"]))):
            raise Blocked("Update recovery pointer is invalid; inspect before proceeding")
        return data["run"]

    def baseline(self, baseline_version=None):
        if not self.remote_allowed:
            raise Blocked("Configured repository does not have accepted read-only inspection access")
        manifest_raw, receipt_raw = self.read(MANIFEST), self.read(RECEIPT)
        if receipt_raw is not None:
            receipt = strict_json(receipt_raw)
            if not isinstance(receipt, dict) or set(receipt) != {"schema_version", "identity", "manifest_sha256"} or receipt["schema_version"] != 1 or not manifest_raw or receipt["manifest_sha256"] != sha(manifest_raw):
                raise Conflict("Installed release receipt/manifest is not a verified baseline")
            data = strict_json(manifest_raw)
            validate_manifest(data)
            identity = receipt["identity"]
            if not isinstance(identity, dict) or identity.get("repository", "").casefold() != self.source.repository.casefold() or identity.get("version") != data["version"]:
                raise Conflict("Installed release identity differs from its selected source or manifest")
            published = self.source.package(self.source.select(data["version"]))
            if published["identity"] != identity or published["manifest_raw"] != manifest_raw:
                raise Conflict("Installed receipt no longer matches the verified published baseline")
            return published
        if manifest_raw is not None:
            data = strict_json(manifest_raw)
            validate_manifest(data)
            if baseline_version and baseline_version != data["version"]:
                raise Conflict("Explicit baseline version differs from installed manifest")
            base = self.source.package(self.source.select(data["version"]))
            if base["manifest_raw"] != manifest_raw:
                raise Conflict("Installed manifest differs from the published baseline")
            return base
        if baseline_version:
            return self.source.package(self.source.select(baseline_version), legacy_baseline=True)
        matches = []
        for release in self.source.releases()[:3]:
            base = self.source.package(self.source.select(release["tag_name"]), legacy_baseline=True)
            if all(self.read(name) == raw for name, raw in base["files"].items()):
                matches.append(base)
        if len(matches) != 1:
            raise Conflict("No unique verified baseline was found within three published candidates; supply a known baseline version or stop")
        return matches[0]

    def plan(self, version=None, baseline_version=None):
        pending = self.pending()
        if pending:
            return {"status": "recovery_required", "run": pending}
        if not self.remote_allowed:
            raise Blocked("Configured repository does not have accepted read-only inspection access")
        release = self.source.select(version)
        candidate = self.source.package(release)
        if version is None and version_key(candidate["manifest"]["version"])[1] == 0:
            raise Conflict("Default update does not select a prerelease tag; request it explicitly")
        validate_content(candidate)
        policy_schema = candidate["files"].get(".agent/skills/init/references/boundaries.schema.json")
        if policy_schema is not None:
            try:
                schema = strict_json(policy_schema)
                errors = []
                INIT._check_schema(self.access.data, schema, schema, "$", errors)
                if errors:
                    raise ReleaseError("Current project policy needs an explicit compatibility/migration decision")
            except (KeyError, TypeError, ValueError, RecursionError) as exc:
                raise ReleaseError("Candidate policy schema is incompatible or unsupported; no migration was executed") from exc
        base = self.baseline(baseline_version)
        old = validate_manifest(base["manifest"])
        if not version and version_key(candidate["manifest"]["version"]) < version_key(base["manifest"]["version"]):
            raise Conflict("Default update would downgrade the kit; choose an explicit version instead")
        if base["manifest"]["version"] == candidate["manifest"]["version"] and base["identity"]["archive_sha256"] != candidate["identity"]["archive_sha256"]:
            raise Conflict("Published content changed under the same version; require a distinct release identity")
        changes, conflicts, before = [], [], {}
        for name in sorted(set(old) | set(candidate["files"])):
            current = self.read(name)
            desired = candidate["files"].get(name)
            before[name] = current
            if name not in old and current is not None:
                conflicts.append({"path": name, "reason": "Incoming path already exists but was not managed by the baseline"})
                continue
            if current == desired:
                continue
            if name in old and (current is None or sha(current) != old[name]["sha256"]):
                conflicts.append({"path": name, "reason": "Managed file differs from its verified baseline"})
                continue
            changes.append({"path": name, "operation": "delete" if desired is None else "create" if current is None else "modify"})
        if conflicts:
            return {"status": "conflicts", "conflicts": conflicts, "version": candidate["manifest"]["version"]}
        receipt = json_bytes({"schema_version": 1, "identity": candidate["identity"], "manifest_sha256": sha(candidate["manifest_raw"])})
        desired = {change["path"]: candidate["files"].get(change["path"]) for change in changes}
        if not changes and self.read(MANIFEST) == candidate["manifest_raw"]:
            return {"status": "already_current", "version": candidate["manifest"]["version"], "archive_sha256": candidate["archive_sha256"]}
        for name, raw in ((MANIFEST, candidate["manifest_raw"]), (RECEIPT, receipt)):
            before[name] = self.read(name)
            desired[name] = raw
        return {"status": "ready", "version": candidate["manifest"]["version"], "archive_sha256": candidate["archive_sha256"],
                "from_version": base["manifest"]["version"], "changes": changes, "candidate": candidate, "before": before, "desired": desired}

    def public_plan(self, plan):
        return {key: value for key, value in plan.items() if key not in {"candidate", "before", "desired"}}

    def write(self, name, raw):
        path = self.path(name)
        if raw is None:
            self.access.require(path, "delete")
            path.unlink()
        else:
            self.access.write(path, raw)

    @contextmanager
    def lock(self):
        path = self.path(".agent/state/update/lock")
        self.access.require(path, "modify" if path.exists() else "create")
        self.access.parents(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            stream = path.open("x+b")
            stream.write(b"0")
            stream.flush()
        except FileExistsError:
            self.access.require(path, "modify")
            stream = path.open("r+b")
        try:
            stream.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            stream.close()
            raise Blocked("Another updater holds this kit's lock") from exc
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)
            stream.close()

    def emit(self, run, status, detail, version=None, attempt=None):
        attempt = attempt or uuid.uuid4().hex
        name = f".agent/reports/update/{attempt}/outcome.json"
        human = self.reader / attempt / "outcome.md"
        result = {"schema_version": 1, "run": run, "status": status, "version": version, "detail": detail,
                  "created_at": datetime.now(timezone.utc).isoformat()}
        target = self.path(name)
        self.access.require(target, "create")
        self.access.require(human, "create")
        if target.exists() or human.exists():
            raise Conflict("Update outcomes are immutable; select a new attempt")
        self.access.parents(human)
        self.access.create(target, json_bytes(result))
        link = quote(os.path.relpath(target, human.parent).replace(os.sep, "/"), safe="/._-")
        rendered = json.dumps(detail, indent=2)
        fence = "~~~"
        while fence in rendered:
            fence += "~"
        text = f"# Update outcome\n\nStatus: {status}\n\nVersion: {version or 'not changed'}\n\n{fence}json\n{rendered}\n{fence}\n\n[Structured outcome]({link})\n"
        self.access.create(human, text.encode("utf-8"))
        return {**result, "json": str(target), "markdown": str(human)}

    def recover(self):
        if not self.pending():
            return {"status": "nothing_to_recover"}
        with self.lock():
            return self._recover()

    def _recover(self, *, emit=True):
        run = self.pending()
        if not run:
            return {"status": "nothing_to_recover"}
        prefix = f".agent/state/update/runs/{run}"
        journal = strict_json(self.read(prefix + "/journal.json"))
        if not isinstance(journal, dict) or set(journal) != {"run", "phase", "entries", "attempted", "version"} or journal["run"] != run:
            raise Blocked("Recovery journal is invalid")
        if journal["phase"] not in {"prepared", "applying", "committed", "rolled_back", "recovery_required"}:
            raise Blocked("Recovery phase is invalid")
        version_key(journal["version"])
        if not isinstance(journal["attempted"], list) or not isinstance(journal["entries"], dict) or len(set(journal["attempted"])) != len(journal["attempted"]) or not set(journal["attempted"]) <= set(journal["entries"]):
            raise Blocked("Recovery inventory is invalid")
        for name, entry in journal["entries"].items():
            if name not in {MANIFEST, RECEIPT}:
                managed_path(name)
            if not isinstance(entry, dict) or set(entry) != {"old_sha256", "new_sha256"} or any(value is not None and (not isinstance(value, str) or not re.fullmatch("[a-f0-9]{64}", value)) for value in entry.values()):
                raise Blocked("Recovery content hashes are invalid")
        if journal["phase"] == "committed":
            drift = [name for name, entry in journal["entries"].items() if (sha(self.read(name)) if self.read(name) is not None else None) != entry["new_sha256"]]
            if drift:
                return self.emit(run, "recovery_required", {"reason": "Committed kit changed; preserve for inspection", "paths": drift}, journal["version"]) if emit else {"status": "recovery_required", "remaining": drift}
            self.write(PENDING, json_bytes({"run": None}))
            return self.emit(run, "updated", {"reason": "Verified committed update; cleared interrupted bookkeeping"}, journal["version"]) if emit else {"status": "updated", "remaining": []}
        remaining = []
        for name in reversed(journal["attempted"]):
            if name not in {MANIFEST, RECEIPT}:
                managed_path(name)
            entry = journal["entries"][name]
            current = self.read(name)
            current_hash = sha(current) if current is not None else None
            if current_hash == entry["old_sha256"]:
                continue
            if current_hash != entry["new_sha256"]:
                remaining.append({"path": name, "reason": "Current content is neither the captured original nor the updater's written value; preserve for review"})
                continue
            try:
                backup = self.read(prefix + "/backups/" + sha(name.encode()) + ".bin") if entry["old_sha256"] is not None else None
                if entry["old_sha256"] is not None and (backup is None or sha(backup) != entry["old_sha256"]):
                    raise Blocked("Original backup is missing or its checksum differs")
                self.write(name, backup)
            except (Blocked, OSError) as exc:
                remaining.append({"path": name, "reason": str(exc)})
        journal["phase"] = "recovery_required" if remaining else "rolled_back"
        self.write(prefix + "/journal.json", json_bytes(journal))
        if not remaining:
            self.write(PENDING, json_bytes({"run": None}))
        return self.emit(run, journal["phase"], {"remaining": remaining}, journal["version"]) if emit else {"status": journal["phase"], "remaining": remaining}

    def apply(self, plan, *, expected_sha, notified=False, after_write=None):
        if plan["status"] != "ready":
            return self.public_plan(plan)
        if expected_sha != plan["archive_sha256"]:
            raise Conflict("Candidate differs from the previewed archive hash")
        if self.access.data["approvals"]["notify_queued_changes"] and not notified:
            raise Blocked("Notify the user of the previewed changes before applying")
        with self.lock():
            return self._apply(plan, after_write=after_write)

    def _apply(self, plan, *, after_write=None):
        if self.pending():
            raise Conflict("Another update needs recovery first")
        for name, old in plan["before"].items():
            if self.read(name) != old:
                raise Conflict("Kit changed after comparison; re-plan without overwriting edits")
        run = uuid.uuid4().hex
        prefix = f".agent/state/update/runs/{run}"
        entries = {name: {"old_sha256": sha(plan["before"][name]) if plan["before"][name] is not None else None,
                          "new_sha256": sha(raw) if raw is not None else None} for name, raw in plan["desired"].items()}
        journal = {"run": run, "phase": "prepared", "entries": entries, "attempted": [], "version": plan["version"]}
        control = [prefix + "/journal.json", PENDING]
        backups = [prefix + "/backups/" + sha(name.encode()) + ".bin" for name in entries if plan["before"][name] is not None]
        for name, raw in plan["desired"].items():
            path = self.path(name)
            self.access.require(path, "delete" if raw is None else "modify" if plan["before"][name] is not None else "create")
            if raw is not None:
                self.access.parents(path)
        for name in control + backups:
            path = self.path(name)
            self.access.require(path, "modify" if path.exists() else "create")
            if name in control:
                self.access.require(path, "modify")
            self.access.parents(path)
        # Outcome permissions are checked before managed writes; a successful run never needs silent access expansion.
        attempt = uuid.uuid4().hex
        for path in (self.path(f".agent/reports/update/{attempt}/outcome.json"), self.reader / attempt / "outcome.md"):
            self.access.require(path, "create")
            self.access.parents(path)
        for name in entries:
            raw = plan["before"][name]
            if raw is not None:
                self.write(prefix + "/backups/" + sha(name.encode()) + ".bin", raw)
        self.write(prefix + "/journal.json", json_bytes(journal))
        pending = self.path(PENDING)
        previous_pending = self.access.read(pending)
        if previous_pending is None:
            pending.parent.mkdir(parents=True, exist_ok=True)
            with pending.open("xb") as stream:
                stream.write(json_bytes({"run": run}))
        else:
            if strict_json(previous_pending) != {"run": None}:
                raise Conflict("Another update acquired the kit")
            self.write(PENDING, json_bytes({"run": run}))
        try:
            journal["phase"] = "applying"
            for name, raw in plan["desired"].items():
                if self.read(name) != plan["before"][name]:
                    raise Conflict("Concurrent edit detected before applying " + name)
                journal["attempted"].append(name)
                self.write(prefix + "/journal.json", json_bytes(journal))
                self.write(name, raw)
                if after_write:
                    after_write(name)
            if any(self.read(name) != raw for name, raw in plan["desired"].items()):
                raise Conflict("Applied file verification did not pass")
            result = self.emit(run, "updated", {"from_version": plan["from_version"], "changes": plan["changes"], "archive_sha256": plan["archive_sha256"]}, plan["version"], attempt)
            journal["phase"] = "committed"
            self.write(prefix + "/journal.json", json_bytes(journal))
            self.write(PENDING, json_bytes({"run": None}))
            return result
        except Exception as exc:
            result = self._recover(emit=False)
            return self.emit(run, result["status"], {"failure": type(exc).__name__, "remaining": result["remaining"]}, plan["version"])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boundaries", required=True, type=Path)
    parser.add_argument("--kit-root", required=True, type=Path)
    parser.add_argument("--source", required=True)
    parser.add_argument("--version")
    parser.add_argument("--baseline-version")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--recover", action="store_true")
    parser.add_argument("--expected-sha")
    parser.add_argument("--notified", action="store_true")
    parser.add_argument("--approve", action="append", default=[])
    parser.add_argument("--reader-reports", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.apply and args.recover:
            raise ValueError("Select apply or recover")
        updater = Updater(args.boundaries, args.kit_root, args.source, approvals=args.approve, reader_reports=args.reader_reports)
        if args.recover:
            result = updater.recover()
        else:
            plan = updater.plan(args.version, args.baseline_version)
            result = updater.apply(plan, expected_sha=args.expected_sha, notified=args.notified) if args.apply else updater.public_plan(plan)
        print(json.dumps(result))
        return 0 if result["status"] in {"ready", "updated", "already_current", "rolled_back", "nothing_to_recover"} else 1
    except NoRelease:
        print(json.dumps({"status": "no_release", "reason": "No published stable release is available"}))
        return 1
    except (Blocked, AccessError, Conflict, SourceError, ReleaseError, OSError, ValueError, TypeError, KeyError, INIT.yaml.YAMLError) as exc:
        status = "blocked" if isinstance(exc, (Blocked, AccessError)) else "baseline_or_content_conflict" if isinstance(exc, Conflict) else "error"
        print(json.dumps({"status": status, "reason": str(exc) if isinstance(exc, (Blocked, AccessError, Conflict, ReleaseError, SourceError)) else "Update input, access, or operation failed; inspect the recovery record before retrying"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
