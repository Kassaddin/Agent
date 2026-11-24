"""Update-owned layout migration. Setup plans; execution needs reviewed approval."""
from __future__ import annotations
import argparse
import base64
from datetime import datetime, timezone
import os
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from update_kit import Access, Blocked, Conflict, validate_content
from release_format import LEGACY_MANIFEST, MANIFEST, json_bytes, sha, strict_json, make_manifest, MAX_TOTAL, GUIDANCE
from release_source import GitHubSource, repository_identity
from bootstrap_access import absolute, no_links, discover, BootstrapAccess

JOURNAL = '.agents/state/migration/layout-v3.json'

def mapped(name):
    return name.replace('.agent/', '.agents/', 1).replace('.agents/skills/context/', '.agents/skills/project-context/', 1)

def translated(name, raw):
    # Immutable reports, receipts, and recovery history retain captured bytes.
    if name.startswith(('.agent/reports/', '.agent/state/')) and not name.startswith('.agent/state/checkpoints/'):
        return raw
    if name in {LEGACY_MANIFEST, '.agent/config/BOUNDARIES.yaml'}:
        return raw
    if not name.endswith(('.md', '.yaml', '.yml', '.json', '.py')) and name != '.gitignore':
        return raw
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeError:
        return raw
    text = text.replace('.agent/', '.agents/').replace('.agent\\', '.agents\\').replace('".agent"', '".agents"').replace("'.agent'", "'.agents'")
    text = text.replace('skills/context/', 'skills/project-context/').replace('../context/', '../project-context/')
    if name.startswith('.agent/skills/context/'):
        text = text.replace('name: context', 'name: project-context').replace('# Context', '# Project Context').replace('display_name: "Context"', 'display_name: "Project Context"')
    text = text.replace('owner: context', 'owner: project-context')
    return text.encode('utf-8')

def relocated_baseline(base):
    files = {mapped(name): translated(name, raw) for name, raw in base['files'].items()}
    # Logical comparison view only: retain the original published identity/raw manifest.
    return {**base, 'manifest': make_manifest(files, base['manifest']['version']), 'files': files}

