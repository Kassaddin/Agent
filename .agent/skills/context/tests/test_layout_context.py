"""New layouts retain access, host records, and separate checkpoint ownership."""
from copy import deepcopy
from pathlib import Path
import unittest
from unittest import mock
import test_context as fixtures
import check_context as context


class SeparateContextTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.ContextTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        f = self.fixture
        self.root = f.root
        self.home = self.root / "Agents/.agent"
        self.boundaries = self.home / "config/BOUNDARIES.yaml"
        self.boundaries.parent.mkdir(parents=True)
        f.boundaries.rename(self.boundaries)
        f.boundaries = self.boundaries
        self.data = deepcopy(f.data)
        self.data["schema_version"] = 2
        self.data["views"][0]["path"] = "Agents/.agent/context/project.md"
        f.write(self.data["views"][0]["path"], "# Context\n\nHost orientation.\n")
        self.checkpoint = "Agents/.agent/state/checkpoints/delivery.yaml"
        self.data["topics"][0]["checkpoint_path"] = self.checkpoint
        self.state = {"schema_version": 1, "topic": "delivery", "decision_record": {"resource": "project", "path": "DISCUSSION.md"},
                      "caller": "refine", "objective": "An established request", "scope": ["Agreed scope"], "current_step": "Ready to resume",
                      "handoff": None, "decision_refs": ["D1"], "blockers": [], "artifact_updates": [],
                      "next_action": "Continue the assigned request", "updated_at": "2026-11-23T00:00:00Z"}
        self.write_checkpoint()
        self.index = self.home / "context/index.yaml"
        self.save()

    def save(self):
        self.index.parent.mkdir(parents=True, exist_ok=True)
        self.index.write_text(context.INIT.yaml.safe_dump(self.data, sort_keys=False), encoding="utf-8")

    def write_checkpoint(self):
        self.fixture.write(self.checkpoint, context.INIT.yaml.safe_dump(self.state, sort_keys=False))

    def check(self, **kwargs):
        return context.ContextCheck(self.boundaries).run(**kwargs)

    def test_read_only_load_keeps_host_and_checkpoint_unchanged(self):
        self.fixture.write("README.md", "Keep host README")
        before = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        report = self.check()
        self.assertEqual(report["status"], "complete")
        self.assertEqual(report["checkpoints"][0]["current_step"], "Ready to resume")
        self.assertEqual(before, {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file()})

    def test_incorrect_decision_link_and_missing_checkpoint_are_partial(self):
        self.state["decision_record"]["path"] = "some-other-topic.md"
        self.write_checkpoint()
        self.assertEqual(self.check()["checkpoints"][0]["state"], "needs_review")
        (self.root / self.checkpoint).unlink()
        self.assertEqual(self.check()["checkpoints"][0]["state"], "missing")

    def test_verified_update_needs_evidence(self):
        self.state["artifact_updates"] = [{"artifact": "a document", "owner": "to-document", "state": "verified", "evidence": None}]
        self.write_checkpoint()
        self.assertEqual(self.check()["checkpoints"][0]["state"], "needs_review")

    def test_checkpoint_cannot_live_with_reader_documents(self):
        self.data["topics"][0]["checkpoint_path"] = "docs/checkpoint.yaml"
        self.save()
        with self.assertRaises(ValueError):
            self.check()

    def test_new_namespace_rejects_legacy_index(self):
        self.data["schema_version"] = 1
        self.save()
        with self.assertRaises(ValueError):
            self.check()

    def test_checkpoint_permission_is_checked_before_content_or_existence(self):
        f = self.fixture
        restriction = deepcopy(f.policy["resources"]["local"][0])
        restriction.update(id="checkpoint-denied", path=str(self.home / "state"))
        restriction["permissions"]["read"] = "never"
        f.policy["resources"]["local"].append(restriction)
        f.save_policy()
        original = Path.open
        def guarded(path, *args, **kwargs):
            self.assertNotEqual(path, self.root / self.checkpoint)
            return original(path, *args, **kwargs)
        with mock.patch.object(Path, "open", guarded):
            report = self.check()
        self.assertEqual(report["checkpoints"][0]["state"], "blocked")

    def test_selected_check_budget_includes_checkpoint(self):
        report = context.ContextCheck(self.boundaries, max_sources=3).run()
        self.assertEqual(report["checkpoints"][0]["state"], "not_checked")


if __name__ == "__main__":
    unittest.main()
