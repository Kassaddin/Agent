"""First-installation behavior using local published-package fixtures only."""
from copy import deepcopy
import io
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / 'scripts'))
import setup_kit as setup
from release_format import make_manifest, json_bytes, unpack, sha, MANIFEST, ReleaseError, strict_json


def files():
    payload = {f'.agent/skills/{name}/SKILL.md': f'---\nname: {name}\ndescription: Fixture skill.\n---\n\n# Fixture\n'.encode() for name in setup.REQUIRED_SKILLS}
    payload.update({'README.md': b'# Kit\n', 'docs/guide.md': b'# Guide\n', '.agent/instructions.md': b'# Instructions\n', '.gitignore': b'__pycache__/\n'})
    return payload


class Source:
    repository = setup.REPOSITORY

    def __init__(self, payload=None, version='v1.2.0'):
        self.payload = files() if payload is None else payload
        self.version = version
        self.calls = []

    def select(self, version=None):
        self.calls.append(version)
        return {'id': 1, 'tag_name': version or self.version}

    def package(self, release):
        version = release['tag_name']
        raw = io.BytesIO()
        manifest = make_manifest(self.payload, version)
        with zipfile.ZipFile(raw, 'w') as archive:
            for name, content in {**self.payload, MANIFEST: json_bytes(manifest)}.items():
                archive.writestr(zipfile.ZipInfo('Agents/' + name, date_time=(1980, 1, 1, 0, 0, 0)), content)
        raw = raw.getvalue()
        bundle = unpack(raw, f'{sha(raw)}  agent-skills.zip\n'.encode(), version)
        bundle['identity'] = {'repository': self.repository, 'version': version, 'release_id': 1, 'asset_id': 2, 'archive_sha256': sha(raw)}
        return bundle


class SetupTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='setup-fixture-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = Source()
        self.boundaries = self.root / '.agent/config/BOUNDARIES.yaml'

    def installer(self, **kwargs):
        return setup.Installer(self.root, source=self.source, bootstrap_approved=True, **kwargs)

    def execute(self, installer=None, **kwargs):
        installer = installer or self.installer()
        plan = installer.plan()
        return installer.apply(plan, expected_sha=plan['archive_sha256'], notified=True, **kwargs)

    def policy(self, **permissions):
        policy = setup.shared.INIT.load_yaml((SKILL.parent / 'init/assets/boundaries-template.yaml').read_text(encoding='utf-8'))
        policy['state'] = 'active'
        policy['project']['name'] = 'Setup fixture'
        policy['resources']['local'][0]['path'] = str(self.root)
        policy['resources']['local'][0]['permissions'].update(permissions)
        policy['resources']['remote'] = [{'id': 'kit', 'url': 'https://github.com/' + setup.REPOSITORY + '.git', 'kind': 'git_repository', 'local_ids': ['project'],
            'requested_mode': 'read', 'effective_mode': 'read', 'access': {'capability': 'read', 'status': 'ready', 'visibility': 'public', 'checked_at': '2026-11-23T00:00:00Z', 'reason': None},
            'write_approval': 'ask_each_time', 'trust_granted_at': None}]
        self.boundaries.parent.mkdir(parents=True, exist_ok=True)
        self.boundaries.write_text(setup.shared.INIT.yaml.safe_dump(policy, sort_keys=False), encoding='utf-8')
        return policy

    def test_no_policy_requires_actual_bootstrap_grant(self):
        with self.assertRaises(setup.shared.Blocked):
            setup.Installer(self.root, source=self.source)
        self.assertFalse((self.root / 'Agents').exists())

    def test_preview_is_read_only_and_has_init_continuation(self):
        plan = self.installer().plan()
        self.assertEqual(plan['status'], 'ready')
        self.assertEqual(plan['continuation']['action'], 'init_required')
        self.assertEqual(list(self.root.iterdir()), [])

    def test_install_preserves_host_and_writes_update_compatible_receipt(self):
        host = self.root / 'README.md'
        host.write_bytes(b'Host README')
        result = self.execute()
        self.assertEqual(result['status'], 'installed')
        self.assertEqual(host.read_bytes(), b'Host README')
        self.assertFalse((self.root / 'AGENTS.md').exists())
        self.assertFalse((self.root / 'Agents/.agent/config/BOUNDARIES.yaml').exists())
        kit = self.root / 'Agents'
        manifest = (kit / MANIFEST).read_bytes()
        receipt = strict_json((kit / setup.RECEIPT).read_bytes())
        self.assertEqual(receipt['manifest_sha256'], sha(manifest))
        self.assertEqual(receipt['identity']['repository'], setup.REPOSITORY)
        self.assertIn('init_required', Path(result['markdown']).read_text(encoding='utf-8'))
        self.assertTrue(Path(result['json']).is_file())

    def test_existing_policy_routes_to_ask_init_and_is_unchanged(self):
        self.policy()
        original = self.boundaries.read_bytes()
        result = self.execute()
        self.assertEqual(result['continuation']['action'], 'ask_init')
        self.assertEqual(self.boundaries.read_bytes(), original)

    def test_existing_empty_folder_is_not_adopted(self):
        (self.root / 'Agents').mkdir()
        self.assertEqual(self.installer().plan()['status'], 'destination_conflict')

    def test_existing_installation_routes_to_update_without_downloading(self):
        self.execute()
        self.source.calls.clear()
        self.assertEqual(self.installer().plan()['status'], 'existing_kit')
        self.assertEqual(self.source.calls, [])

    def test_preview_hash_notification_and_destination_drift_block_before_writes(self):
        installer = self.installer()
        plan = installer.plan()
        with self.assertRaises(setup.shared.Conflict):
            installer.apply(plan, expected_sha='0' * 64, notified=True)
        with self.assertRaises(setup.shared.Blocked):
            installer.apply(plan, expected_sha=plan['archive_sha256'])
        (self.root / 'Agents').mkdir()
        with self.assertRaises(FileExistsError):
            installer.apply(plan, expected_sha=plan['archive_sha256'], notified=True)
        self.assertEqual(list((self.root / 'Agents').iterdir()), [])

    def test_incomplete_bundle_or_broken_links_stop_before_installation(self):
        for missing in ('refine', 'implement', 'backlog', 'create-skill', 'to-tasks'):
            with self.subTest(missing=missing):
                self.source.payload = files()
                self.source.payload.pop(f'.agent/skills/{missing}/SKILL.md')
                with self.assertRaises(ReleaseError):
                    self.installer().plan()
        self.source.payload = files()
        self.source.payload['README.md'] = b'[Missing](absent.md)\n'
        with self.assertRaises(ReleaseError):
            self.installer().plan()
        self.assertFalse((self.root / 'Agents').exists())

    def test_invalid_or_draft_existing_policy_never_uses_bootstrap(self):
        self.boundaries.parent.mkdir(parents=True)
        for raw in ('not: a policy\n', 'state: draft\n'):
            self.boundaries.write_text(raw, encoding='utf-8')
            with self.assertRaises((setup.shared.AccessError, ValueError)):
                self.installer()

    def test_multiple_policies_require_selection(self):
        self.policy()
        (self.root / 'BOUNDARIES.yaml').write_bytes(self.boundaries.read_bytes())
        with self.assertRaises(setup.shared.Blocked):
            self.installer()
        self.assertEqual(self.installer(boundaries=self.boundaries).plan()['status'], 'ready')

    def test_policy_never_cannot_be_approved(self):
        self.policy(create='never')
        with self.assertRaises(setup.shared.Blocked):
            self.execute(self.installer(approvals=['create:Agents']))
        self.assertFalse((self.root / 'Agents').exists())

    def test_policy_changes_or_appears_after_preview_stop_application(self):
        installer = self.installer()
        plan = installer.plan()
        self.policy()
        with self.assertRaises(setup.shared.Blocked):
            installer.apply(plan, expected_sha=plan['archive_sha256'], notified=True)
        self.assertFalse((self.root / 'Agents').exists())

    def test_source_access_failure_or_override_cannot_use_bootstrap(self):
        self.policy()
        policy = setup.shared.INIT.load_yaml(self.boundaries.read_text(encoding='utf-8'))
        policy['resources']['remote'][0]['effective_mode'] = 'none'
        policy['resources']['remote'][0]['access']['status'] = 'unavailable'
        policy['resources']['remote'][0]['access']['capability'] = 'none'
        policy['resources']['remote'][0]['access']['reason'] = 'Fixture read access unavailable'
        self.boundaries.write_text(setup.shared.INIT.yaml.safe_dump(policy), encoding='utf-8')
        with self.assertRaises(setup.shared.Blocked):
            self.installer().plan()
        self.source.repository = 'other/repository'
        with self.assertRaises(setup.shared.Blocked):
            self.installer()

    def test_host_repository_is_not_silently_used_as_the_release_source(self):
        self.policy()
        policy = setup.shared.INIT.load_yaml(self.boundaries.read_text(encoding='utf-8'))
        policy['resources']['remote'][0]['url'] = 'https://github.com/example/host.git'
        self.boundaries.write_text(setup.shared.INIT.yaml.safe_dump(policy), encoding='utf-8')
        original = self.boundaries.read_bytes()
        with self.assertRaises(setup.shared.Blocked):
            self.installer().plan()
        self.assertEqual(self.boundaries.read_bytes(), original)
        self.assertEqual(self.source.calls, [])

    def test_interruption_blocks_fresh_install_and_update_then_recovers(self):
        def interrupt(name):
            raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            self.execute(after_write=interrupt)
        installer = self.installer()
        self.assertEqual(installer.plan()['status'], 'recovery_required')
        self.policy(delete='act')
        with self.assertRaises(setup.shared.Blocked):
            setup.shared.Updater(self.boundaries, self.root / 'Agents', 'kit', source=self.source)
        result = self.installer().recover()
        self.assertEqual(result['status'], 'rolled_back')
        self.assertFalse(any((self.root / 'Agents/.agent/skills').rglob('SKILL.md')))
        self.assertEqual(self.installer().plan()['status'], 'destination_conflict')

    def test_failure_cleans_only_recorded_unchanged_files(self):
        def fail(name):
            (self.root / 'Agents/notes.txt').write_bytes(b'Unmanaged')
            raise RuntimeError('Fixture failure')
        result = self.execute(after_write=fail)
        self.assertEqual(result['status'], 'rolled_back')
        self.assertEqual((self.root / 'Agents/notes.txt').read_bytes(), b'Unmanaged')

    def test_changed_written_file_is_preserved_for_recovery(self):
        def fail(name):
            (self.root / 'Agents' / name).write_bytes(b'Concurrent edit')
            raise RuntimeError('Fixture failure')
        result = self.execute(after_write=fail)
        self.assertEqual(result['status'], 'recovery_required')
        self.assertTrue(result['detail']['remaining'])

    def test_missing_delete_permission_is_a_recovery_blocker(self):
        self.policy()  # Template delete permission is ask, not act.
        def fail(name):
            raise RuntimeError('Fixture failure')
        result = self.execute(after_write=fail)
        self.assertEqual(result['status'], 'recovery_required')
        self.assertIn('delete', result['detail']['remaining'][0]['reason'])
        result = self.installer(approvals=['delete:Agents']).recover()
        self.assertEqual(result['status'], 'rolled_back')

    def test_complete_interrupted_finalization_is_verified_not_removed(self):
        installer = self.installer()
        plan = installer.plan()
        last = next(reversed(plan['desired']))
        def interrupt(name):
            if name == last:
                raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            installer.apply(plan, expected_sha=plan['archive_sha256'], notified=True, after_write=interrupt)
        self.assertEqual(self.installer().recover()['status'], 'installed')
        self.assertTrue((self.root / 'Agents' / setup.RECEIPT).exists())

    def test_committed_installation_drift_is_never_rolled_back(self):
        self.execute()
        path = self.root / 'Agents/README.md'
        path.write_bytes(b'Local edits')
        self.assertEqual(self.installer().recover()['status'], 'recovery_required')
        self.assertEqual(path.read_bytes(), b'Local edits')

    def test_recovery_rejects_journal_paths_outside_managed_inventory(self):
        def interrupt(name):
            raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            self.execute(after_write=interrupt)
        path = self.root / 'Agents' / setup.JOURNAL
        journal = strict_json(path.read_bytes())
        journal['expected']['../host.txt'] = '0' * 64
        path.write_bytes(json_bytes(journal))
        with self.assertRaises(ReleaseError):
            self.installer().recover()

    def test_unknown_partial_or_replaced_file_is_not_removed(self):
        def interrupt(name):
            raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            self.execute(after_write=interrupt)
        path = self.root / 'Agents' / setup.JOURNAL
        journal = strict_json(path.read_bytes())
        journal['created'] = {}  # Simulate crash before file ownership reached the journal.
        path.write_bytes(json_bytes(journal))
        result = self.installer().recover()
        self.assertEqual(result['status'], 'recovery_required')

    def test_installed_receipt_is_accepted_by_update_without_baseline_guessing(self):
        self.execute()
        self.policy()
        updater = setup.shared.Updater(self.boundaries, self.root / 'Agents', 'kit', source=self.source)
        baseline = updater.baseline()
        self.assertEqual(baseline['manifest']['version'], 'v1.2.0')


if __name__ == '__main__':
    unittest.main()
