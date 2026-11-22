"""Behavioral checks for offline boundary validation; no real source access."""

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
import validate_boundaries as validator


def configuration():
    data = validator.load_yaml((SKILL / "assets" / "boundaries-template.yaml").read_text(encoding="utf-8"))
    data["project"]["name"] = "Boundary tests"
    data["resources"]["local"][0]["path"] = "/project"
    return data


def remote():
    return {
        "id": "origin", "url": "https://example.org/team/project.git",
        "kind": "git_repository", "local_ids": ["project"],
        "requested_mode": "read", "effective_mode": "read",
        "access": {
            "capability": "read", "status": "ready", "visibility": "private",
            "checked_at": "2026-11-22T12:00:00+01:00", "reason": None,
        },
        "write_approval": "ask_each_time", "trust_granted_at": None,
    }


class BoundaryValidationTests(unittest.TestCase):
    def assert_invalid(self, data, fragment=None):
        errors, _ = validator.validate_document(data)
        self.assertTrue(errors)
        if fragment:
            self.assertTrue(any(fragment in error for error in errors), errors)

    def test_template_and_activation(self):
        data = configuration()
        self.assertEqual(validator.validate_document(data)[0], [])
        self.assertTrue(validator.validate_document(data, require_active=True)[0])
        data["state"] = "active"
        self.assertEqual(validator.validate_document(data, require_active=True)[0], [])

    def test_default_inspection_does_not_allow_git_mutations(self):
        vcs = configuration()["version_control"]
        self.assertEqual(vcs["operations"]["inspect"], "act")
        self.assertEqual(vcs["unmapped_mutations"], "user_only")
        for operation, decision in vcs["operations"].items():
            if operation != "inspect":
                self.assertEqual(decision, "never" if operation in ("create_branch", "create_pull_request") else "user_only")

    def test_search_approval_is_optional_and_defaults_to_no_standing_grant(self):
        data = configuration()
        self.assertFalse(data["approvals"]["allow_read_only_search_worker"])
        del data["approvals"]["allow_read_only_search_worker"]
        self.assertEqual(validator.validate_document(data)[0], [])
        data["approvals"]["allow_read_only_search_worker"] = True
        self.assertEqual(validator.validate_document(data)[0], [])

    def test_search_approval_requires_boolean(self):
        data = configuration()
        data["approvals"]["allow_read_only_search_worker"] = "true"
        self.assert_invalid(data, "expected boolean")

    def test_search_grant_cannot_override_never_delegation(self):
        data = configuration()
        data["approvals"]["allow_read_only_search_worker"] = True
        data["conversation"]["delegate_work"] = "never"
        errors, warnings = validator.validate_document(data)
        self.assertFalse(errors)
        self.assertTrue(any("inactive" in warning for warning in warnings))

    def test_duplicate_and_non_string_yaml_keys(self):
        for text in ("state: draft\nstate: active", "outer:\n  read: act\n  read: never", "1: value"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                validator.load_yaml(text)

    def test_workflow_and_operation_rules_cannot_conflict(self):
        data = configuration()
        data["version_control"]["operations"]["publish_changes"] = "ask"
        self.assert_invalid(data, "incompatible with local_current_branch")
        data["version_control"]["workflow"] = "explicit_operations"
        self.assertEqual(validator.validate_document(data)[0], [])

    def test_alias_anchor_merge_and_custom_tag_rejected(self):
        for text in ("a: &rule {read: act}\nb: *rule", "a: !custom value", "a: {<<: {read: act}}"):
            with self.subTest(text=text), self.assertRaises((ValueError, validator.yaml.YAMLError)):
                validator.load_yaml(text)

    def test_boolean_resolution_and_unknown_fields(self):
        self.assertEqual(validator.load_yaml("x: true\ny: yes"), {"x": True, "y": "yes"})
        for edit in (lambda d: d.update(unknown=True), lambda d: d.update(schema_version=True),
                     lambda d: d["approvals"].update(notify_queued_changes="yes"),
                     lambda d: d["defaults"].update(unmatched_operation="allow")):
            data = configuration()
            edit(data)
            self.assert_invalid(data)

    def test_required_fields_and_version(self):
        data = configuration()
        del data["conversation"]["expand_task_scope"]
        self.assert_invalid(data, "required")
        data = configuration()
        data["schema_version"] = 2
        self.assert_invalid(data)

    def test_duplicate_ids_unknown_primary_and_remote_links(self):
        data = configuration()
        data["resources"]["remote"] = [remote()]
        data["resources"]["remote"][0]["id"] = "project"
        self.assert_invalid(data, "duplicate source ID")
        data = configuration()
        data["project"]["primary_local_id"] = "missing"
        self.assert_invalid(data, "primary_local_id")
        data = configuration()
        item = remote()
        item["local_ids"] = ["missing"]
        data["resources"]["remote"] = [item]
        self.assert_invalid(data, "unknown local source")

    def test_paths_are_absolute_literal_and_platform_aware(self):
        for path in ("relative/path", "C:relative", "$PROJECT/path", "%PROJECT%/path", "/project/*", "~/project", "\\\\server"):
            data = configuration()
            data["resources"]["local"][0]["path"] = path
            with self.subTest(path=path):
                self.assert_invalid(data)
        self.assertEqual(validator._path_key("C:/Work/Project"), validator._path_key("c:\\work\\project"))
        self.assertNotEqual(validator._path_key("/Work/Project"), validator._path_key("/work/project"))
        self.assertEqual(validator._path_key("\\\\server\\share\\project")[0], "windows")

    def test_duplicate_paths_and_file_recursion(self):
        data = configuration()
        second = deepcopy(data["resources"]["local"][0])
        second["id"] = "duplicate"
        second["path"] = "/project/./"
        data["resources"]["local"].append(second)
        self.assert_invalid(data, "duplicates another normalized")
        data = configuration()
        data["resources"]["local"][0]["kind"] = "file"
        self.assert_invalid(data, "file cannot be recursive")

    def test_nested_prohibition_is_reported_for_review(self):
        data = configuration()
        child = deepcopy(data["resources"]["local"][0])
        child.update(id="reference", path="/project/REFERENCE", role="reference")
        child["permissions"]["modify"] = "never"
        data["resources"]["local"].append(child)
        errors, warnings = validator.validate_document(data)
        self.assertFalse(errors)
        self.assertTrue(any("overlap" in warning for warning in warnings))

    def test_multiple_projects_vault_and_remote(self):
        data = configuration()
        vault = deepcopy(data["resources"]["local"][0])
        vault.update(id="vault", path="/notes", role="obsidian_vault")
        data["resources"]["local"].append(vault)
        item = remote()
        item.update(id="vault-origin", local_ids=["vault"])
        data["resources"]["remote"] = [item]
        self.assertEqual(validator.validate_document(data)[0], [])

    def test_remote_only_sources(self):
        data = configuration()
        item = remote()
        item["local_ids"] = []
        data["resources"]["remote"] = [item]
        self.assertEqual(validator.validate_document(data)[0], [])

    def test_credential_urls_and_invalid_schemes(self):
        for url in ("https://token@example.org/repo", "https://a:secret@example.org/repo", "https://example.org/repo?token=secret", "https://example.org/repo#secret", "file:///project", "https://example.org:bad/repo"):
            data = configuration()
            item = remote()
            item["url"] = url
            data["resources"]["remote"] = [item]
            with self.subTest(url=url):
                self.assert_invalid(data)
        for url in ("git@example.org:team/project.git", "ssh://git@example.org/team/project.git"):
            self.assertTrue(validator._remote_key(url))

    def test_duplicate_remote_urls(self):
        data = configuration()
        first, second = remote(), remote()
        second.update(id="other", url="https://EXAMPLE.org/team/project.git/")
        data["resources"]["remote"] = [first, second]
        self.assert_invalid(data, "duplicate remote")

    def test_read_access_never_proves_write(self):
        data = configuration()
        item = remote()
        item.update(requested_mode="write", effective_mode="write")
        data["resources"]["remote"] = [item]
        self.assert_invalid(data, "exceeds verified")

    def test_private_inaccessible_source_stays_unavailable(self):
        data = configuration()
        item = remote()
        item["effective_mode"] = "none"
        item["access"].update(capability="none", status="unavailable", reason="Private repository access was declined.")
        data["resources"]["remote"] = [item]
        errors, warnings = validator.validate_document(data)
        self.assertFalse(errors)
        self.assertTrue(any("cannot be used" in warning for warning in warnings))
        item["effective_mode"] = "read"
        self.assert_invalid(data, "unavailable")

    def test_limited_fallback_needs_reason_and_correct_modes(self):
        data = configuration()
        item = remote()
        item["requested_mode"] = "write"
        item["access"].update(status="limited", reason="User accepted read-only fallback.")
        data["resources"]["remote"] = [item]
        self.assertEqual(validator.validate_document(data)[0], [])
        item["access"]["reason"] = None
        self.assert_invalid(data, "require a reason")
        item["requested_mode"] = "read"
        self.assert_invalid(data, "limited means")

    def test_unchecked_sources_do_not_grant_access(self):
        data = configuration()
        item = remote()
        item["access"].update(status="unchecked", capability="unknown", checked_at=None)
        item["effective_mode"] = "none"
        data["resources"]["remote"] = [item]
        self.assertEqual(validator.validate_document(data)[0], [])
        item["effective_mode"] = "read"
        self.assert_invalid(data, "unchecked")

    def test_ready_state_requires_matching_mode_and_timestamp(self):
        data = configuration()
        item = remote()
        item["requested_mode"] = "write"
        item["access"]["checked_at"] = None
        data["resources"]["remote"] = [item]
        self.assert_invalid(data, "actual access-check")
        self.assert_invalid(data, "must match requested")

    def test_timestamp_requires_timezone(self):
        data = configuration()
        item = remote()
        data["resources"]["remote"] = [item]
        for value in ("2026-11-22", "2026-11-22T12:00:00", "not-a-time"):
            item["access"]["checked_at"] = value
            self.assert_invalid(data, "timestamp with timezone")
        item["access"]["checked_at"] = "2026-11-22T11:00:00Z"
        self.assertEqual(validator.validate_document(data)[0], [])

    def test_trust_requires_actual_write_access_and_grant(self):
        data = configuration()
        item = remote()
        item["write_approval"] = "trusted_for_source"
        data["resources"]["remote"] = [item]
        self.assert_invalid(data, "trust requires")
        item.update(requested_mode="write", effective_mode="write", trust_granted_at="2026-11-22T12:01:00+01:00")
        item["access"]["capability"] = "write"
        errors, warnings = validator.validate_document(data)
        self.assertFalse(errors)
        self.assertTrue(any("does not override" in warning for warning in warnings))
        self.assertEqual(data["version_control"]["operations"]["publish_changes"], "user_only")
        item["write_approval"] = "ask_each_time"
        self.assert_invalid(data, "trust_granted_at null")

    def test_cli_valid_invalid_missing_and_parse_error(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "BOUNDARIES.yaml"
            file.write_text(json.dumps(configuration()), encoding="utf-8")
            command = [sys.executable, str(SKILL / "scripts" / "validate_boundaries.py"), str(file), "--json"]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)["valid"])
            result = subprocess.run(command + ["--require-active"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            file.write_text("secret: [do-not-echo-this-secret", encoding="utf-8")
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertNotIn("do-not-echo-this-secret", result.stdout + result.stderr)
            file.unlink()
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertFalse(json.loads(result.stdout)["valid"])


if __name__ == "__main__":
    unittest.main()