class Migrator:
    def __init__(self, project_root, access, source, boundaries=None, approvals=()):
        self.root = absolute(project_root)
        self.kit = self.root / 'Agents'
        self.access, self.source = access, source
        self.boundaries = absolute(boundaries) if boundaries else None
        self.approvals = approvals
        no_links(self.kit)
        self.access.require(self.kit)

    def read(self, name):
        path = self.kit / name
        no_links(path)
        return self.access.read(path)

    def write_control(self, data):
        path = self.kit / JOURNAL
        self.access.require(path, 'modify' if path.exists() else 'create')
        parent = path.parent
        while not parent.exists():
            self.access.require(parent, 'create')
            parent = parent.parent
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(json_bytes(data))

    def plan(self, baseline_version=None):
        if self.read(JOURNAL) is not None:
            journal = strict_json(self.read(JOURNAL))
            return {'status': 'migrated' if journal.get('phase') == 'verified' else 'migration_recovery_required', 'journal': str(self.kit / JOURNAL)}
        if not (self.kit / '.agent').is_dir() or (self.kit / '.agents').exists():
            raise Conflict('Migration requires one old .agent area and no competing .agents destination')
        old_manifest = self.read(LEGACY_MANIFEST)
        if old_manifest is None:
            raise Conflict('Restore or identify the matching published layout-2 manifest before migration; no files were changed')
        if old_manifest is not None:
            recorded = strict_json(old_manifest)
            baseline_version = recorded['version']
        if not baseline_version:
            raise Conflict('Select a verifiable published baseline before planning this older kit')
        base = self.source.package(self.source.select(baseline_version))
        validate_content(base)
        if base['manifest']['layout_version'] != 2 or (old_manifest is not None and old_manifest != base['manifest_raw']):
            raise Conflict('Old manifest does not match the published layout-2 baseline')
        receipt_raw = self.read('.agent/state/update/receipt.json')
        if receipt_raw is not None:
            receipt = strict_json(receipt_raw)
            if receipt.get('identity') != base['identity'] or receipt.get('manifest_sha256') != sha(base['manifest_raw']):
                raise Conflict('Old receipt differs from its published baseline')
        for control in ('.agent/state/setup/journal.json', '.agent/state/update/pending.json'):
            raw = self.read(control)
            if raw:
                value = strict_json(raw)
                if ('phase' in value and value['phase'] != 'installed') or ('run' in value and value['run'] is not None):
                    raise Blocked('Recover interrupted installation/update before migration')
        conflicts = [name for name, raw in base['files'].items() if self.read(name) != raw]
        if conflicts:
            return {'status': 'conflicts', 'conflicts': [{'path': name, 'reason': 'Local managed edit or missing file; preserved for a decision'} for name in conflicts]}
        paths = []
        for path in sorted((self.kit / '.agent').rglob('*')):
            no_links(path)
            self.access.require(path)
            if '.git' in path.relative_to(self.kit).parts:
                raise Blocked('Nested version-control data needs an explicit user migration action')
            if path.is_file():
                paths.append(path.relative_to(self.kit).as_posix())
        paths.extend(name for name in base['files'] if not name.startswith('.agent/'))
        entries, total = [], 0
        policy_preview = None
        for name in dict.fromkeys(paths):
            raw = self.read(name)
            if raw is None or len(raw) > 8 * 1024 * 1024:
                raise Blocked('Migration input is missing or exceeds the per-file budget')
            total += len(raw)
            if total > MAX_TOTAL or len(entries) >= 5000:
                raise Blocked('Migration inventory exceeds the bounded plan budget')
            target = mapped(name)
            if target == JOURNAL:
                raise Conflict('An existing migration control path needs explicit recovery review')
            desired = translated(name, raw) if name in base['files'] or name.startswith(('.agent/context/', '.agent/state/checkpoints/')) else raw
            if target != name and (self.kit / target).exists():
                raise Conflict('Migration destination is occupied: ' + target)
            if self.boundaries == self.kit / name:
                value = strict_json(json_bytes(self.access.data))
                for resource in value['resources']['local']:
                    old = str(self.kit / '.agent').replace('\\', '/')
                    given = resource['path'].replace('\\', '/')
                    if given == old or given.startswith(old + '/'):
                        resource['path'] = str(self.kit / '.agents').replace('\\', '/') + given[len(old):]
                from update_kit import INIT
                desired = INIT.yaml.safe_dump(value, sort_keys=False).encode()
                errors, _ = INIT.validate_document(value)
                if errors:
                    raise Blocked('Proposed relocated policy fails validation')
                policy_preview = {'from': str(self.boundaries), 'to': str(self.kit / target), 'before': self.access.data, 'after': value}
            if target != name or desired != raw:
                entries.append({'from': name, 'to': target, 'before': sha(raw), 'after': sha(desired), 'content_changes': desired != raw,
                                'original': base64.b64encode(raw).decode(), 'desired': base64.b64encode(desired).decode()})
        # The active policy moves last; subsequent operations reload its approved location.
        entries.sort(key=lambda item: self.boundaries == self.kit / item['from'])
        body = {'schema_version': 1, 'from_layout': 2, 'to_layout': 3, 'kit': str(self.kit),
                'baseline_identity': base['identity'], 'baseline_manifest_sha256': sha(base['manifest_raw']),
                'entries': entries, 'policy_preview': policy_preview,
                'next_action': 'Verify migration, then make a separate release-update preview/request; host integration is separately approved.'}
        if len(json_bytes(body)) > 6 * 1024 * 1024:
            raise Blocked('Migration plan exceeds the recoverable journal budget; review a bounded migration separately')
        return {'status': 'migration_approval_required', **body, 'plan_sha256': sha(json_bytes(body))}

    @staticmethod
    def public(plan):
        return {**plan, 'entries': [{key: value for key, value in item.items() if key not in {'original', 'desired'}} for item in plan.get('entries', [])]}

    def apply(self, plan, *, approved=False, expected_sha=None, policy_reviewed=False, recovering=False, after_move=None):
        if not approved or expected_sha != plan.get('plan_sha256'):
            raise Blocked('Approve the concrete migration plan and pin its hash')
        body = {key: value for key, value in plan.items() if key not in {'status', 'plan_sha256'}}
        if sha(json_bytes(body)) != expected_sha or body.get('kit') != str(self.kit):
            raise Conflict('Migration plan is not the reviewed plan for this kit')
        if plan.get('policy_preview') and not policy_reviewed:
            raise Blocked('Review the exact policy relocation preview before migration')
        for item in plan['entries']:
            if (not item['from'].startswith('.agent/') and item['from'] not in (GUIDANCE | {'.agent/instructions.md'})) or '.git' in Path(item['from']).parts:
                raise Conflict('Migration cannot target host content or version-control data')
            for key in ('from', 'to'):
                from release_format import safe_path
                safe_path(item[key])
                no_links(self.kit / item[key])
            if mapped(item['from']) != item['to'] or sha(base64.b64decode(item['original'])) != item['before'] or sha(base64.b64decode(item['desired'])) != item['after']:
                raise Conflict('Migration path or bytes do not match its bounded transformation')
            source, target = self.kit / item['from'], self.kit / item['to']
            self.access.require(source)
            self.access.require(target)
            self.access.require(target, 'modify' if source == target else 'create')
            if item['content_changes']:
                self.access.require(source, 'modify')
                self.access.require(target, 'modify')
            if source != target:
                self.access.require(source, 'delete')
            parent = target.parent
            while not parent.exists():
                self.access.require(parent, 'create')
                parent = parent.parent
            raw = self.access.read(target if recovering and not source.exists() else source)
            if raw is None or sha(raw) not in ({item['before'], item['after']} if recovering else {item['before']}):
                raise Conflict('Concurrent migration input changed; preserved: ' + item['from'])
        old_area = self.kit / '.agent'
        for directory in ([old_area] + [p for p in old_area.rglob('*') if p.is_dir()]) if old_area.exists() else []:
            self.access.require(directory, 'delete')
        journal = {'schema_version': 1, 'phase': 'applying', 'plan': plan, 'completed': [], 'created_at': datetime.now(timezone.utc).isoformat()}
        self.write_control(journal)
        try:
            for item in plan['entries']:
                source, target = self.kit / item['from'], self.kit / item['to']
                current = self.access.read(target) if source == target or not source.exists() else self.access.read(source)
                if recovering and current is not None and sha(current) == item['after'] and (source == target or not source.exists()):
                    journal['completed'].append(item['to'])
                    continue
                if current is None or sha(current) != item['before'] or (source != target and target.exists()):
                    raise Conflict('Concurrent edit during migration; preserve both paths')
                self.access.require(target, 'modify' if source == target else 'create')
                parent = target.parent
                while not parent.exists():
                    self.access.require(parent, 'create')
                    parent = parent.parent
                target.parent.mkdir(parents=True, exist_ok=True)
                if source != target:
                    self.access.require(source, 'delete')
                    source.rename(target)
                # This is a preflighted write to the just-moved original, not candidate code execution.
                if target.read_bytes() != base64.b64decode(item['original']):
                    raise Conflict('Moved file changed concurrently')
                if item['content_changes']:
                    target.write_bytes(base64.b64decode(item['desired']))
                if self.boundaries == source:
                    self.boundaries = target
                    self.access = Access(target, self.approvals)
                if sha(target.read_bytes()) != item['after']:
                    raise Conflict('Migrated bytes failed verification')
                journal['completed'].append(item['to'])
                self.write_control(journal)
                if after_move:
                    after_move(item['to'])
            old = self.kit / '.agent'
            directories = sorted((path for path in old.rglob('*') if path.is_dir()), key=lambda p: len(p.parts), reverse=True) if old.exists() else []
            for directory in directories + ([old] if old.exists() else []):
                if not any(directory.iterdir()):
                    self.access.require(directory, 'delete')
                    directory.rmdir()
            if old.exists() or any(sha((self.kit / item['to']).read_bytes()) != item['after'] for item in plan['entries']):
                raise Conflict('Migration did not reach one verified namespace')
            journal['phase'] = 'verified'
            self.write_control(journal)
            return {'status': 'migrated', 'journal': str(self.kit / JOURNAL), 'release_update': 'pending', 'boundaries': str(self.boundaries) if self.boundaries else None,
                    'next_action': 'release_update_preview' if self.boundaries else 'init_required_before_release_update',
                    'agent_home': str(self.kit / '.agents'), 'proposed_boundaries': str(self.kit / '.agents/config/BOUNDARIES.yaml') if self.boundaries is None else None}
        except Exception:
            journal['phase'] = 'recovery_required'
            self.write_control(journal)
            raise

    def recover(self, *, approved=False, policy_reviewed=False, expected_sha=None):
        raw = self.read(JOURNAL)
        if raw is None:
            raise Blocked('No migration journal exists')
        value = strict_json(raw)
        if value.get('phase') == 'verified':
            return {'status': 'migrated', 'release_update': 'pending'}
        return self.apply(value['plan'], approved=approved, expected_sha=expected_sha, policy_reviewed=policy_reviewed, recovering=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, required=True)
    parser.add_argument('--boundaries', type=Path)
    parser.add_argument('--source')
    parser.add_argument('--repository')
    parser.add_argument('--bootstrap-approved', action='store_true')
    parser.add_argument('--approve', action='append', default=[])
    parser.add_argument('--baseline-version')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--recover', action='store_true')
    parser.add_argument('--migration-approved', action='store_true')
    parser.add_argument('--policy-reviewed', action='store_true')
    parser.add_argument('--expected-plan-sha')
    args = parser.parse_args()
    try:
        root = absolute(args.project_root)
        selected = discover(root, args.boundaries)
        if selected:
            access = Access(selected, args.approve)
            remote = next((item for item in access.data['resources']['remote'] if item['id'] == args.source), None)
            if not remote or remote['access']['status'] not in {'ready', 'limited'} or remote['effective_mode'] not in {'read', 'write'} or access.data['version_control']['operations']['inspect'] != 'act':
                raise Blocked('Select an approved readable release source through Init')
            repository = repository_identity(remote['url'])
        else:
            if not args.bootstrap_approved or not args.repository:
                raise Blocked('No policy: authorize the exact release source and existing kit migration')
            access, repository = BootstrapAccess(root), args.repository
        source = GitHubSource(repository, authorize=lambda: access.require(root / 'Agents'))
        migrator = Migrator(root, access, source, selected, args.approve)
        if args.recover:
            result = migrator.recover(approved=args.migration_approved, policy_reviewed=args.policy_reviewed, expected_sha=args.expected_plan_sha)
        else:
            plan = migrator.plan(args.baseline_version)
            result = migrator.apply(plan, approved=args.migration_approved, expected_sha=args.expected_plan_sha, policy_reviewed=args.policy_reviewed) if args.apply else migrator.public(plan)
        print(json_bytes(result).decode())
        return 0
    except (ValueError, RuntimeError, OSError, KeyError) as exc:
        print(json_bytes({'status': 'migration_blocked', 'reason': str(exc)}).decode())
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
