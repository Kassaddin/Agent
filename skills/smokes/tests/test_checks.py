"""Integration tests for immutable audits, actionable reports, and Fix handoff."""

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
import check_artifacts as checks
import validate_report as reports


class SmokesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="smokes-fix-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.boundaries = self.root / "BOUNDARIES.yaml"
        template = SKILL.parent / "init" / "assets" / "boundaries-template.yaml"
        self.policy = reports.INIT.load_yaml(template.read_text(encoding="utf-8"))
        self.policy["state"] = "active"
        self.policy["project"]["name"] = "Smokes tests"
        self.policy["resources"]["local"][0]["path"] = str(self.project)
        # The configuration itself is explicitly available for the checker.
        configuration = deepcopy(self.policy["resources"]["local"][0])
        configuration.update(id="configuration", path=str(self.boundaries), kind="file", recursive=False)
        self.policy["resources"]["local"].append(configuration)
        self.save_policy()

    def save_policy(self):
        self.boundaries.write_text(reports.INIT.yaml.safe_dump(self.policy, sort_keys=False), encoding="utf-8")

    def write(self, path, text):
        file = self.project / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text, encoding="utf-8")
        return file

    def audit(self, paths, **kwargs):
        if isinstance(paths, Path):
            paths = [paths]
        return checks.Auditor(self.boundaries, paths, **kwargs).run()

    def codes(self, report):
        return [item["check_id"] for item in report["findings"]]

    def restrict(self, path, **permissions):
        source = deepcopy(self.policy["resources"]["local"][0])
        source.update(id="restricted", path=str(path))
        source["permissions"].update(permissions)
        self.policy["resources"]["local"].append(source)
        self.save_policy()

    def packet(self, paths, findings=None, status="complete"):
        file = self.project / "review-packet.json"
        file.write_text(json.dumps({"status": status, "reason": "Reviewed the stated text and intent.", "paths": [str(path) for path in paths], "findings": findings or []}), encoding="utf-8")
        return file

    def semantic_finding(self, file):
        return {"check_id": "contradictory_action", "category": "contradiction", "certainty": "confirmed", "severity": "high", "priority": "P1", "title": "Rules require incompatible behavior",
                "locations": [{"path": str(file), "line": 1, "section": None}, {"path": str(file), "line": 2, "section": None}],
                "evidence": [{"path": str(file), "line": 1, "kind": "source_excerpt", "text": "Always ask."}, {"path": str(file), "line": 2, "kind": "source_excerpt", "text": "Never ask."}],
                "impact": "Both rules apply to the same action and cannot both be followed.", "proposed_fix": "Ask which behavior is intended for this action.", "acceptance_check": "The user resolves precedence or narrows the overlapping scopes.", "depends_on": [],
                "remediation": {"mode": "decision_required", "reason": "The intended behavior requires a user decision."}}

    def test_missing_artifact_is_a_finding_not_an_access_failure(self):
        report = self.audit(self.project / "missing.md")
        self.assertEqual(self.codes(report), ["file_missing"])
        self.assertEqual(report["scope"]["snapshots"][0]["state"], "missing")
        self.assertEqual(report["findings"][0]["remediation"]["mode"], "decision_required")

    def test_broken_local_link_and_snapshot(self):
        file = self.write("overview.md", "# Overview\n[Guide](missing.md)\n")
        report = self.audit(file)
        self.assertEqual(self.codes(report), ["link_missing"])
        self.assertEqual(report["findings"][0]["locations"][0]["line"], 2)
        self.assertEqual(report["scope"]["snapshots"][0]["sha256"], hashlib.sha256(file.read_bytes()).hexdigest())
        self.assertEqual(report["summary"]["confirmed"], 1)
        self.assertEqual(reports.validate_report(report), [])

    def test_code_examples_inline_code_and_comments_are_not_dependencies(self):
        file = self.write("examples.md", "```md\n[Fake](missing.md)\n```\n`[Fake](missing.md)`\n<!-- [Fake](missing.md) -->\n")
        self.assertFalse(self.audit(file)["findings"])

    def test_angles_spaces_parentheses_reference_links_and_anchors(self):
        self.write("guide (one).md", "# Use `Search`\n# Use `Search`\n<a id=\"custom\"></a>\n")
        file = self.write("index.md", "[One](<guide (one).md#use-search>)\n[Two](guide%20(one).md#use-search-1)\n[Named][guide]\n[guide]: <guide (one).md#custom>\n")
        self.assertFalse(self.audit(file)["findings"])

    def test_missing_anchor_is_reproducible(self):
        self.write("guide.md", "# Existing\n")
        file = self.write("index.md", "[Missing](guide.md#absent)\n")
        self.assertEqual(self.codes(self.audit(file)), ["anchor_missing"])

    def test_undefined_reference_requires_review(self):
        file = self.write("index.md", "[Guide][undefined]\n")
        report = self.audit(file)
        self.assertEqual(report["findings"][0]["certainty"], "needs_review")
        self.assertEqual(report["findings"][0]["remediation"]["mode"], "decision_required")

    def test_remote_url_is_unchecked_not_broken(self):
        file = self.write("index.md", "[External](https://example.org/no-network)\n")
        report = self.audit(file)
        self.assertFalse(report["findings"])
        self.assertEqual(report["summary"]["audit_status"], "partial")
        self.assertTrue(any(item["check_id"] == "cross_link.remote" and item["status"] == "skipped" for item in report["coverage"]))

    def test_malformed_uri_is_a_finding_not_a_checker_crash(self):
        file = self.write("index.md", "[Bad](http://[invalid)\n")
        self.assertEqual(self.codes(self.audit(file)), ["link_uri_invalid"])

    def test_out_of_boundary_target_is_not_probed(self):
        outside = self.root / "private.md"
        outside.write_text("Private", encoding="utf-8")
        file = self.write("index.md", "[Private](../private.md)\n")
        original = Path.exists
        def guarded(path):
            self.assertNotEqual(path, outside, "Unauthorized target existence was probed")
            return original(path)
        with mock.patch.object(Path, "exists", guarded):
            report = self.audit(file)
        self.assertFalse(report["findings"])
        self.assertTrue(any(item["status"] == "blocked" for item in report["coverage"]))

    def test_wikilinks_resolve_within_scope_and_ambiguity_is_not_auto_fixed(self):
        first = self.write("a/Note.md", "# Section\n")
        second = self.write("b/Note.md", "# Other\n")
        index = self.write("index.md", "[[Note#Section|Label]]\n")
        report = self.audit([first, index])
        self.assertFalse(report["findings"])
        report = self.audit([first, second, index])
        self.assertIn("wiki_ambiguous", self.codes(report))
        self.assertEqual(next(item for item in report["findings"] if item["check_id"] == "wiki_ambiguous")["certainty"], "needs_review")

    def test_exact_duplicates_group_once_and_intentional_copies_are_excluded(self):
        first = self.write("one.md", "Identical meaningful content\n")
        second = self.write("two.md", "Identical meaningful content\n")
        report = self.audit([first, second])
        self.assertEqual(self.codes(report), ["duplicate_files"])
        self.assertEqual(len(report["findings"][0]["locations"]), 2)
        self.assertEqual(report["summary"]["needs_review"], 1)
        self.assertFalse(self.audit([first, second], intentional_duplicates=[first, second])["findings"])

    def test_generic_yaml_merges_are_valid_but_explicit_duplicates_are_not(self):
        good = self.write("good.yaml", "base: &base\n  read: act\ncopy:\n  <<: *base\n  read: never\n")
        bad = self.write("bad.yaml", "read: act\nread: never\n")
        self.assertFalse(self.audit(good)["findings"])
        report = self.audit(bad)
        self.assertIn("structure_invalid", self.codes(report))
        self.assertEqual(report["findings"][0]["remediation"]["mode"], "decision_required")

    def test_custom_yaml_tags_are_unsupported_not_a_universal_syntax_defect(self):
        file = self.write("custom.yaml", "value: !include other.yaml\n")
        report = self.audit(file)
        self.assertFalse(report["findings"])
        self.assertTrue(any(item["status"] == "unsupported" for item in report["coverage"]))
        complex_key = self.write("complex.yaml", "? [one, two]\n: value\n")
        complex_report = self.audit(complex_key)
        self.assertFalse(complex_report["findings"])
        self.assertTrue(any(item["status"] == "unsupported" for item in complex_report["coverage"]))

    def test_json_invalid_and_duplicate_keys(self):
        bad = self.write("bad.json", '{"read": true,}')
        duplicate = self.write("duplicate.json", '{"read": true, "read": false}')
        self.assertIn("structure_invalid", self.codes(self.audit(bad)))
        with self.assertRaises(json.JSONDecodeError) as parser_error:
            json.loads(bad.read_text(encoding="utf-8"))
        self.assertIn(parser_error.exception.msg, self.audit(bad)["findings"][0]["impact"])
        self.assertEqual(self.audit(duplicate)["findings"][0]["remediation"]["mode"], "decision_required")

    def test_skill_name_mismatch_does_not_require_optional_metadata(self):
        file = self.write("sample/SKILL.md", "---\nname: wrong\ndescription: Finished description\n---\n\n# Sample\n")
        self.assertEqual(self.codes(self.audit(file)), ["skill_name"])
        file.write_text(file.read_text(encoding="utf-8").replace("name: wrong", "name: sample"), encoding="utf-8")
        self.assertFalse(self.audit(file)["findings"])

    def test_unfinished_skill_description_but_not_template_content(self):
        file = self.write("sample/SKILL.md", '---\nname: sample\ndescription: "[TODO: complete this]"\n---\n')
        template = self.write("assets/template.md", "# {{topic}}\n")
        self.assertIn("skill_placeholder", self.codes(self.audit(file)))
        self.assertFalse(self.audit(template)["findings"])

    def test_skill_property_locators_follow_the_actual_frontmatter_order(self):
        file = self.write("sample/SKILL.md", "---\ndescription: Finished\nname: wrong\n---\n")
        report = self.audit(file)
        self.assertEqual(report["findings"][0]["locations"][0]["line"], 3)

    def test_invalid_skill_name_is_not_double_counted(self):
        file = self.write("sample/SKILL.md", '---\nname: ""\ndescription: Finished\n---\n')
        self.assertEqual(self.codes(self.audit(file)), ["structure_invalid"])

    def test_invocation_policy_boolean_is_checked(self):
        file = self.write("sample/agents/openai.yaml", 'interface:\n  display_name: Sample\npolicy:\n  allow_implicit_invocation: "false"\n')
        report = self.audit(file)
        self.assertIn("boolean allow_implicit_invocation", report["findings"][0]["impact"])

    def test_no_semantic_pass_is_claimed_without_review(self):
        file = self.write("rules.md", "Always ask.\nNever ask.\n")
        report = self.audit(file)
        self.assertFalse(report["findings"])
        self.assertEqual(report["summary"]["audit_status"], "partial")
        packet = self.packet([file], [self.semantic_finding(file)])
        report = self.audit(file, semantic_review=packet)
        self.assertEqual(report["summary"]["audit_status"], "complete")
        self.assertEqual(report["summary"]["by_severity"]["high"], 1)
        self.assertEqual(report["summary"]["by_priority"]["P1"], 1)
        self.assertEqual(reports.validate_report(report), [])

    def test_semantic_packet_rejects_invented_or_uncaptured_evidence(self):
        file = self.write("rules.md", "Always ask.\nNever ask.\n")
        finding = self.semantic_finding(file)
        finding["evidence"][0]["text"] = "Invented quote"
        packet = self.packet([file], [finding])
        with self.assertRaises(ValueError):
            self.audit(file, semantic_review=packet)

    def test_malformed_semantic_packet_fails_cleanly(self):
        file = self.write("rules.md", "Content")
        packet = self.project / "review-packet.json"
        packet.write_text(json.dumps({"status": [], "reason": "", "paths": [], "findings": []}), encoding="utf-8")
        with self.assertRaises(ValueError):
            self.audit(file, semantic_review=packet)
        packet = self.packet([self.project / "not-captured.md"])
        with self.assertRaises(ValueError):
            self.audit(file, semantic_review=packet)

    def test_partial_semantic_scope_stays_partial(self):
        first = self.write("one.md", "First text")
        second = self.write("two.md", "Second text")
        report = self.audit([first, second], semantic_review=self.packet([first]))
        self.assertEqual(report["summary"]["audit_status"], "partial")

    def test_readonly_target_has_user_action_remediation(self):
        file = self.write("REFERENCE/index.md", "[Bad](missing.md)")
        self.restrict(file.parent, modify="never", create="never", delete="never", execute="never")
        report = self.audit(file)
        self.assertEqual(report["findings"][0]["remediation"]["mode"], "user_action")

    def test_blocked_scope_is_reported_without_opening_content(self):
        file = self.write("private/note.md", "Not allowed")
        self.restrict(file.parent, read="never")
        original = Path.open
        def guarded(path, *args, **kwargs):
            self.assertNotEqual(path, file)
            return original(path, *args, **kwargs)
        with mock.patch.object(Path, "open", guarded):
            report = self.audit(file)
        self.assertEqual(report["summary"]["audit_status"], "blocked")
        self.assertFalse(report["findings"])

    def test_reports_are_only_writes_and_cannot_overwrite_existing_runs(self):
        file = self.write("index.md", "[Bad](missing.md)")
        before = file.read_bytes()
        auditor = checks.Auditor(self.boundaries, [file])
        report = auditor.run()
        output = self.project / "reports" / report["report_id"]
        checks.save_report(report, output, auditor.access)
        self.assertEqual(file.read_bytes(), before)
        self.assertEqual({path.name for path in output.iterdir()}, {"report.json", "report.md"})
        parsed = reports.strict_json((output / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(reports.validate_report(parsed), [])
        self.assertIn("1 unique findings", (output / "report.md").read_text(encoding="utf-8"))
        self.assertIn("SMK-001", (output / "report.md").read_text(encoding="utf-8"))
        with self.assertRaises(ValueError):
            checks.save_report(report, output, auditor.access)
        report["summary"]["total"] = 99
        with self.assertRaises(ValueError):
            checks.save_report(report, self.project / "invalid-output", auditor.access)
        self.assertFalse((self.project / "invalid-output").exists())

    def test_readonly_report_destination_is_denied(self):
        file = self.write("index.md", "Clean")
        folder = self.project / "readonly"
        folder.mkdir()
        self.restrict(folder, create="never", modify="never")
        auditor = checks.Auditor(self.boundaries, [file])
        report = auditor.run()
        with self.assertRaises(reports.AccessError):
            checks.save_report(report, folder / "run", auditor.access)
        self.assertFalse((folder / "run").exists())

    def test_report_creation_checks_missing_intermediate_directories(self):
        file = self.write("index.md", "Clean")
        forbidden_parent = self.project / "reports"
        self.restrict(forbidden_parent, create="never")
        self.policy["resources"]["local"][-1]["recursive"] = False
        self.save_policy()
        auditor = checks.Auditor(self.boundaries, [file])
        report = auditor.run()
        with self.assertRaises(reports.AccessError):
            checks.save_report(report, forbidden_parent / "run", auditor.access)
        self.assertFalse(forbidden_parent.exists())

    def test_fix_current_state_respects_new_read_restrictions(self):
        file = self.write("private/index.md", "[Bad](missing.md)")
        report = self.audit(file)
        self.restrict(file.parent, read="never", modify="never")
        access = reports.BoundaryAccess(self.boundaries)
        original = Path.open
        def guarded(path, *args, **kwargs):
            self.assertNotEqual(path, file)
            return original(path, *args, **kwargs)
        with mock.patch.object(Path, "open", guarded):
            state = reports.current_state(report, access)[0]
        self.assertEqual(state["state"], "blocked")
        self.assertFalse(state["modify_authorized"])

    def test_fix_handoff_detects_drift_then_verifies_a_real_link_correction(self):
        file = self.write("index.md", "[Guide](wrong.md)\n")
        target = self.write("guide.md", "# Guide\n")
        report = self.audit(file)
        original = deepcopy(report)
        access = reports.BoundaryAccess(self.boundaries)
        self.assertEqual(reports.current_state(report, access)[0]["state"], "unchanged")
        # Simulate the explicitly invoked Fix applying a minimal patch to current text.
        file.write_text("[Guide](guide.md)\n", encoding="utf-8")
        self.assertEqual(reports.current_state(report, access)[0]["state"], "changed")
        follow_up = self.audit(file)
        self.assertNotIn("link_missing", self.codes(follow_up))
        self.assertEqual(report, original)

    def test_report_counts_fingerprints_dependencies_and_lines_are_validated(self):
        file = self.write("index.md", "[Bad](missing.md)")
        report = self.audit(file)
        report["summary"]["total"] = 99
        self.assertTrue(reports.validate_report(report))
        reports.finalize(report)
        report["findings"][0]["depends_on"] = ["SMK-001"]
        self.assertTrue(any("cycle" in error for error in reports.validate_report(report)))
        report["findings"][0]["depends_on"] = ["SMK-999"]
        self.assertTrue(any("unknown dependency" in error for error in reports.validate_report(report)))
        report["findings"][0]["depends_on"] = []
        report["findings"][0]["locations"][0]["line"] = 0
        self.assertTrue(any("positive" in error for error in reports.validate_report(report)))

    def test_limits_and_unsupported_formats_do_not_become_passes(self):
        file = self.write("large.md", "x" * 100)
        report = self.audit(file, max_bytes=10)
        self.assertEqual(report["summary"]["audit_status"], "partial")
        source = self.write("module.py", "print('no execution')")
        self.assertEqual(self.audit(source)["summary"]["audit_status"], "partial")
        links = self.write("links.md", "[One](one.md)\n[Two](two.md)\n")
        limited = self.audit(links, max_findings=1)
        self.assertEqual(limited["summary"]["total"], 1)
        self.assertEqual(limited["summary"]["audit_status"], "partial")

    def test_boundary_change_stops_audit(self):
        file = self.write("index.md", "Clean")
        auditor = checks.Auditor(self.boundaries, [file])
        self.policy["conversation"]["investigate_within_scope"] = "never"
        self.save_policy()
        with self.assertRaises(reports.AccessError):
            auditor.run()

    def test_cli_report_and_validator_outputs(self):
        file = self.write("index.md", "[Bad](missing.md)")
        output = self.project / "reports" / "cli-run"
        result = subprocess.run([sys.executable, "-B", str(SKILL / "scripts" / "check_artifacts.py"), "--boundaries", str(self.boundaries), "--path", str(file), "--report-dir", str(output), "--summary"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(json.loads(result.stdout)["summary"]["total"], 1)
        result = subprocess.run([sys.executable, "-B", str(SKILL / "scripts" / "validate_report.py"), str(output / "report.json"), "--boundaries", str(self.boundaries), "--check-current"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertTrue(json.loads(result.stdout)["valid"])

    def test_regression_escaped_link_and_image_delimiters_are_literal(self):
        for text in (r"\[Example\](missing.md)", r"!\[Image\](missing.png)",
                     r"[Unclosed\](missing.md)", r"\[[Note]]"):
            with self.subTest(text=text):
                self.assertEqual(list(checks.markdown_links(text)), [])

    def test_regression_link_and_wiki_backslash_parity(self):
        for count in range(1, 5):
            for text, target, kind in (("[Guide](guide.md)", "guide.md", "markdown"),
                                       ("[[Note]]", "Note", "wiki")):
                with self.subTest(count=count, kind=kind):
                    expected = [] if count % 2 else [(1, target, kind)]
                    self.assertEqual(list(checks.markdown_links("\\" * count + text)), expected)
        self.assertEqual(list(checks.markdown_links(r"\![Guide](guide.md)")), [(1, "guide.md", "markdown")])

    def test_regression_real_links_can_have_escaped_label_brackets(self):
        for text in (r"[Use \] carefully](guide.md)", r"[\[Guide\]](guide.md)"):
            with self.subTest(text=text):
                self.assertEqual(list(checks.markdown_links(text)), [(1, "guide.md", "markdown")])

    def test_regression_reference_delimiters_and_labels_respect_escapes(self):
        text = r"\[hidden]: missing.md" + "\n[hidden]\n"
        self.assertEqual(list(checks.markdown_links(text)), [])
        text = "[label]: guide.md\n" + r"\[label]" + "\n"
        self.assertEqual(list(checks.markdown_links(text)), [])
        text = r"[label\]]: guide.md" + "\n" + r"[Text][label\]]" + "\n"
        self.assertEqual(list(checks.markdown_links(text)), [(2, "guide.md", "markdown")])
        text = r"[label\!]: guide.md" + "\n[Text][label!]\n"
        self.assertEqual(list(checks.markdown_links(text)), [(2, "guide.md", "markdown")])

    def test_regression_escaped_examples_do_not_hide_a_real_missing_link(self):
        text = r"\[Example\](fake.md)" + "\n" + r"!\[Image\](fake.png)" + "\n[Real](missing.md)\n"
        file = self.write("examples.md", text)
        report = self.audit(file)
        self.assertEqual(self.codes(report), ["link_missing"])
        self.assertEqual(report["findings"][0]["locations"][0]["line"], 3)

    def test_regression_rendered_report_evidence_is_not_a_live_link(self):
        source = self.write("index.md", "[Guide](missing.md)\n")
        rendered = reports.render_markdown(self.audit(source))
        report_file = self.write("report.md", rendered)
        self.assertFalse(self.audit(report_file)["findings"])

    def test_regression_apostrophe_targets_and_quoted_titles(self):
        cases = [
            ("[Guide](guides/O'Reilly.md)", "guides/O'Reilly.md"),
            ("[Guide](<guides/O'Reilly notes.md>)", "guides/O'Reilly notes.md"),
            ('[Guide](guide.md "Title with an apostrophe\'s note")', "guide.md"),
            ("[Guide](guide.md 'Quoted title')", "guide.md"),
            (r"[Guide](guide\(one\).md)", "guide(one).md"),
            ("[Guide](<guide(one.md>)", "guide(one.md"),
        ]
        for text, target in cases:
            with self.subTest(text=text):
                self.assertEqual(list(checks.markdown_links(text)), [(1, target, "markdown")])

    def test_regression_missing_apostrophe_target_is_reported(self):
        file = self.write("index.md", "[Guide](O'Reilly.md)\n")
        self.assertEqual(self.codes(self.audit(file)), ["link_missing"])
        self.write("O'Reilly.md", "# Guide\n")
        self.assertFalse(self.audit(file)["findings"])

    def test_regression_inline_code_cannot_define_html_anchor(self):
        text = ('Example: `<a id="ghost"></a>`\n# Use `Search`\n<a id="real"></a>\n'
                '<!-- <a id="comment"></a> -->\n```html\n<a id="fenced"></a>\n```\n')
        anchors, _ = checks.heading_anchors(text)
        self.assertNotIn("ghost", anchors)
        self.assertNotIn("comment", anchors)
        self.assertNotIn("fenced", anchors)
        self.assertIn("use-search", anchors)
        self.assertIn("real", anchors)

    def test_regression_link_to_inline_example_anchor_is_missing(self):
        self.write("guide.md", 'Example: `<a id="ghost"></a>`\n')
        file = self.write("index.md", "[Ghost](guide.md#ghost)\n")
        self.assertEqual(self.codes(self.audit(file)), ["anchor_missing"])

    def test_regression_fenced_comment_example_does_not_hide_links(self):
        file = self.write("index.md", "```html\n<!--\n```\n[Guide](missing.md)\n<!-- end -->\n")
        report = self.audit(file)
        self.assertEqual(self.codes(report), ["link_missing"])
        self.assertEqual(report["findings"][0]["locations"][0]["line"], 4)

    def test_regression_inline_comment_example_and_real_comments(self):
        text = "Literal `<!--`\n[Guide](missing.md)\n<!-- [Hidden](hidden.md) -->\n"
        self.assertEqual(list(checks.markdown_links(text)), [(2, "missing.md", "markdown")])
        text = "<!--\n```html\n[Hidden](hidden.md)\n-->\n[Guide](missing.md)\n"
        self.assertEqual(list(checks.markdown_links(text)), [(5, "missing.md", "markdown")])

    def test_regression_comment_text_in_fence_info_does_not_escape(self):
        text = "```html <!--\nexample\n```\n[Guide](missing.md)\n<!-- actual comment -->\n"
        self.assertEqual(list(checks.markdown_links(text)), [(4, "missing.md", "markdown")])

    def test_regression_frontmatter_parser_uses_original_file_lines(self):
        file = self.write("broken/SKILL.md", "---\nname: broken\n description: bad\n---\n")
        finding = self.audit(file)["findings"][0]
        self.assertEqual(finding["check_id"], "structure_invalid")
        self.assertEqual(finding["locations"][0]["line"], 3)
        yaml_file = self.write("broken.yaml", "name: broken\n description: bad\n")
        self.assertEqual(self.audit(yaml_file)["findings"][0]["locations"][0]["line"], 2)
        json_file = self.write("broken.json", '{\n  "name": invalid\n}')
        self.assertEqual(self.audit(json_file)["findings"][0]["locations"][0]["line"], 2)

    def test_regression_unhashed_snapshot_is_unverified(self):
        file = self.write("large.md", "Meaningful unchanged content" * 10)
        report = self.audit(file, max_bytes=10)
        self.assertIsNone(report["scope"]["snapshots"][0]["sha256"])
        before = file.read_bytes()
        state = reports.current_state(report, reports.BoundaryAccess(self.boundaries))[0]
        self.assertEqual(state["state"], "unverified")
        self.assertEqual(file.read_bytes(), before)

    def test_regression_missing_snapshot_can_detect_creation(self):
        path = self.project / "missing.md"
        report = self.audit(path)
        access = reports.BoundaryAccess(self.boundaries)
        self.assertEqual(reports.current_state(report, access)[0]["state"], "unchanged")
        path.write_text("New content", encoding="utf-8")
        self.assertEqual(reports.current_state(report, access)[0]["state"], "changed")
        path.unlink()
        self.assertEqual(reports.current_state(report, access)[0]["state"], "unchanged")

    def test_regression_previously_blocked_snapshot_is_unverified_after_access(self):
        file = self.write("private/file.md", "Unchanged content")
        self.restrict(file.parent, read="never")
        report = self.audit(file)
        self.assertEqual(report["scope"]["snapshots"][0]["state"], "blocked")
        self.policy["resources"]["local"][-1]["permissions"]["read"] = "act"
        self.save_policy()
        state = reports.current_state(report, reports.BoundaryAccess(self.boundaries))[0]
        self.assertEqual(state["state"], "unverified")

    def test_regression_code_spans_require_equal_backtick_delimiters(self):
        text = 'Example: ``<a id="ghost"></a>``\n<a id="real"></a>\n'
        anchors, _ = checks.heading_anchors(text)
        self.assertNotIn("ghost", anchors)
        self.assertIn("real", anchors)
        self.assertEqual(checks.visible_markdown("``unclosed ` marker"), ["``unclosed ` marker"])


if __name__ == "__main__":
    unittest.main()
