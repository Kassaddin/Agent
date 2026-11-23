#!/usr/bin/env python3
"""First-install the fixed published kit; default is a non-writing preview."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import sys
from urllib.parse import quote
import uuid

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'update/scripts'))
import update_kit as shared
from release_format import GUIDANCE, MANIFEST, ReleaseError, json_bytes, managed_path, safe_path, sha, strict_json, version_key
from release_source import GitHubSource, NoRelease, SourceError, repository_identity

REPOSITORY = 'Kassaddin/Agent'
REQUIRED_SKILLS = {'backlog', 'context', 'fix', 'glossary', 'implement', 'init', 'refine', 'search', 'setup', 'smokes', 'to-document', 'update'}
JOURNAL = '.agent/state/setup/journal.json'
LOCK = '.agent/state/setup/lock'
RECEIPT = shared.RECEIPT


def absolute(path):
    return Path(os.path.abspath(path))


def no_links(path):
    for part in (path, *path.parents):
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise shared.Blocked('Setup does not follow project or kit links/junctions')


def boundary_candidates(root):
    return [root / '.agent/config/BOUNDARIES.yaml', root / 'Agents/.agent/config/BOUNDARIES.yaml', root / 'BOUNDARIES.yaml']


def discover(root, explicit=None):
    if explicit is not None:
        selected = absolute(explicit if Path(explicit).is_absolute() else root / explicit)
        no_links(selected)
        if not selected.is_file():
            raise shared.Blocked('The explicitly selected boundary file is missing or not a regular file')
        return selected
    found = []
    for candidate in boundary_candidates(root):
        no_links(candidate)
        if candidate.exists():
            found.append(candidate)
    if len(found) > 1:
        raise shared.Blocked('Multiple boundary files exist; select one explicitly')
    return found[0] if found else None


class BootstrapAccess:
    """Ephemeral caller-authorized kit access; never saves or impersonates a policy."""
    def __init__(self, root):
        self.root = root
        self.kit = root / 'Agents'

    def require(self, path, op='read'):
        path = absolute(path)
        no_links(path)
        if discover(self.root) is not None:
            raise shared.Blocked('Boundaries appeared; reload them before further bootstrap operations')
        if path == self.root and op == 'read':
            return
        if not path.is_relative_to(self.kit) or op not in {'read', 'create', 'modify', 'delete'}:
            raise shared.Blocked('Bootstrap authorization covers only the new project kit')

    def read(self, path):
        self.require(path)
        if not path.exists():
            return None
        if not path.is_file() or path.stat().st_size > 8 * 1024 * 1024:
            raise shared.Blocked('Expected a bounded regular installation file')
        return path.read_bytes()


class Installer:
    def __init__(self, project_root, *, boundaries=None, source_id=None, bootstrap_approved=False, approvals=(), source=None):
        self.root = absolute(project_root)
        no_links(self.root)
        if not self.root.is_dir():
            raise shared.Blocked('Select an existing local project folder')
        self.kit = self.root / 'Agents'
        no_links(self.kit)
        self.boundaries = discover(self.root, boundaries)
        self.remote = None
        if self.boundaries:
            self.access = shared.Access(self.boundaries, approvals)
            self.access.require(self.root)
            if self.access.data['conversation']['investigate_within_scope'] != 'act':
                raise shared.Blocked('Investigation is not currently permitted')
            self.source_id = source_id
            candidates = []
            for item in self.access.data['resources']['remote']:
                if item['kind'] != 'git_repository' or (source_id is not None and item['id'] != source_id):
                    continue
                try:
                    identity = repository_identity(item['url'])
                except SourceError:
                    continue
                if identity.casefold() == REPOSITORY.casefold():
                    candidates.append(item)
            if len(candidates) == 1:
                self.remote = candidates[0]
            # Local recovery remains possible if source access is no longer available.
        else:
            if not bootstrap_approved:
                raise shared.Blocked('No policy exists; obtain explicit fixed-source and destination bootstrap authorization')
            if source_id is not None or approvals:
                raise shared.Blocked('Bootstrap uses its scoped grant, not policy source IDs or path approvals')
            self.access = BootstrapAccess(self.root)
        self.source = source or GitHubSource(REPOSITORY, authorize=self.check_remote)
        if self.source.repository.casefold() != REPOSITORY.casefold():
            raise shared.Blocked('Setup supports only its fixed release repository')

    def check_remote(self):
        self.access.require(self.kit)
        if self.boundaries:
            if not self.remote or self.remote['access']['status'] not in {'ready', 'limited'} or self.remote['effective_mode'] not in {'read', 'write'}:
                raise shared.Blocked('Init must establish a usable configured read source for the fixed repository')
            if self.access.data['version_control']['operations']['inspect'] != 'act':
                raise shared.Blocked('Read-only repository inspection is not permitted')

    def path(self, name):
        path = self.kit / safe_path(name)
        no_links(path)
        self.access.require(path)
        return path

    def read(self, name):
        return self.access.read(self.path(name))

    def mkdirs(self, directory):
        missing = []
        while directory != self.root:
            self.access.require(directory)
            if directory.exists():
                if not directory.is_dir():
                    raise shared.Conflict('A required installation directory is occupied')
                break
            self.access.require(directory, 'create')
            missing.append(directory)
            directory = directory.parent
        for directory in reversed(missing):
            self.access.require(directory, 'create')
            directory.mkdir(exist_ok=True)
            no_links(directory)

    def write(self, name, raw, *, exclusive=False):
        path = self.path(name)
        self.access.require(path, 'create' if exclusive or not path.exists() else 'modify')
        self.mkdirs(path.parent)
        no_links(path)
        with path.open('xb' if exclusive else 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
            info = os.fstat(stream.fileno())
        return [info.st_dev, info.st_ino]

    def continuation(self):
        try:
            selected = discover(self.root, self.boundaries)
            return {'action': 'ask_init' if selected else 'init_required', 'boundaries': str(selected) if selected else None,
                    'activation': 'not_assessed', 'note': 'The agent must run or offer Init; installation does not activate boundaries.'}
        except shared.Blocked as exc:
            return {'action': 'select_boundaries', 'activation': 'pending', 'reason': str(exc)}

    def plan(self, version=None):
        self.access.require(self.kit)
        if self.kit.exists():
            if self.read(JOURNAL) is not None:
                journal = self.load_journal()
                if journal['phase'] not in {'installed', 'rolled_back'}:
                    return {'status': 'recovery_required', 'kit': str(self.kit), 'reason': 'Resume Setup with --recover before another operation'}
            manifest = self.read(MANIFEST)
            if manifest is not None:
                return {'status': 'existing_kit', 'kit': str(self.kit), 'reason': 'Use an explicit Update request to verify and update this installation'}
            return {'status': 'destination_conflict', 'kit': str(self.kit), 'reason': 'Existing destinations are never merged, even when empty or previously recovered'}
        self.check_remote()
        candidate = self.source.package(self.source.select(version))
        shared.validate_content(candidate)
        if not REQUIRED_SKILLS <= set(candidate['manifest']['skills']) or not GUIDANCE <= set(candidate['files']):
            raise ReleaseError('Release is not the complete kit supported by this Setup version')
        if candidate['identity'].get('repository', '').casefold() != REPOSITORY.casefold():
            raise ReleaseError('Published identity differs from the fixed Setup source')
        desired = dict(candidate['files'])
        desired[MANIFEST] = candidate['manifest_raw']
        desired[RECEIPT] = json_bytes({'schema_version': 1, 'identity': candidate['identity'], 'manifest_sha256': sha(candidate['manifest_raw'])})
        return {'status': 'ready', 'kit': str(self.kit), 'version': candidate['manifest']['version'],
                'archive_sha256': candidate['archive_sha256'], 'additions': sorted(desired), 'desired': desired,
                'continuation': self.continuation()}

    @staticmethod
    def public(plan):
        return {key: value for key, value in plan.items() if key != 'desired'}

    @contextmanager
    def lock(self):
        path = self.path(LOCK)
        self.access.require(path, 'modify' if path.exists() else 'create')
        self.mkdirs(path.parent)
        with path.open('a+b') as stream:
            if path.stat().st_size == 0:
                stream.write(b'0')
                stream.flush()
            stream.seek(0)
            try:
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise shared.Blocked('Another Setup process holds this kit lock') from exc
            try:
                yield
            finally:
                stream.seek(0)
                if os.name == 'nt':
                    msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(stream, fcntl.LOCK_UN)

    def emit(self, journal, status, detail, attempt=None):
        attempt = attempt or uuid.uuid4().hex
        name = f'.agent/reports/setup/{attempt}/outcome.json'
        human = f'docs/reports/setup/{attempt}/outcome.md'
        result = {'schema_version': 1, 'run': journal['run'], 'status': status, 'kit': str(self.kit), 'version': journal['version'],
                  'archive_sha256': journal['archive_sha256'], 'created_at': datetime.now(timezone.utc).isoformat(),
                  'continuation': self.continuation(), 'detail': detail}
        self.write(name, json_bytes(result), exclusive=True)
        link = quote(os.path.relpath(self.path(name), self.path(human).parent).replace(os.sep, '/'), safe='/._-')
        rendered = json_bytes({'detail': detail, 'continuation': result['continuation']}).decode()
        fence = '~~~'
        while fence in rendered:
            fence += '~'
        self.write(human, f'# Setup outcome\n\nStatus: {status}\n\nVersion: {journal["version"]}\n\n{fence}json\n{rendered}{fence}\n\n[Structured outcome]({link})\n\nInstallation and boundary activation are separate.\n'.encode(), exclusive=True)
        return {**result, 'json': str(self.path(name)), 'markdown': str(self.path(human))}

    def preflight(self, plan, attempt):
        self.access.require(self.kit, 'create')
        names = list(plan['desired']) + [JOURNAL, LOCK, f'.agent/reports/setup/{attempt}/outcome.json', f'docs/reports/setup/{attempt}/outcome.md']
        for name in names:
            path = self.path(name)
            self.access.require(path, 'create')
            for parent in path.parents:
                if parent == self.root:
                    break
                self.access.require(parent, 'create')
        # Journaling is mutable even though all managed-file writes are exclusive creations.
        self.access.require(self.path(JOURNAL), 'modify')

    def apply(self, plan, *, expected_sha, notified=False, after_write=None):
        if plan['status'] != 'ready':
            return self.public(plan)
        if expected_sha != plan['archive_sha256']:
            raise shared.Conflict('Release differs from the previewed archive hash')
        if not notified:
            raise shared.Blocked('Notify the user of the destination and additions before installing')
        self.check_remote()
        attempt = uuid.uuid4().hex
        self.preflight(plan, attempt)
        # Exclusive reservation prevents two first installers from merging their writes.
        self.access.require(self.kit, 'create')
        self.kit.mkdir(exist_ok=False)
        journal = {'schema_version': 1, 'run': uuid.uuid4().hex, 'phase': 'installing', 'version': plan['version'],
                   'archive_sha256': plan['archive_sha256'], 'expected': {name: sha(raw) for name, raw in plan['desired'].items()}, 'created': {}}
        try:
            with self.lock():
                self.write(JOURNAL, json_bytes(journal), exclusive=True)
                for name, raw in plan['desired'].items():
                    identity = self.write(name, raw, exclusive=True)
                    journal['created'][name] = identity
                    self.write(JOURNAL, json_bytes(journal))
                    if after_write:
                        after_write(name)
                if any(self.read(name) != raw for name, raw in plan['desired'].items()):
                    raise shared.Conflict('Installed bytes did not verify')
                journal['phase'] = 'installed'
                self.write(JOURNAL, json_bytes(journal))
                return self.emit(journal, 'installed', {'files_verified': len(plan['desired'])}, attempt)
        except Exception as exc:
            # A missing/corrupt journal or lost permission remains a visible recovery blocker.
            try:
                result = self.recover()
                return {**result, 'failure': type(exc).__name__}
            except Exception:
                return {'status': 'recovery_required', 'kit': str(self.kit), 'journal': str(self.kit / JOURNAL),
                        'reason': 'Installation/finalization failed; preserve the kit and inspect its journal before retrying', 'failure': type(exc).__name__}

    def load_journal(self):
        journal = strict_json(self.read(JOURNAL))
        if not isinstance(journal, dict) or set(journal) != {'schema_version', 'run', 'phase', 'version', 'archive_sha256', 'expected', 'created'} or journal['schema_version'] != 1:
            raise shared.Blocked('Invalid Setup recovery journal')
        if not isinstance(journal['run'], str) or not re.fullmatch('[a-f0-9]{32}', journal['run']) or journal['phase'] not in {'installing', 'installed', 'rolled_back', 'recovery_required'}:
            raise shared.Blocked('Invalid Setup recovery phase or run')
        version_key(journal['version'])
        if not isinstance(journal['archive_sha256'], str) or not re.fullmatch('[a-f0-9]{64}', journal['archive_sha256']):
            raise shared.Blocked('Invalid Setup archive identity')
        expected, created = journal['expected'], journal['created']
        if not isinstance(expected, dict) or not 3 <= len(expected) <= 2002 or not isinstance(created, dict) or not set(created) <= set(expected) or not {MANIFEST, RECEIPT} <= set(expected):
            raise shared.Blocked('Invalid Setup recovery inventory')
        for name, fingerprint in expected.items():
            if name not in {MANIFEST, RECEIPT}:
                managed_path(name)
            if not isinstance(fingerprint, str) or not re.fullmatch('[a-f0-9]{64}', fingerprint):
                raise shared.Blocked('Invalid Setup recovery hash')
        for identity in created.values():
            if not isinstance(identity, list) or len(identity) != 2 or any(type(value) is not int or value < 0 for value in identity):
                raise shared.Blocked('Invalid Setup file identity')
        return journal

    def recover(self):
        if not self.kit.is_dir() or self.read(JOURNAL) is None:
            raise shared.Blocked('No Setup journal is available; do not infer ownership or delete the destination')
        with self.lock():
            journal = self.load_journal()
            current = {name: self.read(name) for name in journal['expected']}
            if all(raw is not None and sha(raw) == journal['expected'][name] for name, raw in current.items()):
                journal['phase'] = 'installed'
                self.write(JOURNAL, json_bytes(journal))
                return self.emit(journal, 'installed', {'reason': 'Verified complete inventory after interrupted finalization'})
            if journal['phase'] == 'installed':
                return self.emit(journal, 'recovery_required', {'reason': 'A completed kit changed; preserve it for inspection'})
            remaining = []
            for name, raw in current.items():
                if raw is None:
                    continue
                path = self.path(name)
                info = path.stat()
                identity = journal['created'].get(name)
                if not identity or identity[1] == 0 or [info.st_dev, info.st_ino] != identity or sha(raw) != journal['expected'][name]:
                    remaining.append({'path': name, 'reason': 'Unrecorded, replaced, or changed content; preserved'})
                    continue
                try:
                    self.access.require(path, 'delete')
                    # Recheck content and file identity immediately before bounded removal.
                    check = path.stat()
                    if [check.st_dev, check.st_ino] != identity or self.read(name) != raw:
                        raise shared.Conflict('File changed during recovery')
                    path.unlink()
                except (shared.Blocked, shared.Conflict, OSError) as exc:
                    remaining.append({'path': name, 'reason': str(exc)})
            journal['phase'] = 'recovery_required' if remaining else 'rolled_back'
            self.write(JOURNAL, json_bytes(journal))
            return self.emit(journal, journal['phase'], {'remaining': remaining, 'note': 'Records, unmanaged additions, and empty directories are retained; no recursive deletion'})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, required=True)
    parser.add_argument('--boundaries', type=Path)
    parser.add_argument('--source')
    parser.add_argument('--bootstrap-approved', action='store_true')
    parser.add_argument('--approve', action='append', default=[])
    parser.add_argument('--version')
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument('--apply', action='store_true')
    actions.add_argument('--recover', action='store_true')
    parser.add_argument('--expected-sha')
    parser.add_argument('--notified', action='store_true')
    args = parser.parse_args(argv)
    try:
        installer = Installer(args.project_root, boundaries=args.boundaries, source_id=args.source, bootstrap_approved=args.bootstrap_approved, approvals=args.approve)
        if args.recover:
            result = installer.recover()
        else:
            plan = installer.plan(args.version)
            result = installer.apply(plan, expected_sha=args.expected_sha, notified=args.notified) if args.apply else installer.public(plan)
        print(json_bytes(result).decode(), end='')
        return 0 if result['status'] in {'ready', 'installed', 'rolled_back'} else 1
    except NoRelease:
        result = {'status': 'no_release', 'reason': 'No published stable release is available'}
    except (shared.Blocked, shared.AccessError, shared.Conflict, SourceError, ReleaseError, OSError, ValueError, TypeError, KeyError, shared.INIT.yaml.YAMLError) as exc:
        result = {'status': 'blocked' if isinstance(exc, (shared.Blocked, shared.AccessError)) else 'error',
                  'reason': str(exc) if isinstance(exc, (shared.Blocked, shared.AccessError, shared.Conflict, SourceError, ReleaseError)) else 'Setup input or operation failed; inspect any existing installation journal before retrying'}
    print(json_bytes(result).decode(), end='')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
