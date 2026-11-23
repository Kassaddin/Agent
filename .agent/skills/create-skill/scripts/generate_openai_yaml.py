#!/usr/bin/env python3
"""Adapted from Codex Skill Creator on 2026-11-23; see ../NOTICE.txt and ../license.txt.

Modified for project-bound reads, preview, exclusive creation, UTF-8, and no
replacement of existing metadata/policy/dependency fields.
"""
from __future__ import annotations
import argparse
import json
import re
from project_access import LocalSkills, add_context, run, skill_name, Blocked, INIT
from release_format import safe_path

ALLOWED = {'display_name', 'short_description', 'default_prompt', 'icon_small', 'icon_large', 'brand_color'}
ACRONYMS = {'GH', 'MCP', 'API', 'CI', 'CLI', 'LLM', 'PDF', 'PR', 'UI', 'URL', 'SQL'}
BRANDS = {'openai': 'OpenAI', 'openapi': 'OpenAPI', 'github': 'GitHub', 'sqlite': 'SQLite', 'fastapi': 'FastAPI'}


def format_display_name(name):
    words = []
    for word in name.split('-'):
        words.append(word.upper() if word.upper() in ACRONYMS else BRANDS.get(word, word.capitalize()))
    return ' '.join(words)


def render_metadata(name, overrides=()):
    skill_name(name)
    values = {}
    for override in overrides:
        key, separator, value = override.partition('=')
        if not separator or key not in ALLOWED or not value.strip() or key in values:
            raise ValueError('Use unique supported interface fields in key=value form')
        values[key] = value
    display = values.get('display_name', format_display_name(name))
    description = values.get('short_description', f'Help with {display} tasks and workflows'[:64].rstrip())
    if not 25 <= len(description) <= 64:
        raise ValueError('short_description must have 25-64 characters')
    prompt = values.get('default_prompt')
    if prompt is not None and f'${name}' not in prompt:
        raise ValueError('default_prompt must mention the skill as $' + name)
    for key in ('icon_small', 'icon_large'):
        if key in values:
            safe_path(values[key].removeprefix('./'))
    if 'brand_color' in values and not re.fullmatch('#[0-9A-Fa-f]{6}', values['brand_color']):
        raise ValueError('brand_color must be a six-digit hexadecimal color')
    interface = {'display_name': display, 'short_description': description}
    interface.update({key: value for key, value in values.items() if key not in interface})
    return ('interface:\n' + ''.join(f'  {key}: {json.dumps(value, ensure_ascii=False)}\n' for key, value in interface.items())).encode('utf-8')


def generate(context, name, *, overrides=(), apply=False, notified=False):
    folder = context.skill(name)
    raw = context.read(folder / 'SKILL.md')
    if raw is None:
        raise Blocked('Create the skill instructions before its metadata')
    match = re.match(r'^---\r?\n(.*?)\r?\n---(?:\r?\n|$)', raw.decode('utf-8-sig'), re.S)
    front = INIT.load_yaml(match[1]) if match else None
    if not isinstance(front, dict) or front.get('name') != name:
        raise ValueError('Skill frontmatter must match its directory name')
    target = folder / 'agents/openai.yaml'
    metadata = render_metadata(name, overrides)
    context.preflight([target])
    result = {'status': 'ready', 'skill': str(folder), 'create': [str(target)], 'note': 'Existing metadata is never replaced; edit requested fields directly.'}
    if apply:
        context.notify_required(notified)
        context.create(target, metadata)
        result['status'] = 'metadata_created'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name')
    add_context(parser)
    parser.add_argument('--interface', action='append', default=[])
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--notified', action='store_true')
    args = parser.parse_args()
    return run(lambda: generate(LocalSkills.from_args(args), args.name, overrides=args.interface, apply=args.apply, notified=args.notified))


if __name__ == '__main__':
    raise SystemExit(main())
