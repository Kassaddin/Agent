"""Layout selection never migrates a host or chooses between competing policies."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from project_layout import ProjectLayout, discover_boundaries


class LayoutTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="agent-layout-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def file(self, relative, text="existing"):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_discovery_has_no_writes_when_not_adopted(self):
        before = list(self.root.iterdir())
        self.assertEqual(discover_boundaries(self.root), self.root / ".agent/config/BOUNDARIES.yaml")
        self.assertEqual(before, list(self.root.iterdir()))

    def test_multiple_candidates_require_explicit_selection(self):
        first = self.file(".agent/config/BOUNDARIES.yaml", "invalid")
        second = self.file("Agents/.agent/config/BOUNDARIES.yaml", "active")
        self.file("BOUNDARIES.yaml", "legacy")
        with self.assertRaises(ValueError):
            discover_boundaries(self.root)
        self.assertEqual(discover_boundaries(self.root, second), second)
        self.assertEqual(discover_boundaries(self.root, first), first)

    def test_unconfigured_wrapper_is_proposed_without_activation(self):
        (self.root / "Agents/.agent").mkdir(parents=True)
        proposed = discover_boundaries(self.root)
        self.assertEqual(proposed, self.root / "Agents/.agent/config/BOUNDARIES.yaml")
        self.assertFalse(proposed.exists())
        (self.root / ".agent").mkdir()
        with self.assertRaises(ValueError):
            discover_boundaries(self.root)

    def test_external_wrapper_is_noninvasive(self):
        readme = self.file("README.md", "Host README")
        document = self.file("documentation/domain.md", "Host decisions")
        policy = self.file("Agents/.agent/config/BOUNDARIES.yaml")
        before = {p: p.read_bytes() for p in (readme, document, policy)}
        layout = ProjectLayout(self.root, discover_boundaries(self.root))
        self.assertFalse(layout.legacy)
        self.assertEqual(layout.index, self.root / "Agents/.agent/context/index.yaml")
        self.assertEqual(layout.reader_report_directory(layout.reports / "smokes/run"), self.root / "Agents/docs/reports/smokes/run")
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_repo_and_custom_locations(self):
        layout = ProjectLayout(self.root, self.root / ".agent/config/BOUNDARIES.yaml")
        self.assertEqual(layout.home, self.root / ".agent")
        custom = ProjectLayout(self.root, self.root / "policy.yaml", "tooling/agents")
        self.assertFalse(custom.legacy)
        self.assertEqual(custom.index, self.root / "tooling/agents/context/index.yaml")

    def test_custom_area_cannot_escape_or_replace_project_root(self):
        for path in (self.root, self.root.parent, self.root / "../outside"):
            with self.assertRaises(ValueError):
                ProjectLayout(self.root, self.root / "policy.yaml", path)

    def test_legacy_explicit_policy_remains_legacy(self):
        layout = ProjectLayout(self.root, self.root.parent / "explicit-policy.yaml")
        self.assertTrue(layout.legacy)
        self.assertEqual(layout.view, self.root / "CONTEXT.md")

    def test_unreadable_candidate_does_not_fall_through_to_another_policy(self):
        self.file("BOUNDARIES.yaml", "A different policy")
        original = Path.stat
        def guarded(path, *args, **kwargs):
            if path == self.root / ".agent/config/BOUNDARIES.yaml":
                raise PermissionError("Cannot establish this candidate")
            return original(path, *args, **kwargs)
        with mock.patch.object(Path, "stat", guarded):
            with self.assertRaises(PermissionError):
                discover_boundaries(self.root)


if __name__ == "__main__":
    unittest.main()
