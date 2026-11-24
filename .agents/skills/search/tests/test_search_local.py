"""Observable retrieval and boundary tests using isolated temporary sources."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))
import search_local as search


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="search-skill-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.policy = self.root / "BOUNDARIES.yaml"
        template = SKILL.parent / "init" / "assets" / "boundaries-template.yaml"
        self.data = search.BOUNDARIES.load_yaml(template.read_text(encoding="utf-8"))
        self.data["state"] = "active"
        self.data["project"]["name"] = "Search tests"
        self.data["resources"]["local"][0]["path"] = str(self.project)
        self.save()

    def save(self):
        self.policy.write_text(search.BOUNDARIES.yaml.safe_dump(self.data, sort_keys=False), encoding="utf-8")

    def write(self, relative, text="Target evidence\n"):
        path = self.project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def source(self, source_id, path, *, read="act", recursive=True):
        item = deepcopy(self.data["resources"]["local"][0])
        item.update(id=source_id, path=str(path), recursive=recursive)
        item["permissions"]["read"] = read
        self.data["resources"]["local"].append(item)
        self.save()

    def run_search(self, query="target", **kwargs):
        return search.LocalSearch(self.policy, query, **kwargs).run()

    def test_case_insensitive_default_and_line_locators(self):
        path = self.write("Guide.md", "Intro\nTARGET evidence\n")
        result = self.run_search(mode="content")
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["matches"][0]["path"], str(path))
        self.assertEqual(result["matches"][0]["line"], 2)
        self.assertEqual(result["matches"][0]["excerpt"], "TARGET evidence")
        self.assertEqual(self.run_search(mode="content", case_sensitive=True)["status"], "no_matches")

    def test_literal_not_regex_or_shell(self):
        self.write("text.md", "[a-z]+ $(do-not-execute)\n")
        self.assertEqual(len(self.run_search("[a-z]+", mode="content")["matches"]), 1)
        self.assertEqual(len(self.run_search("$(do-not-execute)", mode="content")["matches"]), 1)

    def test_filename_and_directory_path(self):
        self.write("nested/Report.MD", "no content hit")
        result = self.run_search("report.md", mode="filename")
        self.assertEqual(result["matches"][0]["kind"], "filename")
        result = self.run_search("nested", mode="path")
        self.assertTrue(any(Path(item["path"]).name == "nested" and "line" not in item for item in result["matches"]))

    def test_auto_matches_relative_path_without_root_prefix_noise(self):
        self.write("Guide.md", "unrelated")
        result = self.run_search("project", mode="auto")
        self.assertEqual(len(result["matches"]), 1)
        self.assertEqual(result["matches"][0]["path"], str(self.project))

    def test_hidden_sources_and_declared_default_exclusions(self):
        self.write(".agents/note.md")
        self.write("node_modules/ignored.md")
        self.write(".git/ignored.txt")
        result = self.run_search(mode="content")
        self.assertEqual(len(result["matches"]), 1)
        self.assertIn(".agents", result["matches"][0]["path"])
        self.assertEqual(result["coverage"][0]["excluded_default"], 2)
        result = self.run_search(mode="content", include_generated=True, include_git_internals=True)
        self.assertEqual(len(result["matches"]), 3)

    def test_including_git_metadata_cannot_override_inspection_denial(self):
        self.write(".git/note.txt")
        self.data["version_control"]["operations"]["inspect"] = "never"
        self.save()
        result = self.run_search(mode="content", include_git_internals=True)
        self.assertFalse(result["matches"])
        self.assertEqual(result["status"], "partial")

    def test_denied_content_is_never_opened(self):
        forbidden = self.write("private/secret.md")
        self.write("public.md")
        self.source("private", forbidden.parent, read="never")
        original = Path.open
        def guarded(path, *args, **kwargs):
            self.assertNotEqual(path, forbidden, "A prohibited file was opened")
            return original(path, *args, **kwargs)
        with mock.patch.object(Path, "open", guarded):
            result = self.run_search(mode="content")
        self.assertEqual(len(result["matches"]), 1)
        self.assertEqual(result["status"], "partial")
        self.assertTrue(any(item["blocked"] for item in result["coverage"]))

    def test_read_ask_is_not_auto_approved(self):
        self.write("private/note.md")
        self.source("private", self.project / "private", read="ask")
        result = self.run_search(mode="content", sources=["private"])
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["matches"])

    def test_read_only_sources_need_no_write_permission(self):
        self.write("REFERENCE/note.md")
        self.source("reference", self.project / "REFERENCE")
        for operation in ("create", "modify", "delete", "execute"):
            self.data["resources"]["local"][1]["permissions"][operation] = "never"
        self.save()
        result = self.run_search(mode="content", sources=["reference"])
        self.assertEqual(result["status"], "complete")
        self.assertEqual(len(result["matches"]), 1)

    def test_overlapping_roots_are_deduplicated_and_attributed(self):
        self.write("REFERENCE/note.md")
        self.source("reference", self.project / "REFERENCE")
        result = self.run_search(mode="content")
        self.assertEqual(len(result["matches"]), 1)
        self.assertEqual(result["matches"][0]["source_id"], "reference")
        self.assertEqual({item["source_id"]: item["files_searched"] for item in result["coverage"]}, {"project": 1, "reference": 1})

    def test_nonrecursive_selected_scope_does_not_borrow_parent_recursion(self):
        self.write("limited/note.md")
        self.source("limited", self.project / "limited", recursive=False)
        result = self.run_search(mode="content", sources=["limited"])
        self.assertFalse(result["matches"])
        self.assertEqual(result["status"], "no_matches")

    def test_permission_checks_resolved_target_before_content(self):
        alias = self.write("alias.md", "not target")
        outside = self.root / "outside.md"
        outside.write_text("Target outside scope", encoding="utf-8")
        original = Path.resolve
        def resolved(path, *args, **kwargs):
            return outside if path == alias else original(path, *args, **kwargs)
        with mock.patch.object(Path, "resolve", resolved):
            result = self.run_search(mode="content")
        self.assertFalse(result["matches"])
        self.assertEqual(result["status"], "partial")

    def test_real_symlink_escape_when_supported(self):
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "note.md").write_text("Target outside scope", encoding="utf-8")
        try:
            (self.project / "escape").symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("Host does not permit creating test symlinks")
        result = self.run_search(mode="content")
        self.assertFalse(result["matches"])
        self.assertEqual(result["status"], "partial")

    def test_link_does_not_expand_scope_to_an_unselected_allowed_source(self):
        alias = self.write("alias.md")
        vault = self.root / "vault"
        vault.mkdir()
        target = vault / "note.md"
        target.write_text("Target evidence", encoding="utf-8")
        self.source("vault", vault)
        worker = search.LocalSearch(self.policy, "target", sources=["project"])
        original = Path.resolve
        def resolved(path, *args, **kwargs):
            return target if path == alias else original(path, *args, **kwargs)
        with mock.patch.object(Path, "resolve", resolved):
            self.assertFalse(worker._allowed(alias))
            result = worker.run()
        self.assertFalse(result["matches"])
        self.assertEqual(result["status"], "partial")

    def test_linked_match_uses_actual_source_attribution_and_notes(self):
        alias = self.write("alias.md")
        vault = self.root / "vault"
        vault.mkdir()
        target = vault / "note.md"
        target.write_text("Target evidence", encoding="utf-8")
        self.source("vault", vault)
        worker = search.LocalSearch(self.policy, "target", source_notes={"vault": "Not current."})
        original = Path.resolve
        def resolved(path, *args, **kwargs):
            return target if path == alias else original(path, *args, **kwargs)
        with mock.patch.object(Path, "resolve", resolved):
            worker._add(alias, "content", line=1, excerpt="Target evidence")
        self.assertEqual(worker.matches[0]["source_id"], "vault")
        self.assertEqual(worker.matches[0]["source_notes"], ["Not current."])

    def test_result_file_and_time_limits_are_partial(self):
        self.write("one.md")
        self.write("two.md")
        self.assertEqual(self.run_search(mode="content", max_results=1)["stop_reason"], "result_limit")
        self.assertEqual(self.run_search(mode="content", max_files=1)["stop_reason"], "file_limit")
        worker = search.LocalSearch(self.policy, "target", mode="content")
        worker.deadline = 0
        result = worker.run()
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["stop_reason"], "time_limit")

    def test_filename_search_honors_file_budget_before_emitting_hits(self):
        self.write("target-one.md")
        self.write("target-two.md")
        result = self.run_search(mode="filename", max_files=1)
        self.assertEqual(len(result["matches"]), 1)
        self.assertEqual(result["stop_reason"], "file_limit")

    def test_time_limit_must_be_finite(self):
        for timeout in (float("nan"), float("inf"), -1):
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                self.run_search(timeout=timeout)

    def test_binary_large_and_non_utf8_are_coverage_gaps(self):
        self.write("binary.bin", "Target\0binary")
        (self.project / "encoding.bin").write_bytes(b"Target\xff")
        self.write("large.md", "Target" * 20)
        result = self.run_search(mode="content", max_file_bytes=50)
        self.assertEqual(result["status"], "partial")
        self.assertFalse(result["matches"])
        self.assertEqual(result["coverage"][0]["unsupported"], 2)
        self.assertEqual(result["coverage"][0]["limits"], 1)

    def test_excerpts_bounded_and_source_notes_preserved(self):
        self.write("note.md", "Target " + "x" * 1000)
        result = self.run_search(mode="content", source_notes={"project": "User reports this source is not current."})
        match = result["matches"][0]
        self.assertEqual(len(match["excerpt"]), 240)
        self.assertTrue(match["excerpt_truncated"])
        self.assertIn("not current", match["source_notes"][0])

    def test_unknown_sources_and_invalid_boundaries_fail_closed(self):
        with self.assertRaises(ValueError):
            self.run_search(sources=["missing"])
        self.data["state"] = "draft"
        self.save()
        with self.assertRaises(ValueError):
            self.run_search()

    def test_policy_change_interrupts_search(self):
        self.write("note.md")
        worker = search.LocalSearch(self.policy, "target", mode="content")
        self.data["conversation"]["investigate_within_scope"] = "never"
        self.save()
        result = worker.run()
        self.assertFalse(result["matches"])
        self.assertEqual(result["stop_reason"], "boundaries_changed")
        self.assertEqual(result["status"], "partial")

    def test_delegation_standing_approval_does_not_override_never(self):
        self.assertFalse(search.worker_permission(self.data)[0])
        self.data["approvals"]["allow_read_only_search_worker"] = True
        self.assertTrue(search.worker_permission(self.data)[0])
        self.data["conversation"]["delegate_work"] = "never"
        self.assertFalse(search.worker_permission(self.data)[0])

    def test_investigation_never_blocks_even_with_standing_approval(self):
        self.write("note.md")
        self.data["approvals"]["allow_read_only_search_worker"] = True
        self.data["conversation"]["investigate_within_scope"] = "never"
        self.save()
        result = self.run_search()
        self.assertEqual(result["status"], "blocked")
        self.assertFalse(result["matches"])

    def test_missing_local_source_is_not_no_matches(self):
        shutil.rmtree(self.project)
        result = self.run_search()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["coverage"][0]["status"], "unavailable")

    def test_remote_only_needs_adapter_and_never_becomes_no_matches(self):
        self.data["resources"]["remote"] = [{
            "id": "origin", "url": "https://example.org/repo.git", "kind": "git_repository", "local_ids": ["project"],
            "requested_mode": "read", "effective_mode": "read", "write_approval": "ask_each_time", "trust_granted_at": None,
            "access": {"capability": "read", "status": "ready", "visibility": "public", "checked_at": "2026-11-22T12:00:00Z", "reason": None},
        }]
        self.save()
        result = self.run_search(sources=["origin"])
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["coverage"][1]["status"], "unsupported")
        self.data["resources"]["remote"][0]["access"].update(status="unavailable", capability="none", reason="Access declined")
        self.data["resources"]["remote"][0]["effective_mode"] = "none"
        self.save()
        self.assertEqual(self.run_search(sources=["origin"])["status"], "blocked")

    @unittest.skipUnless(shutil.which("rg"), "Regex engine rg is not available")
    def test_regex_modes_case_and_line_numbers(self):
        self.write("Report7.md", "heading\vstill line one\nItem42 evidence\n")
        result = self.run_search(r"item\d+", mode="content", regex=True)
        self.assertEqual(result["matches"][0]["line"], 2)
        self.assertEqual(result["matches"][0]["excerpt"], "Item42 evidence")
        self.assertEqual(self.run_search(r"item\d+", mode="content", regex=True, case_sensitive=True)["status"], "no_matches")
        self.assertEqual(len(self.run_search(r"report\d+\.md$", mode="filename", regex=True)["matches"]), 1)
        self.assertEqual(self.run_search("--pre=do-not-execute", mode="content", regex=True)["status"], "no_matches")
        with self.assertRaises(ValueError):
            self.run_search("[invalid", regex=True)

    def test_plan_does_not_open_source_contents(self):
        self.write("note.md")
        original = Path.open
        def guarded(path, *args, **kwargs):
            self.assertNotEqual(path, self.project / "note.md")
            return original(path, *args, **kwargs)
        with mock.patch.object(Path, "open", guarded):
            result = search.LocalSearch(self.policy, "target").plan()
        self.assertFalse(result["worker_allowed"])

    def test_cli_outputs_json_and_no_progress(self):
        self.write("note.md")
        result = subprocess.run([sys.executable, "-B", str(SKILL / "scripts" / "search_local.py"),
                                 "--boundaries", str(self.policy), "--query", "target", "--mode", "content"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "complete")
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
