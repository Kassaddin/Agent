"""Behavioral checks for scoped, read-only context freshness validation."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
import check_context as context


class ContextTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="context-check-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        template = SKILL.parent / "init/assets/boundaries-template.yaml"
        self.policy = context.INIT.load_yaml(template.read_text(encoding="utf-8"))
        self.policy["state"] = "active"
        self.policy["project"]["name"] = "Context tests"
        self.policy["resources"]["local"][0]["path"] = str(self.root)
        self.boundaries = self.root / "BOUNDARIES.yaml"
        self.save_policy()
        self.write("GLOSSARY.md", "# Terms\n\n## Agreed terms\n\nA defined project term.\n")
        self.write("DISCUSSION.md", "# Decisions\n\n## Current\n\nAn accepted choice.\n")
        self.write("docs/spec.md", "# Specification\n\nThe agreed outcome.\n")
        self.write("CONTEXT.md", "# Context\n\nA short source-linked orientation.\n")
        self.data = {"schema_version": 1, "project": "Context tests", "layout": "one_view", "root_view": "project",
                     "views": [{"id": "project", "path": "CONTEXT.md", "source_ids": ["terms", "decisions", "spec"]}],
                     "sources": [self.source("terms", "GLOSSARY.md", "glossary"), self.source("decisions", "DISCUSSION.md", "decision_record"), self.source("spec", "docs/spec.md", "documentation")],
                     "topics": [{"id": "delivery", "decision_source_id": "decisions", "view_ids": ["project"]}]}
        self.index = self.root / "context/index.yaml"
        self.save_index()

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def source(self, key, relative, role="documentation"):
        return {"id": key, "resource": "project", "path": relative, "role": role, "owner": "refine" if role == "decision_record" else "to-document",
                "section": None, "reviewed_sha256": hashlib.sha256((self.root / relative).read_bytes()).hexdigest(), "reviewed_at": "2026-11-22T12:00:00Z"}

    def save_policy(self):
        self.boundaries.write_text(context.INIT.yaml.safe_dump(self.policy, sort_keys=False), encoding="utf-8")

    def save_index(self):
        self.index.parent.mkdir(parents=True, exist_ok=True)
        self.index.write_text(context.INIT.yaml.safe_dump(self.data, sort_keys=False), encoding="utf-8")

    def run_check(self, **kwargs):
        return context.ContextCheck(self.boundaries).run(**kwargs)

    def states(self, report):
        return {item["id"]: item["state"] for item in report["sources"]}

    def add_area(self):
        self.write("docs/area.md", "# Independent area\n\nArea-specific evidence.\n")
        self.write("context/areas/area.md", "# Area context\n\nA focused view.\n")
        self.data["sources"].append(self.source("area-source", "docs/area.md"))
        self.data["views"].append({"id": "area", "path": "context/areas/area.md", "source_ids": ["area-source"]})
        self.data["layout"] = "by_area"
        self.save_index()

    def test_current_sources_and_load_leave_every_file_unchanged(self):
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.rglob("*") if p.is_file()}
        result = self.run_check()
        self.assertEqual(result["status"], "complete")
        self.assertTrue(result["read_only"])
        self.assertEqual(result["topic_records"], {"delivery": "decisions"})
        self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.rglob("*") if p.is_file()})

    def test_changed_source_requires_review_and_does_not_rewrite_fingerprint(self):
        self.write("docs/spec.md", "# Specification\n\nA changed decision.\n")
        before = self.index.read_bytes()
        result = self.run_check()
        self.assertEqual(result["status"], "partial")
        self.assertEqual(self.states(result)["spec"], "needs_review")
        self.assertEqual(result["affected_view_ids"], ["project"])
        self.assertEqual(before, self.index.read_bytes())

    def test_missing_source_and_missing_index_are_coverage_gaps(self):
        (self.root / "docs/spec.md").unlink()
        self.assertEqual(self.states(self.run_check())["spec"], "missing")
        self.index.unlink()
        result = self.run_check()
        self.assertEqual((result["status"], result["index_state"]), ("partial", "missing"))

    def test_missing_review_is_unverified_even_when_file_is_readable(self):
        self.data["sources"][0].update(reviewed_sha256=None, reviewed_at=None)
        self.save_index()
        self.assertEqual(self.states(self.run_check())["terms"], "needs_review")

    def test_unselected_area_is_not_opened_or_claimed_checked(self):
        self.add_area()
        target = self.root / "docs/area.md"
        original = Path.open
        def guarded(path, *args, **kwargs):
            self.assertNotEqual(path, target)
            return original(path, *args, **kwargs)
        with mock.patch.object(Path, "open", guarded):
            result = self.run_check()
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["not_selected_source_ids"], ["area-source"])

    def test_explicit_area_and_source_selection(self):
        self.add_area()
        result = self.run_check(view_ids=["area"])
        self.assertEqual(result["selected_view_ids"], ["project", "area"])
        self.assertEqual(len(result["sources"]), 4)
        result = self.run_check(source_ids=["area-source"])
        self.assertIn("area-source", result["selected_source_ids"])

    def test_refresh_check_selects_only_affected_views(self):
        self.add_area()
        result = self.run_check(changed_ids=["area-source"])
        self.assertEqual(result["selected_view_ids"], ["area"])
        self.assertEqual(result["selected_source_ids"], ["area-source"])
        self.assertEqual(result["affected_view_ids"], ["area"])

    def test_denied_source_is_not_opened_or_probed(self):
        target = self.root / "docs/spec.md"
        denied = deepcopy(self.policy["resources"]["local"][0])
        denied.update(id="private", path=str(target), kind="file", recursive=False)
        denied["permissions"]["read"] = "never"
        self.policy["resources"]["local"].append(denied)
        self.save_policy()
        original_open, original_exists = Path.open, Path.exists
        def guarded_open(path, *args, **kwargs):
            self.assertNotEqual(path, target)
            return original_open(path, *args, **kwargs)
        def guarded_exists(path):
            self.assertNotEqual(path, target)
            return original_exists(path)
        with mock.patch.object(Path, "open", guarded_open), mock.patch.object(Path, "exists", guarded_exists):
            result = self.run_check()
        self.assertEqual(self.states(result)["spec"], "blocked")

    def test_read_only_project_can_load_context(self):
        self.policy["resources"]["local"][0]["permissions"].update(create="never", modify="never", delete="never")
        self.save_policy()
        self.assertEqual(self.run_check()["status"], "complete")

    def test_investigation_denial_blocks_the_check(self):
        self.policy["conversation"]["investigate_within_scope"] = "never"
        self.save_policy()
        with self.assertRaises(context.AccessError):
            self.run_check()

    def test_unlisted_resolved_target_is_blocked(self):
        target = self.root / "docs/spec.md"
        outside = self.root.parent / "unlisted-context-source.md"
        original = Path.resolve
        def redirected(path, *args, **kwargs):
            return outside if path == target else original(path, *args, **kwargs)
        with mock.patch.object(Path, "resolve", redirected):
            result = self.run_check()
        self.assertEqual(self.states(result)["spec"], "blocked")

    def test_invalid_shapes_duplicates_and_unknown_ids_are_rejected(self):
        for change in (lambda d: d.update(unexpected=True), lambda d: d["sources"].append(deepcopy(d["sources"][0])),
                       lambda d: d["views"][0]["source_ids"].append("unknown"), lambda d: d["topics"][0].update(decision_source_id="spec"),
                       lambda d: d.update(layout="by_area")):
            original = deepcopy(self.data)
            change(self.data)
            self.save_index()
            with self.assertRaises(ValueError):
                self.run_check()
            self.data = original

    def test_duplicate_yaml_keys_are_rejected(self):
        self.index.write_text("schema_version: 1\nschema_version: 1\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.run_check()

    def test_source_path_cannot_escape_or_become_a_uri(self):
        for value in ("../private.md", "/outside.md", "C:/outside.md", "https://example.org/doc", "docs\\spec.md"):
            self.data["sources"][2]["path"] = value
            self.save_index()
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.run_check()

    def test_derived_context_cannot_be_its_own_source(self):
        for value in ("CONTEXT.md", "context/index.yaml"):
            self.data["sources"][2]["path"] = value
            self.save_index()
            with self.assertRaises(ValueError):
                self.run_check()

    def test_source_budget_and_time_budget_are_partial(self):
        result = context.ContextCheck(self.boundaries, max_sources=1).run()
        self.assertEqual(result["status"], "partial")
        self.assertEqual(list(self.states(result).values()).count("not_checked"), 2)
        checker = context.ContextCheck(self.boundaries)
        original = checker.read
        def expire_after_index(path):
            value = original(path)
            if path == checker.index:
                checker.deadline = 0
            return value
        with mock.patch.object(checker, "read", expire_after_index):
            self.assertEqual(checker.run()["status"], "partial")

    def test_unknown_selection_does_not_broaden_scope(self):
        for options in ({"view_ids": ["missing"]}, {"source_ids": ["missing"]}, {"changed_ids": ["missing"]}):
            with self.assertRaises(ValueError):
                self.run_check(**options)

    def test_section_is_checked_even_when_hash_matches(self):
        self.data["sources"][1]["section"] = "current"
        self.save_index()
        self.assertEqual(self.run_check()["status"], "complete")
        self.data["sources"][1]["section"] = "absent"
        self.save_index()
        self.assertEqual(self.states(self.run_check())["decisions"], "needs_review")

    def test_binary_non_utf8_and_byte_limit_are_unsupported(self):
        target = self.root / "docs/spec.md"
        for payload in (b"\0binary", b"\xff\xfe", b"x" * 10000):
            target.write_bytes(payload)
            result = context.ContextCheck(self.boundaries, max_bytes=9000).run()
            self.assertEqual(self.states(result)["spec"], "unsupported")

    def test_review_metadata_must_be_consistent(self):
        for changes in ({"reviewed_sha256": "bad"}, {"reviewed_at": "yesterday"}, {"reviewed_at": None}):
            original = deepcopy(self.data["sources"][0])
            self.data["sources"][0].update(changes)
            self.save_index()
            with self.assertRaises(ValueError):
                self.run_check()
            self.data["sources"][0] = original

    def test_views_cannot_claim_canonical_document_locations(self):
        self.data["views"][0]["path"] = "docs/spec.md"
        self.save_index()
        with self.assertRaises(ValueError):
            self.run_check()

    def test_orientation_budget_is_advisory(self):
        self.write("CONTEXT.md", "word " * 701)
        result = self.run_check()
        self.assertEqual(result["status"], "complete")
        self.assertTrue(result["warnings"])

    def test_index_cannot_use_parent_traversal(self):
        with self.assertRaises(ValueError):
            context.ContextCheck(self.boundaries, self.root / "../outside/index.yaml")

    def test_other_configured_read_only_local_resource_is_supported(self):
        other = tempfile.TemporaryDirectory(prefix="context-reference-")
        self.addCleanup(other.cleanup)
        path = Path(other.name) / "reference.md"
        path.write_text("# Reference\n\nAccepted source.\n", encoding="utf-8")
        source = deepcopy(self.policy["resources"]["local"][0])
        source.update(id="reference", path=other.name)
        source["permissions"].update(create="never", modify="never", delete="never", execute="never")
        self.policy["resources"]["local"].append(source)
        self.save_policy()
        self.data["sources"][2].update(resource="reference", path="reference.md", reviewed_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        self.save_index()
        self.assertEqual(self.run_check()["status"], "complete")

    def test_remote_adapter_limit_is_distinct_from_unavailable_access(self):
        remote = {"id": "remote", "url": "https://example.org/project.git", "kind": "git_repository", "local_ids": ["project"],
                  "requested_mode": "read", "effective_mode": "read", "access": {"capability": "read", "status": "ready", "visibility": "public", "checked_at": "2026-11-22T12:00:00Z", "reason": "Read verified."}, "write_approval": "ask_each_time", "trust_granted_at": None}
        self.policy["resources"]["remote"].append(remote)
        self.save_policy()
        self.data["sources"][2]["resource"] = "remote"
        self.save_index()
        self.assertEqual(self.states(self.run_check())["spec"], "unsupported")
        remote.update(effective_mode="none")
        remote["access"].update(capability="unknown", status="unavailable", reason="No usable access.")
        self.save_policy()
        self.assertEqual(self.states(self.run_check())["spec"], "unavailable")

    def test_denied_index_is_not_opened(self):
        denied = deepcopy(self.policy["resources"]["local"][0])
        denied.update(id="private-index", path=str(self.index), kind="file", recursive=False)
        denied["permissions"]["read"] = "never"
        self.policy["resources"]["local"].append(denied)
        self.save_policy()
        original = Path.open
        def guarded(path, *args, **kwargs):
            self.assertNotEqual(path, self.index)
            return original(path, *args, **kwargs)
        with mock.patch.object(Path, "open", guarded):
            self.assertEqual(self.run_check()["status"], "blocked")

    def test_policy_change_interrupts_the_check(self):
        checker = context.ContextCheck(self.boundaries)
        original = checker.read
        def change_after_index(path):
            value = original(path)
            if path == checker.index:
                self.policy["conversation"]["investigate_within_scope"] = "never"
                self.save_policy()
            return value
        with mock.patch.object(checker, "read", change_after_index), self.assertRaises(context.AccessError):
            checker.run()

    def test_missing_dependencies_have_structured_error_output(self):
        script = self.root / "isolated/context/scripts/check_context.py"
        script.parent.mkdir(parents=True)
        script.write_bytes((SKILL / "scripts/check_context.py").read_bytes())
        result = subprocess.run([sys.executable, "-I", "-B", str(script), "--boundaries", str(self.boundaries)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["status"], "error")

    def test_cli_has_structured_output_and_no_progress(self):
        result = subprocess.run([sys.executable, "-B", str(SKILL / "scripts/check_context.py"), "--boundaries", str(self.boundaries)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "complete")
        result = subprocess.run([sys.executable, "-B", str(SKILL / "scripts/check_context.py"), "--boundaries", str(self.boundaries), "--view", "missing"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["status"], "error")


if __name__ == "__main__":
    unittest.main()
