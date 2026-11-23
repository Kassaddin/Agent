#!/usr/bin/env python3
"""Adapted from Codex Skill Creator on 2026-11-23; see ../NOTICE.txt and ../license.txt.

Modified for project-local defaults, boundary gates, non-writing preview, UTF-8,
exclusive scaffold creation, and explicit draft status. No examples are executed.
"""
from __future__ import annotations
import argparse
from project_access import LocalSkills, add_context, run, Blocked
from generate_openai_yaml import render_metadata, format_display_name

RESOURCES = {'scripts', 'references', 'assets'}


def initialize(context, name, *, resources=(), overrides=(), apply=False, notified=False):
    folder = context.skill(name)
    if folder.exists():
        raise Blocked('Skill folder already exists; use an authorized targeted update')
    if len(set(resources)) != len(resources) or not set(resources) <= RESOURCES:
        raise ValueError('Select only needed unique resource folders: scripts,references,assets')
    content = (f'---\nname: {name}\ndescription: "[TODO: Describe the project task and when this skill applies.]"\n---\n\n'
               f'# {format_display_name(name)}\n\n[TODO: Add the project-specific instructions and relevant source references.]\n').encode('utf-8')
    files = {folder / 'SKILL.md': content, folder / 'agents/openai.yaml': render_metadata(name, overrides)}
    directories = [folder] + [folder / resource for resource in resources]
    context.preflight(files, directories)
    result = {'status': 'ready', 'skill': str(folder), 'create': [str(path) for path in files], 'resources': list(resources),
              'note': 'This creates a draft scaffold, not a complete or host-registered skill.'}
    if not apply:
        return result
    context.notify_required(notified)
    context.mkdirs(folder.parent)
    context.check(folder, 'create')
    folder.mkdir(exist_ok=False)
    created = []
    try:
        for path, raw in files.items():
            context.create(path, raw)
            created.append(str(path))
        for path in directories[1:]:
            context.mkdirs(path)
    except Exception as exc:
        return {**result, 'status': 'incomplete', 'created': created, 'reason': str(exc),
                'note': 'Preserve and inspect this incomplete scaffold; never reinitialize it by overwriting.'}
    return {**result, 'status': 'scaffold_created', 'created': created}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name')
    add_context(parser)
    parser.add_argument('--resources', default='')
    parser.add_argument('--interface', action='append', default=[])
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--notified', action='store_true')
    args = parser.parse_args()
    resources = [value.strip() for value in args.resources.split(',') if value.strip()]
    return run(lambda: initialize(LocalSkills.from_args(args), args.name, resources=resources, overrides=args.interface, apply=args.apply, notified=args.notified))


if __name__ == '__main__':
    raise SystemExit(main())
