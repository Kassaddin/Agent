"""Generate Setup's self-contained bootstrap from canonical owned sources."""
from pathlib import Path
import hashlib
import json

MODULES = {
    'init/scripts': ('validate_boundaries.py', 'project_layout.py', 'requirements.txt'),
    'init/references': ('boundaries.schema.json', 'boundary-contract.md', 'elevated-rights-contract.md', 'project-layout.md', 'version-control-actions.md'),
    'smokes/scripts': ('validate_report.py', 'check_artifacts.py'),
    'smokes/references': ('report.schema.json',),
    'refine/references': ('checkpoint.schema.json',),
    'update/scripts': ('release_format.py', 'release_source.py', 'update_kit.py', 'bootstrap_access.py', 'migrate_kit.py', 'integrate_project.py'),
    'update/references': ('update-contract.md', 'migration-contract.md'),
}

def bundle(root):
    skills = Path(root) / '.agents/skills'
    dest = skills / 'setup/bootstrap'
    if not skills.resolve().is_relative_to(Path(root).resolve()) or not dest.resolve().is_relative_to((skills / 'setup').resolve()):
        raise ValueError('Bootstrap generation cannot leave the selected source package')
    hashes = {}
    for folder, names in MODULES.items():
        for name in names:
            relative = folder + '/' + name
            source = skills / relative
            if source.is_symlink() or not source.resolve().is_relative_to(skills.resolve()):
                raise ValueError('Bootstrap sources must stay in the skill library')
            raw = source.read_bytes()
            if name.endswith('.md'):
                raw = raw.replace(b'(../../setup/SKILL.md)', b'(../../../SKILL.md)')
            target = dest / relative
            if not target.resolve().is_relative_to(dest.resolve()) or target.is_symlink():
                raise ValueError('Bootstrap target escapes its package')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            hashes[relative] = hashlib.sha256(raw).hexdigest()
    (dest / 'provenance.json').write_text(json.dumps({'generated': True, 'canonical_sources': hashes}, indent=2) + '\n', encoding='utf-8')
    return hashes

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, default=Path.cwd())
    print(json.dumps({'bundled_files': len(bundle(parser.parse_args().project_root))}))
