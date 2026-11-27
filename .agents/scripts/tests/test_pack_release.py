"""Exercise release inventories, repository checks, and private-path checks."""
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import zipfile

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
import pack_release
from release_format import unpack


SETUP = '.agents/skills/setup/'
REVIEWED = {
    'SKILL.md': (b"`https://github.com/Kassaddin/Agents`",),
    'references/setup-contract.md': (b"`https://github.com/Kassaddin/Agents`",),
    'scripts/setup_kit.py': (b"REPOSITORY = 'Kassaddin/Agents'",),
    'tests/test_setup.py': (
        b"'url': 'https://github.com/Kassaddin/Agents.git',",
        b"self.source.repository = 'Kassaddin/Agents'",
    ),
}
NEGATIVE_FIXTURE = b"self.source.repository = 'Kassaddin/Agent'"


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        source = SCRIPTS.parents[1]
        for package in pack_release.PACKAGES:
            relative = Path('.agents/skills') / package
            shutil.copytree(source / relative, self.root / relative,
                            ignore=shutil.ignore_patterns(*pack_release.EXCLUDED))
        shutil.copytree(source / '.agents/assets', self.root / '.agents/assets')
        (self.root / 'docs').mkdir()
        shutil.copyfile(source / 'docs/guide.md', self.root / 'docs/guide.md')

    def reject(self, relative, changed):
        path = self.root / relative
        original = path.read_bytes()
        self.assertNotEqual(changed, original)
        path.write_bytes(changed)
        try:
            with self.assertRaisesRegex(ValueError, 'A project-specific path or repository identity'):
                pack_release.build(self.root, 'v2.2.0')
        finally:
            path.write_bytes(original)

    def test_reviewed_setup_literals_are_packaged_verbatim(self):
        pack_release.build(self.root, 'v2.2.0')
        with (zipfile.ZipFile(self.root / 'releases/agent-skills.zip') as kit,
              zipfile.ZipFile(self.root / 'releases/setup.zip') as standalone):
            for relative, literals in REVIEWED.items():
                source = (self.root / SETUP / relative).read_bytes()
                for literal in literals:
                    self.assertIn(literal, source)
                self.assertEqual(kit.read('Agents/' + SETUP + relative), source)
                self.assertEqual(standalone.read('setup/' + relative), source)
            self.assertIn(NEGATIVE_FIXTURE, standalone.read('setup/tests/test_setup.py'))

    def test_google_and_research_are_managed_and_listed_in_the_released_skill_catalog(self):
        pack_release.build(self.root, 'v2.5.0')
        releases = self.root / 'releases'
        kit = unpack((releases / 'agent-skills.zip').read_bytes(),
                     (releases / 'agent-skills.zip.sha256').read_bytes(), 'v2.5.0')
        for skill in ('google', 'research'):
            with self.subTest(skill=skill):
                self.assertIn(skill, kit['manifest']['skills'])
                for name in ('SKILL.md', 'agents/openai.yaml'):
                    path = f'.agents/skills/{skill}/{name}'
                    self.assertEqual(kit['files'][path], (self.root / path).read_bytes())
                self.assertIn(f'| `${skill}` |'.encode(), kit['files']['.agents/instructions.md'])
        with zipfile.ZipFile(releases / 'setup.zip') as standalone:
            self.assertTrue(all(name.startswith('setup/') for name in standalone.namelist()))

    def test_repository_collisions_in_every_reviewed_context_are_rejected(self):
        for relative, literals in REVIEWED.items():
            source = (self.root / SETUP / relative).read_bytes()
            for literal in literals:
                for identity in (b'MirrorKassaddin/Agents', b'Mirror-Kassaddin/Agents',
                                 b'Kassaddin-Mirror-Kassaddin/Agents', b'Kassaddin/Agents-backup'):
                    with self.subTest(relative=relative, literal=literal, identity=identity):
                        alternate = literal.replace(b'Kassaddin/Agents', identity)
                        self.reject(SETUP + relative, source.replace(literal, alternate, 1))

    def test_only_exact_setup_negative_fixture_is_exempt(self):
        relative = SETUP + 'tests/test_setup.py'
        source = (self.root / relative).read_bytes()
        self.reject(relative, source.replace(NEGATIVE_FIXTURE,
                                             NEGATIVE_FIXTURE.replace(b'Kassaddin', b'MirrorKassaddin'), 1))
        self.reject(relative, source.replace(b"self.source.repository = 'Kassaddin/Agents'",
                                             NEGATIVE_FIXTURE, 1))
        self.reject(relative, source + b"\nother_repository = 'Kassaddin/Agent'\n")

    def test_other_literals_and_private_paths_are_rejected(self):
        cases = {
            SETUP + 'SKILL.md': (
                b"`https://example.test/Kassaddin/Agents`",
                b"`https://github.com/Mirror/Kassaddin/Agents`",
                b"`https://github.com/Kassaddin/Agents.git`",
                b"`Kassaddin/Agents`",
                b"`C:/Users/Example/repo`",
            ),
            '.agents/skills/backlog/SKILL.md': (
                b"`https://github.com/Kassaddin/Agents`",
                b"`c:\\users\\example\\repo`",
                b"`g:/vault/example`",
            ),
        }
        for relative, markers in cases.items():
            source = (self.root / relative).read_bytes()
            for marker in markers:
                with self.subTest(relative=relative, marker=marker):
                    self.reject(relative, source + b'\n' + marker + b'\n')


if __name__ == '__main__':
    unittest.main()
