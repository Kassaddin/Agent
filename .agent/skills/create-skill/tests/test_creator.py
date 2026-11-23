"""Behavioral tests for project-local creation and read-only validation."""
from copy import deepcopy
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / 'scripts'))
from project_access import LocalSkills, Blocked, AccessError, INIT
from init_skill import initialize
from generate_openai_yaml import generate, render_metadata
from quick_validate import validate_skill


class CreatorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='project-creator-')
        self.root = Path(self.temporary.name)
        self.addCleanup(self.cleanup)
        self.policy_path = self.root / '.agent/config/BOUNDARIES.yaml'
        self.policy = INIT.load_yaml((SKILL.parent / 'init/assets/boundaries-template.yaml').read_text(encoding='utf-8'))
        self.policy['state'] = 'active'
        self.policy['project']['name'] = 'Creator fixture'
        self.policy['resources']['local'][0]['path'] = str(self.root)
        self.policy['resources']['remote'] = []
        self.save_policy()

    def cleanup(self):
        assert self.root.resolve().parent == Path(tempfile.gettempdir()).resolve()
        assert self.root.name.startswith('project-creator-') and not self.root.is_symlink()
        self.temporary.cleanup()

    def save_policy(self):
        self.policy_path.parent.mkdir(parents=True, exist_ok=True)
        self.policy_path.write_text(INIT.yaml.safe_dump(self.policy, sort_keys=False), encoding='utf-8')

    def context(self, **kwargs):
        return LocalSkills(self.policy_path, **kwargs)

    def create(self, **kwargs):
        context = self.context()
        initialize(context, 'tabletop-notes', apply=True, notified=True, **kwargs)
        return context, context.skill('tabletop-notes')

    def complete(self, folder, body='# Tabletop Notes\n\nUse the project terminology to prepare session notes.\n'):
        (folder / 'SKILL.md').write_text('---\nname: tabletop-notes\ndescription: Prepare project-specific tabletop session notes.\n---\n\n' + body, encoding='utf-8')

    def test_preview_has_no_side_effects_and_uses_separate_local_area(self):
        context = self.context()
        result = initialize(context, 'tabletop-notes')
        self.assertEqual(result['status'], 'ready')
        self.assertEqual(Path(result['skill']), self.root / '.agent/local-skills/tabletop-notes')
        self.assertFalse(context.home.exists())

    def test_creation_is_a_draft_and_has_only_requested_resources(self):
        context, folder = self.create(resources=['references'])
        self.assertTrue((folder / 'references').is_dir())
        self.assertFalse((folder / 'scripts').exists())
        self.assertFalse((folder / 'assets').exists())
        result = validate_skill(context, 'tabletop-notes')
        self.assertEqual(result['status'], 'invalid')
        self.assertTrue(any('scaffold' in error for error in result['errors']))

    def test_completed_skill_validates_without_writes_or_code_execution(self):
        context, folder = self.create(resources=['scripts'])
        self.complete(folder)
        (folder / 'scripts/not-run.py').write_text("from pathlib import Path\nPath(__file__).with_name('executed.txt').write_text('executed')\n", encoding='utf-8')
        before = {path: path.read_bytes() for path in self.root.rglob('*') if path.is_file()}
        self.assertEqual(validate_skill(context, 'tabletop-notes')['status'], 'valid')
        self.assertEqual(before, {path: path.read_bytes() for path in self.root.rglob('*') if path.is_file()})
        self.assertFalse((folder / 'scripts/executed.txt').exists())

    def test_existing_skill_even_empty_is_not_overwritten(self):
        context = self.context()
        folder = context.skill('tabletop-notes')
        folder.mkdir(parents=True)
        (folder / 'notes.txt').write_bytes(b'Local work')
        with self.assertRaises(Blocked):
            initialize(context, 'tabletop-notes', apply=True, notified=True)
        self.assertEqual((folder / 'notes.txt').read_bytes(), b'Local work')

    def test_existing_metadata_policy_dependencies_and_comments_are_preserved(self):
        context, folder = self.create()
        metadata = folder / 'agents/openai.yaml'
        raw = metadata.read_bytes() + b'\n# Preserve this\npolicy:\n  allow_implicit_invocation: false\ndependencies:\n  tools: []\n'
        metadata.write_bytes(raw)
        with self.assertRaises(Blocked):
            generate(context, 'tabletop-notes', overrides=['display_name=Changed'], apply=True, notified=True)
        self.assertEqual(metadata.read_bytes(), raw)

    def test_missing_metadata_can_be_previewed_then_created(self):
        context, folder = self.create()
        (folder / 'agents/openai.yaml').unlink()  # Fixture mutation, not helper behavior.
        self.assertEqual(generate(context, 'tabletop-notes')['status'], 'ready')
        self.assertFalse((folder / 'agents/openai.yaml').exists())
        self.assertEqual(generate(context, 'tabletop-notes', apply=True, notified=True)['status'], 'metadata_created')

    def test_notification_gate_precedes_any_folder_creation(self):
        context = self.context()
        with self.assertRaises(Blocked):
            initialize(context, 'tabletop-notes', apply=True)
        self.assertFalse(context.home.exists())

    def test_never_cannot_be_overridden_and_ask_needs_scoped_grant(self):
        self.policy['resources']['local'][0]['permissions']['create'] = 'ask'
        self.save_policy()
        with self.assertRaises(Blocked):
            initialize(self.context(), 'tabletop-notes', apply=True, notified=True)
        context = self.context(approvals=['create:.agent/local-skills'])
        self.assertEqual(initialize(context, 'tabletop-notes', apply=True, notified=True)['status'], 'scaffold_created')
        self.policy['resources']['local'][0]['permissions']['create'] = 'never'
        self.save_policy()
        with self.assertRaises(Blocked):
            initialize(self.context(approvals=['create:.agent/local-skills']), 'another-skill', apply=True, notified=True)

    def test_protected_and_outside_locations_are_rejected(self):
        for location in ['.agent/skills', '.agent/config', '.agent/state', '.agent/context', '.agent/reports', '.git/skills', '../outside-creator']:
            with self.subTest(location=location), self.assertRaises(Blocked):
                self.context(skills_dir=Path(location))

    def test_configured_personal_skills_root_is_forbidden_even_inside_project(self):
        with mock.patch.dict(os.environ, {'CODEX_HOME': str(self.root / 'codex-home')}):
            with self.assertRaises(Blocked):
                self.context(skills_dir=Path('codex-home/skills'))
        self.assertFalse((self.root / 'codex-home').exists())

    def test_denied_resource_is_not_read_or_traversed_during_validation(self):
        context, folder = self.create(resources=['references'])
        self.complete(folder)
        secret = folder / 'references/private'
        secret.mkdir()
        (secret / 'private.md').write_bytes(b'Not authorized for inspection')
        restriction = deepcopy(self.policy['resources']['local'][0])
        restriction.update(id='private', path=str(secret))
        restriction['permissions']['read'] = 'never'
        self.policy['resources']['local'].append(restriction)
        self.save_policy()
        with self.assertRaises(Blocked):
            validate_skill(self.context(), 'tabletop-notes')

    def test_authorized_custom_location_and_agent_home_are_supported(self):
        context = self.context(skills_dir=Path('project-tools/skills'), agent_home=Path('.agent'))
        initialize(context, 'tabletop-notes', apply=True, notified=True)
        self.assertTrue((self.root / 'project-tools/skills/tabletop-notes/SKILL.md').exists())

    def test_wrapped_kit_default_uses_its_selected_agent_area(self):
        original = self.policy_path
        self.policy_path = self.root / 'Agents/.agent/config/BOUNDARIES.yaml'
        self.save_policy()
        context = self.context()
        self.assertEqual(context.home, self.root / 'Agents/.agent/local-skills')
        self.assertTrue(original.exists())  # Explicit selection does not migrate an existing policy.

    def test_empty_bad_and_nonportable_names_stop_before_writing(self):
        for name in ['', '../escape', 'UpperCase', 'two--parts', 'nul', 'a' * 65]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                initialize(self.context(), name, apply=True, notified=True)
        self.assertFalse((self.root / '.agent/local-skills').exists())

    def test_unknown_resources_and_bad_interface_are_rejected_before_writes(self):
        with self.assertRaises(ValueError):
            initialize(self.context(), 'tabletop-notes', resources=['secrets'], apply=True, notified=True)
        with self.assertRaises(ValueError):
            initialize(self.context(), 'tabletop-notes', overrides=['short_description=Too short'], apply=True, notified=True)
        self.assertFalse((self.root / '.agent/local-skills').exists())

    def test_interface_quotes_unicode_and_multiline_text_safely(self):
        metadata = INIT.load_yaml(render_metadata('tabletop-notes', ['display_name=Session "résumé"', 'default_prompt=Use $tabletop-notes\nfor these notes.']).decode('utf-8'))
        self.assertEqual(metadata['interface']['display_name'], 'Session "résumé"')
        self.assertIn('\n', metadata['interface']['default_prompt'])
        self.assertNotIn('icon_small', metadata['interface'])

    def test_optional_metadata_is_not_invented(self):
        metadata = INIT.load_yaml(render_metadata('tabletop-notes').decode('utf-8'))
        self.assertEqual(set(metadata['interface']), {'display_name', 'short_description'})
        with self.assertRaises(ValueError):
            render_metadata('tabletop-notes', ['default_prompt=Use another tool'])

    def test_frontmatter_mismatch_and_duplicate_keys_are_not_valid(self):
        context, folder = self.create()
        self.complete(folder)
        path = folder / 'SKILL.md'
        path.write_text(path.read_text(encoding='utf-8').replace('name: tabletop-notes', 'name: other-notes'), encoding='utf-8')
        self.assertEqual(validate_skill(context, 'tabletop-notes')['status'], 'invalid')
        path.write_text('---\nname: tabletop-notes\nname: other-notes\ndescription: A fixture description.\n---\n\n# Body\n', encoding='utf-8')
        with self.assertRaises((ValueError, INIT.yaml.YAMLError)):
            validate_skill(context, 'tabletop-notes')

    def test_local_dependency_links_and_python_syntax_are_checked(self):
        context, folder = self.create(resources=['scripts'])
        self.complete(folder, '# Notes\n\n[Missing](references/absent.md)\n')
        (folder / 'scripts/bad.py').write_text('def broken(:\n', encoding='utf-8')
        result = validate_skill(context, 'tabletop-notes')
        self.assertTrue(any('reference is missing' in error for error in result['errors']))
        self.assertTrue(any('syntax' in error for error in result['errors']))

    def test_canonical_project_reference_is_valid_and_external_reference_is_unverified(self):
        context, folder = self.create()
        (self.root / 'TERMS.md').write_text('# Canonical Terms\n\nProject words.\n', encoding='utf-8')
        link = os.path.relpath(self.root / 'TERMS.md', folder).replace(os.sep, '/')
        self.complete(folder, f'# Notes\n\n[Terms]({link}#canonical-terms)\n[Remote](https://example.test/terms)\n')
        result = validate_skill(context, 'tabletop-notes')
        self.assertEqual(result['status'], 'valid')
        self.assertTrue(result['warnings'])

    def test_todo_examples_in_code_are_not_unfinished_instructions(self):
        context, folder = self.create()
        self.complete(folder, '# Notes\n\nUse this placeholder only in the example:\n\n```text\n[TODO: example]\n```\n')
        self.assertEqual(validate_skill(context, 'tabletop-notes')['status'], 'valid')

    def test_changed_policy_is_reloaded_before_further_writes(self):
        context = self.context()
        self.policy['resources']['local'][0]['permissions']['create'] = 'never'
        self.save_policy()
        with self.assertRaises((Blocked, AccessError)):
            initialize(context, 'tabletop-notes', apply=True, notified=True)
        self.assertFalse(context.home.exists())

    def test_incomplete_write_reports_partial_state_without_deleting_it(self):
        context = self.context()
        create = context.create
        def fail_metadata(path, raw):
            if path.name == 'openai.yaml':
                raise OSError('Fixture write failure')
            create(path, raw)
        context.create = fail_metadata
        result = initialize(context, 'tabletop-notes', apply=True, notified=True)
        self.assertEqual(result['status'], 'incomplete')
        self.assertTrue((context.skill('tabletop-notes') / 'SKILL.md').exists())

    def test_cli_defaults_to_preview_and_validator_exit_marks_scaffold_invalid(self):
        command = [sys.executable, '-B', str(SKILL / 'scripts/init_skill.py'), 'tabletop-notes', '--boundaries', str(self.policy_path)]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.root / '.agent/local-skills').exists())
        result = subprocess.run(command + ['--apply', '--notified'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        result = subprocess.run([sys.executable, '-B', str(SKILL / 'scripts/quick_validate.py'), 'tabletop-notes', '--boundaries', str(self.policy_path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
