"""Separate representations retain immutable reports and access preflight."""
from pathlib import Path
import json
import unittest
import test_checks as fixtures
import check_artifacts as checks
import validate_report as reports


class SplitReportTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.SmokesTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        f = self.fixture
        self.root = f.project
        f.boundaries = self.root / "Agents/.agent/config/BOUNDARIES.yaml"
        f.boundaries.parent.mkdir(parents=True)
        f.save_policy()
        self.boundaries = f.boundaries
        self.source = f.write("documentation/guide.md", "# Human guide\n")
        self.report = f.audit(self.source)
        self.access = reports.BoundaryAccess(self.boundaries)
        self.output = self.root / "Agents/.agent/reports/smokes/run"

    def test_default_split_has_identical_data_and_json_navigation(self):
        outputs = checks.save_report(self.report, self.output, self.access)
        markdown = self.root / "Agents/docs/reports/smokes/run/report.md"
        self.assertEqual(Path(outputs["markdown"]), markdown)
        self.assertTrue((self.output / "report.json").is_file())
        self.assertFalse((self.output / "report.md").exists())
        self.assertIn("[report.json]", markdown.read_text(encoding="utf-8"))
        self.assertEqual(json.loads((self.output / "report.json").read_text(encoding="utf-8")), self.report)
        self.assertEqual(self.fixture.audit(markdown)["findings"], [])

    def test_existing_host_document_location_can_be_selected(self):
        readme = self.fixture.write("README.md", "Existing README")
        before = readme.read_bytes()
        human = self.root / "documentation/qa/run"
        checks.save_report(self.report, self.output, self.access, human)
        self.assertTrue((human / "report.md").exists())
        self.assertEqual(readme.read_bytes(), before)

    def test_denied_reader_destination_creates_no_structured_report(self):
        human = self.root / "documentation/blocked/run"
        self.fixture.restrict(human.parent, create="never")
        access = reports.BoundaryAccess(self.boundaries)
        with self.assertRaises(reports.AccessError):
            checks.save_report(self.report, self.output, access, human)
        self.assertFalse(self.output.exists())

    def test_existing_human_run_is_immutable(self):
        human = self.root / "documentation/existing"
        human.mkdir()
        with self.assertRaises(ValueError):
            checks.save_report(self.report, self.output, self.access, human)
        self.assertFalse(self.output.exists())

    def test_structured_reports_stay_agent_side_and_markdown_reader_side(self):
        with self.assertRaises(ValueError):
            checks.save_report(self.report, self.root / "docs/raw/run", self.access)
        with self.assertRaises(ValueError):
            checks.save_report(self.report, self.output, self.access, self.root / "Agents/.agent/private/run")
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
