"""Project access for the adapted creator helpers. See ../NOTICE.txt and ../license.txt.

Added 2026-11-23 for scoped local authoring; no candidate code is executed.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
LIBRARY = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LIBRARY / 'update/scripts'))
from update_kit import Access, AccessError, Blocked, INIT
from release_format import safe_path
sys.path.insert(0, str(LIBRARY / 'init/scripts'))
from project_layout import ProjectLayout


def add_context(parser):
    parser.add_argument('--boundaries', required=True, type=Path)
    parser.add_argument('--agent-home', type=Path)
    parser.add_argument('--skills-dir', type=Path)
    parser.add_argument('--approve', action='append', default=[])


def skill_name(value):
    if not isinstance(value, str) or len(value) > 64 or not re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*', value):
        raise ValueError('Use a nonempty lowercase hyphenated skill name of at most 64 characters')
    safe_path(value)
    return value


def no_links(path):
    for part in (path, *path.parents):
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise Blocked('Creator helpers do not follow linked/junction paths')


class LocalSkills:
    def __init__(self, boundaries, *, agent_home=None, skills_dir=None, approvals=()):
        self.access = Access(boundaries, approvals)
        self.root = self.access.root
        self.access.require(self.root)
        if not self.root.is_dir():
            raise Blocked('Select an existing primary project directory')
        self.layout = ProjectLayout(self.root, Path(boundaries).absolute(), agent_home)
        chosen = skills_dir if skills_dir is not None else self.layout.home / 'local-skills'
        self.home = Path(os.path.abspath(chosen if Path(chosen).is_absolute() else self.root / chosen))
        self.forbidden = [self.layout.home / name for name in ['skills', 'config', 'context', 'state', 'reports']]
        self.forbidden += [LIBRARY, Path.home() / '.codex/skills']
        if os.environ.get('CODEX_HOME'):
            self.forbidden.append(Path(os.environ['CODEX_HOME']) / 'skills')
        self.check(self.home)
        if self.home.exists() and not self.home.is_dir():
            raise Blocked('The local-skills location is occupied by a file')
        if self.access.data['conversation']['investigate_within_scope'] != 'act':
            raise Blocked('Investigation must be permitted before using creator helpers')

    @classmethod
    def from_args(cls, args):
        return cls(args.boundaries, agent_home=args.agent_home, skills_dir=args.skills_dir, approvals=args.approve)

    def check(self, path, op='read'):
        path = Path(os.path.abspath(path))
        no_links(path)
        self.access.require(path, op)
        if '.git' in (part.casefold() for part in path.relative_to(self.root).parts):
            raise Blocked('Version-control internals are not skill destinations')
        if any(path.is_relative_to(target) or path.resolve().is_relative_to(target.resolve()) for target in self.forbidden):
            raise Blocked('Use a project-local destination outside managed, operational, and personal skill areas')
        if op != 'read' and not path.is_relative_to(self.home) and not (op == 'create' and self.home.is_relative_to(path)):
            raise Blocked('Creator writes must stay within the selected local-skills area')
        return path

    def skill(self, name):
        return self.check(self.home / skill_name(name))

    def read(self, path):
        # References may be elsewhere in the authorized primary project, including
        # selected policy/guidance. Writes always use the separate local area.
        no_links(path)
        return self.access.read(path)

    def preflight(self, files, directories=()):
        for path in list(files) + list(directories):
            self.check(path)
            if path.exists():
                raise Blocked('Creation destination already exists; use an authorized targeted edit')
            self.check(path, 'create')
            parent = path.parent
            while not parent.exists():
                self.check(parent, 'create')
                parent = parent.parent
            self.check(parent)

    def mkdirs(self, path):
        missing = []
        while not path.exists():
            self.check(path, 'create')
            missing.append(path)
            path = path.parent
        self.check(path)
        if not path.is_dir():
            raise Blocked('A required parent directory is occupied by a file')
        for directory in reversed(missing):
            self.check(directory, 'create')
            directory.mkdir(exist_ok=True)
            no_links(directory)

    def create(self, path, raw):
        self.check(path, 'create')
        self.mkdirs(path.parent)
        self.check(path, 'create')
        with path.open('xb') as stream:
            stream.write(raw)
        if self.read(path) != raw:
            raise OSError('Created bytes did not verify')

    def notify_required(self, notified):
        if self.access.data['approvals']['notify_queued_changes'] and not notified:
            raise Blocked('Notify the user of the destinations before applying')

    def files(self, folder, limit=500):
        pending, count = [folder], 0
        while pending:
            directory = self.check(pending.pop())
            with os.scandir(directory) as entries:
                paths = sorted((Path(entry.path) for entry in entries), reverse=True)
            for path in paths:
                if path.name in {'__pycache__', '.git', '.venv', 'node_modules', '.pytest_cache'}:
                    continue
                self.check(path)
                if path.is_dir():
                    pending.append(path)
                elif path.is_file():
                    count += 1
                    if count > limit:
                        raise Blocked('Skill validation exceeded its 500-file budget')
                    yield path


def run(operation):
    try:
        result = operation()
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result['status'] in {'ready', 'scaffold_created', 'metadata_created', 'valid'} else 1
    except (Blocked, AccessError, ValueError, OSError, TypeError, KeyError, INIT.yaml.YAMLError) as exc:
        print(json.dumps({'status': 'blocked' if isinstance(exc, (Blocked, AccessError)) else 'error', 'reason': str(exc),
                          'note': 'Preserve any incomplete scaffold; do not retry by overwriting it.'}, ensure_ascii=False))
        return 1
