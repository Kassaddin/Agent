"""Normal cleanup acceptance flows using local release fixtures, never the network."""
from pathlib import Path
import io
import sys
import tempfile
import unittest
import zipfile

SKILLS = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILLS / 'update/scripts'))
import update_kit as update
from release_format import make_manifest, json_bytes, unpack, sha, MANIFEST, LEGACY_MANIFEST
from migrate_kit import Migrator
import integrate_project
sys.path.insert(0, str(SKILLS / 'setup/scripts'))
import setup_kit as setup

def package(files, version):
    manifest = make_manifest(files, version)
    manifest_name = LEGACY_MANIFEST if manifest['layout_version'] == 2 else MANIFEST
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as archive:
        for name, raw in {**files, manifest_name: json_bytes(manifest)}.items():
            archive.writestr('Agents/' + name, raw)
    raw = stream.getvalue()
    result = unpack(raw, f'{sha(raw)}  agent-skills.zip\n'.encode(), version)
    result['identity'] = {'repository': setup.REPOSITORY, 'version': version, 'release_id': 1, 'asset_id': 2, 'archive_sha256': sha(raw)}
    return result

class Source:
    repository = setup.REPOSITORY
    def __init__(self):
        legacy = {'.agent/skills/context/SKILL.md': b'---\nname: context\ndescription: Context fixture.\n---\n# Context\n',
                  'README.md': b'# Existing kit\n', 'docs/guide.md': b'# Guide\n', '.agent/instructions.md': b'# Instructions\n', '.gitignore': b'/.agent/state/\n'}
        new = {f'.agents/skills/{name}/SKILL.md': f'---\nname: {name}\ndescription: Fixture.\n---\n# Skill\n'.encode() for name in setup.REQUIRED_SKILLS}
        new.update({'README.md': b'# Kit\n', 'docs/guide.md': b'# Guide\n', '.agents/instructions.md': b'# Instructions\n', '.gitignore': b'/.agents/state/\n'})
        self.bundles = {'v1.7.0': package(legacy, 'v1.7.0'), 'v2.0.0': package(new, 'v2.0.0')}
    def select(self, version=None):
        return {'tag_name': version or 'v2.0.0'}
    def package(self, release, **kwargs):
        return self.bundles[release['tag_name']]

class CleanupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='cleanup-acceptance-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.kit = self.root / 'Agents'
        self.source = Source()
        self.policy = self.root / '.agents/config/BOUNDARIES.yaml'
        value = update.INIT.load_yaml((SKILLS / 'init/assets/boundaries-template.yaml').read_text(encoding='utf-8'))
        value['state'] = 'active'
        value['resources']['local'] = [value['resources']['local'][0]]
        value['resources']['local'][0]['path'] = str(self.root)
        value['resources']['local'][0]['permissions'] = {name: 'act' for name in ('read', 'create', 'modify', 'delete', 'execute')}
        value['resources']['remote'] = [{'id': 'kit', 'url': 'https://github.com/' + setup.REPOSITORY + '.git', 'kind': 'git_repository', 'local_ids': ['project'],
                                        'requested_mode': 'read', 'effective_mode': 'read', 'access': {'capability': 'read', 'status': 'ready', 'visibility': 'public', 'checked_at': '2026-11-24T00:00:00Z', 'reason': None},
                                        'write_approval': 'ask_each_time', 'trust_granted_at': None}]
        self.policy.parent.mkdir(parents=True)
        self.policy.write_text(update.INIT.yaml.safe_dump(value, sort_keys=False), encoding='utf-8')

    def old_kit(self):
        bundle = self.source.bundles['v1.7.0']
        files = {**bundle['files'], LEGACY_MANIFEST: bundle['manifest_raw'],
                 '.agent/state/update/receipt.json': json_bytes({'schema_version': 1, 'identity': bundle['identity'], 'manifest_sha256': sha(bundle['manifest_raw'])}),
                 '.agent/local-skills/my-skill/notes.md': b'Preserve my literal .agent/path reference.\n',
                 '.agent/reports/old/report.json': b'{"captured_path":".agent/skills/context/SKILL.md"}\n'}
        for name, raw in files.items():
            path = self.kit / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)

    def migrator(self):
        return Migrator(self.root, update.Access(self.policy), self.source, self.policy)

    def test_setup_plans_without_mutating_the_old_kit(self):
        self.old_kit()
        before = {p.relative_to(self.kit).as_posix(): p.read_bytes() for p in self.kit.rglob('*') if p.is_file()}
        plan = setup.Installer(self.root, boundaries=self.policy, source_id='kit', source=self.source).plan()
        self.assertEqual(plan['status'], 'migration_approval_required')
        self.assertTrue(any(item['to'] == '.agents/skills/project-context/SKILL.md' for item in plan['entries']))
        self.assertFalse((self.kit / '.agents').exists())
        self.assertEqual(before, {p.relative_to(self.kit).as_posix(): p.read_bytes() for p in self.kit.rglob('*') if p.is_file()})

    def test_migration_then_separate_update_preserves_local_content(self):
        self.old_kit()
        migrator = self.migrator()
        plan = migrator.plan()
        result = migrator.apply(plan, approved=True, expected_sha=plan['plan_sha256'])
        self.assertEqual(result['status'], 'migrated')
        self.assertEqual(result['release_update'], 'pending')
        self.assertFalse((self.kit / '.agent').exists())
        self.assertEqual((self.kit / '.agents/local-skills/my-skill/notes.md').read_bytes(), b'Preserve my literal .agent/path reference.\n')
        self.assertEqual((self.kit / '.agents/reports/old/report.json').read_bytes(), b'{"captured_path":".agent/skills/context/SKILL.md"}\n')
        updater = update.Updater(self.policy, self.kit, 'kit', source=self.source)
        preview = updater.plan()
        self.assertEqual(preview['status'], 'ready')
        outcome = updater.apply(preview, expected_sha=preview['archive_sha256'], notified=True)
        self.assertEqual(outcome['status'], 'updated')
        self.assertEqual(updater.plan()['status'], 'already_current')

    def test_local_managed_changes_are_reported_before_migration(self):
        self.old_kit()
        path = self.kit / '.agent/skills/context/SKILL.md'
        path.write_bytes(path.read_bytes() + b'Local requirement.\n')
        self.assertEqual(self.migrator().plan()['status'], 'conflicts')
        self.assertFalse((self.kit / '.agents').exists())

    def test_policy_location_is_reviewed_and_reloaded_without_permission_changes(self):
        self.old_kit()
        original = update.INIT.load_yaml(self.policy.read_text(encoding='utf-8'))
        moved_policy = self.kit / '.agent/config/BOUNDARIES.yaml'
        moved_policy.parent.mkdir(parents=True)
        self.policy.rename(moved_policy)
        self.policy = moved_policy
        migrator = self.migrator()
        plan = migrator.plan()
        self.assertIsNotNone(plan['policy_preview'])
        self.assertEqual(plan['policy_preview']['before'], plan['policy_preview']['after'])
        with self.assertRaises(update.Blocked):
            migrator.apply(plan, approved=True, expected_sha=plan['plan_sha256'])
        result = migrator.apply(plan, approved=True, expected_sha=plan['plan_sha256'], policy_reviewed=True)
        self.assertEqual(result['status'], 'migrated')
        self.assertEqual(update.INIT.load_yaml(Path(result['boundaries']).read_text(encoding='utf-8')), original)

    def test_interrupted_migration_resumes_recorded_outputs(self):
        self.old_kit()
        migrator = self.migrator()
        plan = migrator.plan()
        def interrupt(name):
            raise RuntimeError('Fixture interruption')
        with self.assertRaises(RuntimeError):
            migrator.apply(plan, approved=True, expected_sha=plan['plan_sha256'], after_move=interrupt)
        self.assertEqual(self.migrator().recover(approved=True, expected_sha=plan['plan_sha256'])['status'], 'migrated')

    def test_missing_delete_permission_blocks_before_moving_any_file(self):
        self.old_kit()
        value = update.INIT.load_yaml(self.policy.read_text(encoding='utf-8'))
        value['resources']['local'][0]['permissions']['delete'] = 'never'
        self.policy.write_text(update.INIT.yaml.safe_dump(value, sort_keys=False), encoding='utf-8')
        migrator = self.migrator()
        plan = migrator.plan()
        with self.assertRaises(update.Blocked):
            migrator.apply(plan, approved=True, expected_sha=plan['plan_sha256'])
        self.assertTrue((self.kit / '.agent/skills/context/SKILL.md').is_file())
        self.assertFalse((self.kit / '.agents').exists())

    def test_host_pointer_is_reviewed_preserves_content_and_is_idempotent(self):
        installer = setup.Installer(self.root, boundaries=self.policy, source_id='kit', source=self.source)
        preview = installer.plan()
        self.assertEqual(installer.apply(preview, expected_sha=preview['archive_sha256'], notified=True)['status'], 'installed')
        host = self.root / 'AGENTS.md'
        host.write_bytes(b'User rules.\nSee Agents/.agent/instructions.md\n')
        original = host.read_bytes()
        preview = integrate_project.plan(self.root, self.policy)
        self.assertEqual(host.read_bytes(), original)
        self.assertEqual(preview['status'], 'approval_required')
        result = integrate_project.apply(preview, approved=True, expected_sha=preview['after_sha256'])
        self.assertEqual(result['status'], 'integrated')
        self.assertIn(b'User rules.\n', host.read_bytes())
        self.assertNotIn(b'Agents/.agent/', host.read_bytes())
        self.assertEqual((self.kit / '.agents/state/integration/host-original.bin').read_bytes(), original)
        self.assertEqual(integrate_project.plan(self.root, self.policy)['status'], 'already_integrated')

if __name__ == '__main__':
    unittest.main()
