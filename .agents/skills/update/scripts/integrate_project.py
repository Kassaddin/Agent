"""Preview and apply one approved project guidance pointer, preserving host bytes."""
from pathlib import Path
import argparse
import os
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'init/scripts'))
from project_layout import discover_boundaries
from update_kit import Access, Blocked, Conflict
from release_format import sha, json_bytes, MANIFEST, strict_json

MARKER = b'<!-- agents-kit:v3 -->'
POINTER = MARKER + b'\nRead [Agents kit guidance](Agents/.agents/instructions.md) for project skill routing.\n'

def plan(project_root, boundaries=None, approvals=()):
    root = Path(os.path.abspath(project_root))
    policy = discover_boundaries(root, boundaries)
    if not policy.is_file():
        raise Blocked('Run Init before approving host guidance integration')
    access = Access(policy, approvals)
    path = root / 'AGENTS.md'
    access.require(path)
    for current in (path, root / 'Agents/.agents/instructions.md', root / 'Agents' / MANIFEST):
        access.require(current)
        if current.is_symlink() or (hasattr(current, 'is_junction') and current.is_junction()):
            raise Blocked('Integration cannot follow linked destinations')
    if not (root / 'Agents/.agents/instructions.md').is_file() or strict_json((root / 'Agents' / MANIFEST).read_bytes())['layout_version'] != 3:
        raise Blocked('A verified canonical project kit is required')
    raw = access.read(path)
    if raw is not None and MARKER in raw:
        if POINTER not in raw:
            raise Conflict('An existing integration marker has different content; review it')
        return {'status': 'already_integrated', 'path': str(path)}
    if raw is not None and len(raw) > 2 * 1024 * 1024:
        raise Blocked('Host instructions exceed the bounded integration size')
    current = raw or b''
    migrated = current.replace(b'Agents/.agent/', b'Agents/.agents/').replace(b'Agents/.agents/skills/context/', b'Agents/.agents/skills/project-context/')
    desired = migrated + (b'\n\n' if migrated else b'') + POINTER
    return {'status': 'approval_required', 'path': str(path), 'before_sha256': sha(raw) if raw is not None else None,
            'after_sha256': sha(desired), 'append': POINTER.decode(), 'reference_updates': ['Agents/.agent/ -> Agents/.agents/', 'Agents/.agents/skills/context/ -> Agents/.agents/skills/project-context/'] if migrated != current else [], 'before': raw, 'desired': desired, 'access': access}

def apply(preview, *, approved=False, expected_sha=None):
    if preview['status'] == 'already_integrated':
        return preview
    if not approved or expected_sha != preview['after_sha256']:
        raise Blocked('Approve the concrete host-file preview and pin its after hash')
    path, access = Path(preview['path']), preview['access']
    if access.read(path) != preview['before']:
        raise Conflict('Host instructions changed after preview')
    access.require(path, 'modify' if path.exists() else 'create')
    backup = path.parent / 'Agents/.agents/state/integration/host-original.bin'
    if preview['before'] is not None:
        access.create(backup, preview['before'])
    access.write(path, preview['desired'])
    if access.read(path) != preview['desired']:
        raise Conflict('Host pointer did not verify')
    return {'status': 'integrated', 'path': str(path), 'after_sha256': preview['after_sha256'], 'unrelated_content_preserved': True}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', required=True, type=Path)
    parser.add_argument('--boundaries', type=Path)
    parser.add_argument('--approve', action='append', default=[])
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--host-change-approved', action='store_true')
    parser.add_argument('--expected-sha')
    args = parser.parse_args()
    try:
        preview = plan(args.project_root, args.boundaries, args.approve)
        result = apply(preview, approved=args.host_change_approved, expected_sha=args.expected_sha) if args.apply else {key: value for key, value in preview.items() if key not in {'before', 'desired', 'access'}}
        print(json_bytes(result).decode())
        return 0
    except (ValueError, RuntimeError, OSError) as exc:
        print(json_bytes({'status': 'blocked', 'reason': str(exc)}).decode())
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
