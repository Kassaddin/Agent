"""Behavioral release/update fixtures: no Git command, live network, or real project mutation."""
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
import update_kit as update
import release_format as fmt
from release_source import NoRelease


def payload(value="one", extras=None):
    main = f"---\nname: foo\ndescription: Refine the fixture topic.\n---\n\n# Foo\n\n{value}\n".encode()
    return {".agent/skills/foo/SKILL.md": main, **(extras or {})}


def artifact(files, version="v1.0.0", *, legacy=False, manifest_change=None, extra_zip=None):
    data = fmt.make_manifest(files, version)
    if manifest_change:
        manifest_change(data)
    raw = io.BytesIO()
    with zipfile.ZipFile(raw, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr("Agents/" + name, content)
        if not legacy:
            archive.writestr("Agents/" + fmt.MANIFEST, fmt.json_bytes(data))
        if extra_zip:
            for name, content in extra_zip.items():
                archive.writestr(name, content)
    raw = raw.getvalue()
    return raw, f"{fmt.sha(raw)}  agent-skills.zip\n".encode()


class FakeSource:
    repository = "example/kit"

    def __init__(self, versions, latest=None):
        self.versions = versions
        self.latest = latest or next(reversed(versions))

    def select(self, version=None):
        version = version or self.latest
        if version not in self.versions:
            raise NoRelease("No published release fixture")
        return {"tag_name": version, "id": list(self.versions).index(version) + 1}

    def releases(self):
        return [self.select(version) for version in reversed(self.versions)]

    def package(self, release, *, legacy_baseline=False):
        version = release["tag_name"]
        raw, checksum = self.versions[version]
        result = fmt.unpack(raw, checksum, version, legacy_baseline=legacy_baseline)
        result["identity"] = {"repository": self.repository, "version": version, "release_id": release["id"], "asset_id": release["id"] * 10, "archive_sha256": fmt.sha(raw)}
        return result


class UpdateTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="kit-update-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.kit = self.root / "Agents"
        self.old = payload()
        self.new = payload("two")
        self.source = FakeSource({"v1.0.0": artifact(self.old), "v1.1.0": artifact(self.new, "v1.1.0")})
        self.policy = update.INIT.load_yaml((SKILL.parent / "init/assets/boundaries-template.yaml").read_text(encoding="utf-8"))
        self.policy["state"] = "active"
        self.policy["project"]["name"] = "Update fixture"
        self.policy["resources"]["local"][0]["path"] = str(self.root)
        self.policy["resources"]["local"][0]["permissions"]["delete"] = "act"
        self.policy["resources"]["remote"] = [{"id": "origin", "url": "https://github.com/example/kit.git", "kind": "git_repository", "local_ids": ["project"],
            "requested_mode": "read", "effective_mode": "read", "access": {"capability": "read", "status": "ready", "visibility": "public", "checked_at": "2026-11-23T00:00:00Z", "reason": None},
            "write_approval": "ask_each_time", "trust_granted_at": None}]
        self.boundaries = self.root / "policy.yaml"
        self.save_policy()
        self.install(self.old)

    def save_policy(self):
        self.boundaries.write_text(update.INIT.yaml.safe_dump(self.policy, sort_keys=False), encoding="utf-8")

    def install(self, files, version="v1.0.0", legacy=False):
        for name, raw in files.items():
            path = self.kit / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        if not legacy:
            manifest = self.kit / fmt.MANIFEST
            manifest.parent.mkdir(parents=True, exist_ok=True)
            manifest.write_bytes(fmt.json_bytes(fmt.make_manifest(files, version)))

    def updater(self, approvals=()):
        return update.Updater(self.boundaries, self.kit, "origin", source=self.source, approvals=approvals)

    def execute(self, updater=None, **kwargs):
        updater = updater or self.updater()
        plan = updater.plan()
        return updater.apply(plan, expected_sha=plan.get("archive_sha256"), notified=True, **kwargs)

    def restrict(self, path, **permissions):
        resource = deepcopy(self.policy["resources"]["local"][0])
        resource.update(id="restricted", path=str(path))
        resource["permissions"].update(permissions)
        self.policy["resources"]["local"].append(resource)
        self.save_policy()

    def test_clean_update_and_receipt_match_published_candidate(self):
        result = self.execute()
        self.assertEqual(result["status"], "updated")
        self.assertEqual((self.kit / ".agent/skills/foo/SKILL.md").read_bytes(), self.new[".agent/skills/foo/SKILL.md"])
        receipt = fmt.strict_json((self.kit / update.RECEIPT).read_bytes())
        self.assertEqual(receipt["identity"]["version"], "v1.1.0")
        self.assertTrue(Path(result["markdown"]).is_file())
        self.assertIn("[Structured outcome]", Path(result["markdown"]).read_text(encoding="utf-8"))

    def test_check_and_already_current_do_not_write(self):
        before = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(self.updater().plan()["status"], "ready")
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()})
        self.execute()
        before = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(self.execute()["status"], "already_current")
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()})

    def test_local_edits_and_local_deletions_pause_entire_bundle(self):
        file = self.kit / ".agent/skills/foo/SKILL.md"
        file.write_bytes(b"Local work")
        self.assertEqual(self.updater().plan()["status"], "conflicts")
        self.assertEqual(file.read_bytes(), b"Local work")
        file.unlink()
        self.assertEqual(self.updater().plan()["status"], "conflicts")

    def test_new_unmanaged_path_collision_is_not_silently_adopted(self):
        extras = {".agent/skills/foo/new.txt": b"same"}
        self.source.versions["v1.1.0"] = artifact(payload("two", extras), "v1.1.0")
        path = self.kit / ".agent/skills/foo/new.txt"
        path.write_bytes(b"same")
        self.assertEqual(self.updater().plan()["status"], "conflicts")

    def test_unmanaged_and_protected_host_files_survive(self):
        paths = {self.root / "README.md": b"Host README", self.root / "documentation/terms.md": b"Host definitions",
                 self.kit / ".agent/config/BOUNDARIES.yaml": b"Keep configuration", self.kit / ".agent/state/checkpoints/topic.yaml": b"Keep checkpoint",
                 self.kit / ".agent/context/project.md": b"Keep context", self.kit / ".agent/skills/custom/note.txt": b"Unmanaged addon"}
        for path, raw in paths.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        self.execute()
        self.assertEqual(paths, {p: p.read_bytes() for p in paths})

    def test_managed_removal_and_new_skill_follow_release_inventory(self):
        removed = ".agent/skills/foo/retired.txt"
        old = payload(extras={removed: b"old"})
        self.install(old)
        self.source.versions["v1.0.0"] = artifact(old)
        bar = b"---\nname: bar\ndescription: Another fixture skill.\n---\n# Bar\n"
        self.source.versions["v1.1.0"] = artifact(payload("two", {".agent/skills/bar/SKILL.md": bar}), "v1.1.0")
        self.assertEqual(self.execute()["status"], "updated")
        self.assertFalse((self.kit / removed).exists())
        self.assertTrue((self.kit / ".agent/skills/bar/SKILL.md").exists())

    def test_delete_ask_needs_real_grant_and_never_cannot_be_overridden(self):
        old = payload(extras={".agent/skills/foo/retired.txt": b"old"})
        self.install(old)
        self.source.versions["v1.0.0"] = artifact(old)
        self.restrict(self.kit / ".agent/skills/foo", delete="ask")
        with self.assertRaises(update.Blocked):
            self.execute()
        self.assertEqual(self.execute(self.updater(["delete:Agents/.agent/skills/foo"]))["status"], "updated")
        self.install(old)
        (self.kit / update.RECEIPT).unlink()
        self.policy["resources"]["local"][-1]["permissions"]["delete"] = "never"
        self.save_policy()
        with self.assertRaises(update.Blocked):
            self.execute(self.updater(["delete:Agents/.agent/skills/foo"]))

    def test_unknown_legacy_baseline_stops_and_matching_published_one_can_be_used(self):
        (self.kit / fmt.MANIFEST).unlink()
        self.source.versions["v1.0.0"] = artifact(self.old, legacy=True)
        self.assertEqual(self.updater().plan()["status"], "ready")
        self.assertEqual(self.execute()["status"], "updated")
        (self.kit / fmt.MANIFEST).unlink()
        (self.kit / update.RECEIPT).unlink()
        (self.kit / ".agent/skills/foo/SKILL.md").write_bytes(b"Unknown installation")
        with self.assertRaises(update.Conflict):
            self.updater().plan()

    def test_manifest_and_receipt_drift_cannot_redefine_ownership(self):
        self.execute()
        receipt = self.kit / update.RECEIPT
        value = fmt.strict_json(receipt.read_bytes())
        value["identity"]["release_id"] = 999
        receipt.write_bytes(fmt.json_bytes(value))
        with self.assertRaises(update.Conflict):
            self.updater().plan()

    def test_concurrent_edit_after_comparison_is_preserved(self):
        updater = self.updater()
        plan = updater.plan()
        file = self.kit / ".agent/skills/foo/SKILL.md"
        file.write_bytes(b"New user work")
        with self.assertRaises(update.Conflict):
            updater.apply(plan, expected_sha=plan["archive_sha256"], notified=True)
        self.assertEqual(file.read_bytes(), b"New user work")

    def test_failure_restores_original_files(self):
        def fail(_):
            raise RuntimeError("Injected failure")
        result = self.execute(after_write=fail)
        self.assertEqual(result["status"], "rolled_back")
        self.assertEqual((self.kit / ".agent/skills/foo/SKILL.md").read_bytes(), self.old[".agent/skills/foo/SKILL.md"])
        self.assertIsNone(self.updater().pending())

    def test_recovery_does_not_overwrite_concurrent_user_work(self):
        file = self.kit / ".agent/skills/foo/SKILL.md"
        def fail(_):
            file.write_bytes(b"Concurrent user work")
            raise RuntimeError("Injected failure")
        result = self.execute(after_write=fail)
        self.assertEqual(result["status"], "recovery_required")
        self.assertEqual(file.read_bytes(), b"Concurrent user work")
        self.assertEqual(self.updater().plan()["status"], "recovery_required")

    def test_interruption_can_be_recovered_without_running_new_code(self):
        def interrupt(_):
            raise SystemExit("Simulated process interruption")
        with self.assertRaises(SystemExit):
            self.execute(after_write=interrupt)
        result = self.updater().recover()
        self.assertEqual(result["status"], "rolled_back")
        self.assertEqual((self.kit / ".agent/skills/foo/SKILL.md").read_bytes(), self.old[".agent/skills/foo/SKILL.md"])

    def test_missing_original_backup_never_becomes_a_delete(self):
        with self.assertRaises(SystemExit):
            self.execute(after_write=lambda _: (_ for _ in ()).throw(SystemExit()))
        updater = self.updater()
        run = updater.pending()
        name = ".agent/skills/foo/SKILL.md"
        backup = self.kit / f".agent/state/update/runs/{run}/backups/{fmt.sha(name.encode())}.bin"
        backup.unlink()
        self.assertEqual(updater.recover()["status"], "recovery_required")
        self.assertEqual((self.kit / name).read_bytes(), self.new[name])

    def test_missing_recovery_permission_is_explicit_and_can_be_granted_later(self):
        self.policy["resources"]["local"][0]["permissions"]["delete"] = "ask"
        self.save_policy()
        self.source.versions["v1.1.0"] = artifact(payload("two", {".agent/skills/foo/new.txt": b"new"}), "v1.1.0")
        def fail(name):
            if name.endswith("new.txt"):
                raise RuntimeError("Injected failure after new-file creation")
        first = self.execute(after_write=fail)
        self.assertEqual(first["status"], "recovery_required")
        first_json = Path(first["json"]).read_bytes()
        recovered = self.updater(["delete:Agents/.agent/skills/foo/new.txt"]).recover()
        self.assertEqual(recovered["status"], "rolled_back")
        self.assertEqual(Path(first["json"]).read_bytes(), first_json)
        self.assertNotEqual(first["json"], recovered["json"])

    def test_invalid_candidate_links_and_wrong_preview_hash_stop(self):
        updater = self.updater()
        plan = updater.plan()
        with self.assertRaises(update.Conflict):
            updater.apply(plan, expected_sha="0" * 64, notified=True)
        self.source.versions["v1.1.0"] = artifact(payload("[Missing](missing.md)"), "v1.1.0")
        with self.assertRaises(fmt.ReleaseError):
            self.updater().plan()

    def test_notification_and_read_only_source_rules_still_apply(self):
        updater = self.updater()
        plan = updater.plan()
        with self.assertRaises(update.Blocked):
            updater.apply(plan, expected_sha=plan["archive_sha256"])
        self.policy["resources"]["remote"][0]["effective_mode"] = "none"
        self.policy["resources"]["remote"][0]["access"].update(status="unavailable", capability="none", reason="Unavailable")
        self.save_policy()
        with self.assertRaises(update.Blocked):
            self.updater().plan()

    def test_kit_cannot_be_primary_project_or_global_installation(self):
        for target in (self.root, self.root.parent / "outside-kit"):
            with self.assertRaises(update.Blocked):
                update.Updater(self.boundaries, target, "origin", source=self.source)

    def test_new_python_code_is_parsed_but_not_executed(self):
        marker = self.root / "executed.txt"
        script = f"from pathlib import Path\nPath({str(marker)!r}).write_text('bad')\n".encode()
        self.source.versions["v1.1.0"] = artifact(payload("two", {".agent/skills/foo/scripts/new.py": script}), "v1.1.0")
        self.assertEqual(self.execute()["status"], "updated")
        self.assertFalse(marker.exists())

    def test_kit_can_be_the_only_permitted_primary_root(self):
        self.policy["resources"]["local"][0]["path"] = str(self.kit)
        self.save_policy()
        self.assertEqual(self.execute()["status"], "updated")

    def test_global_implementation_prohibition_blocks_even_allowed_file_writes(self):
        self.policy["conversation"]["implement_when_requested"] = "never"
        self.save_policy()
        with self.assertRaises(update.Blocked):
            self.execute()
        self.assertEqual((self.kit / ".agent/skills/foo/SKILL.md").read_bytes(), self.old[".agent/skills/foo/SKILL.md"])

    def test_denied_read_is_not_opened_and_policy_drift_stops(self):
        file = self.kit / ".agent/skills/foo/SKILL.md"
        self.restrict(file.parent, read="never")
        original = Path.open
        def guarded(path, *args, **kwargs):
            self.assertNotEqual(path, file)
            return original(path, *args, **kwargs)
        with mock.patch.object(Path, "open", guarded), self.assertRaises(update.Blocked):
            self.updater().plan()
        self.policy["resources"]["local"].pop()
        self.save_policy()
        updater = self.updater()
        plan = updater.plan()
        self.policy["conversation"]["investigate_within_scope"] = "never"
        self.save_policy()
        with self.assertRaises(update.AccessError):
            updater.apply(plan, expected_sha=plan["archive_sha256"], notified=True)

    def test_downgrade_requires_explicit_version(self):
        self.execute()
        self.source.latest = "v1.0.0"
        with self.assertRaises(update.Conflict):
            self.updater().plan()
        self.assertEqual(self.updater().plan("v1.0.0")["status"], "ready")

    def test_prerelease_tag_needs_explicit_selection_even_if_provider_marks_latest(self):
        self.source.versions["v1.2.0-beta"] = artifact(payload("beta"), "v1.2.0-beta")
        self.source.latest = "v1.2.0-beta"
        with self.assertRaises(update.Conflict):
            self.updater().plan()
        self.assertEqual(self.updater().plan("v1.2.0-beta")["status"], "ready")

    def test_same_version_replaced_asset_stops(self):
        self.execute()
        self.source.versions["v1.1.0"] = artifact(payload("replacement"), "v1.1.0")
        with self.assertRaises(update.Conflict):
            self.updater().plan()

    def test_candidate_policy_schema_cannot_silently_migrate_permissions(self):
        init_skill = b"---\nname: init\ndescription: Setup fixture boundaries.\n---\n# Init\n"
        extras = {".agent/skills/init/SKILL.md": init_skill,
                  ".agent/skills/init/references/boundaries.schema.json": fmt.json_bytes({"type": "object", "required": ["new_consequential_policy_choice"]})}
        self.source.versions["v1.1.0"] = artifact(payload("two", extras), "v1.1.0")
        before = self.boundaries.read_bytes()
        with self.assertRaises(fmt.ReleaseError):
            self.updater().plan()
        self.assertEqual(self.boundaries.read_bytes(), before)

    def test_completed_commit_with_interrupted_bookkeeping_is_not_rolled_back(self):
        updater = self.updater()
        original = updater.write
        def interrupted(name, raw):
            if name == update.PENDING and raw == fmt.json_bytes({"run": None}):
                raise SystemExit("Interrupted after a verified commit")
            return original(name, raw)
        with mock.patch.object(updater, "write", interrupted), self.assertRaises(SystemExit):
            self.execute(updater)
        result = self.updater().recover()
        self.assertEqual(result["status"], "updated")
        self.assertEqual((self.kit / ".agent/skills/foo/SKILL.md").read_bytes(), self.new[".agent/skills/foo/SKILL.md"])

    def test_lock_prevents_a_second_updater_from_applying(self):
        first, second = self.updater(), self.updater()
        plan = second.plan()
        with first.lock(), self.assertRaises(update.Blocked):
            second.apply(plan, expected_sha=plan["archive_sha256"], notified=True)

    def test_report_permission_failure_leaves_managed_files_untouched(self):
        self.restrict(self.kit / "docs/reports", create="never")
        with self.assertRaises(update.Blocked):
            self.execute()
        self.assertEqual((self.kit / ".agent/skills/foo/SKILL.md").read_bytes(), self.old[".agent/skills/foo/SKILL.md"])

    def test_recovery_uses_local_backups_when_remote_access_is_unavailable(self):
        with self.assertRaises(SystemExit):
            self.execute(after_write=lambda _: (_ for _ in ()).throw(SystemExit()))
        self.policy["resources"]["remote"][0]["effective_mode"] = "none"
        self.policy["resources"]["remote"][0]["access"].update(status="unavailable", capability="none", reason="No access")
        self.save_policy()
        self.assertEqual(self.updater().recover()["status"], "rolled_back")


class FormatTests(unittest.TestCase):
    def test_traversal_wrong_hash_and_private_inventory_fail(self):
        raw, checksum = artifact(payload(), extra_zip={"Agents/../escape.txt": b"bad"})
        with self.assertRaises(fmt.ReleaseError):
            fmt.unpack(raw, checksum, "v1.0.0")
        raw, checksum = artifact(payload())
        with self.assertRaises(fmt.ReleaseError):
            fmt.unpack(raw, b"0" * 64 + b"  agent-skills.zip\n", "v1.0.0")
        with self.assertRaises(fmt.ReleaseError):
            fmt.make_manifest({**payload(), ".agent/config/BOUNDARIES.yaml": b"forbidden"}, "v1.0.0")

    def test_case_collisions_and_incompatible_protocol_fail(self):
        with self.assertRaises(fmt.ReleaseError):
            artifact({**payload(), ".agent/skills/foo/a.txt": b"a", ".agent/skills/foo/A.txt": b"b"})
        raw, checksum = artifact(payload(), manifest_change=lambda m: m.update(min_update_protocol=99))
        with self.assertRaises(fmt.ReleaseError):
            fmt.unpack(raw, checksum, "v1.0.0")

    def test_manifest_is_not_self_hashed_and_legacy_is_baseline_only(self):
        data = fmt.make_manifest(payload(), "v1.0.0")
        self.assertNotIn(fmt.MANIFEST, fmt.validate_manifest(data))
        raw, checksum = artifact(payload(), legacy=True)
        with self.assertRaises(fmt.ReleaseError):
            fmt.unpack(raw, checksum, "v1.0.0")
        self.assertEqual(fmt.unpack(raw, checksum, "v1.0.0", legacy_baseline=True)["manifest"]["version"], "v1.0.0")

    def test_duplicate_json_and_reserved_paths_fail(self):
        with self.assertRaises(fmt.ReleaseError):
            fmt.strict_json(b'{"same":1,"same":2}')
        for name in ("/absolute", "a/../b", "a\\b", "a/CON.txt", "a/file.", "a//b"):
            with self.assertRaises(fmt.ReleaseError):
                fmt.safe_path(name)


if __name__ == "__main__":
    unittest.main()
