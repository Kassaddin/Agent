#!/usr/bin/env python3
"""Adapted from Codex Skill Creator on 2026-11-23; see ../NOTICE.txt and ../license.txt.

Modified for scoped read-only validation, strict UTF-8/YAML, complete metadata,
local dependency checks, unfinished scaffold detection, and syntax-only Python QA.
"""
from __future__ import annotations
import argparse
import ast
import os
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
from project_access import LocalSkills, add_context, run, no_links, INIT
from update_kit import markdown_links, heading_anchors

ALLOWED = {'name', 'description', 'license', 'allowed-tools', 'metadata'}


def validate_skill(context, name):
    folder = context.skill(name)
    errors, warnings = [], []
    raw = context.read(folder / 'SKILL.md')
    if raw is None:
        return {'status': 'invalid', 'errors': ['SKILL.md is missing'], 'warnings': []}
    text = raw.decode('utf-8-sig')
    match = re.match(r'^---\r?\n(.*?)\r?\n---(?:\r?\n|$)', text, re.S)
    if not match:
        return {'status': 'invalid', 'errors': ['A YAML frontmatter block is required'], 'warnings': []}
    front = INIT.load_yaml(match[1])
    if not isinstance(front, dict) or set(front) - ALLOWED:
        return {'status': 'invalid', 'errors': ['Unsupported skill frontmatter fields'], 'warnings': []}
    if front.get('name') != name:
        errors.append('Frontmatter name must match the skill directory')
    description = front.get('description')
    if not isinstance(description, str) or not description.strip() or len(description) > 1024 or any(value in description for value in '<>'):
        errors.append('Use a nonempty plain-text description of at most 1024 characters')
    elif description.strip().startswith('[TODO:'):
        errors.append('Description is an unfinished scaffold')
    body = text[match.end():]
    if not body.strip():
        errors.append('Skill instructions are empty')
    fenced = None
    for line in body.splitlines():
        fence = re.match(r'^[ \t]*(?:(?:[-+*]|\d+[.)])[ \t]+)?(`{3,}|~{3,})(.*)$', line)
        if fence:
            marker = fence[1]
            if fenced is None:
                fenced = (marker[0], len(marker))
            elif marker[0] == fenced[0] and len(marker) >= fenced[1] and not fence[2].strip():
                fenced = None
            continue
        if fenced is None and re.fullmatch(r'\s*\[TODO:[^\n]*\]\s*', line):
            errors.append('Instructions contain an unfinished scaffold')
    metadata_raw = context.read(folder / 'agents/openai.yaml')
    if metadata_raw is not None:
        metadata = INIT.load_yaml(metadata_raw.decode('utf-8-sig'))
        interface = metadata.get('interface') if isinstance(metadata, dict) else None
        if not isinstance(interface, dict) or not isinstance(interface.get('display_name'), str) or not interface['display_name'].strip():
            errors.append('Metadata requires a display_name')
        else:
            short = interface.get('short_description')
            if not isinstance(short, str) or not 25 <= len(short) <= 64:
                errors.append('Metadata short_description must have 25-64 characters')
            prompt = interface.get('default_prompt')
            if prompt is not None and (not isinstance(prompt, str) or '$' + name not in prompt):
                errors.append('Metadata default_prompt must mention $' + name)
            for key in ('icon_small', 'icon_large'):
                if interface.get(key):
                    if not isinstance(interface[key], str):
                        errors.append('Metadata icon path must be a string: ' + key)
                        continue
                    target = folder / interface[key]
                    context.access.require(target)
                    no_links(target)
                    if not target.is_file():
                        errors.append('Metadata icon target is missing: ' + key)
    for path in context.files(folder):
        if path.suffix == '.py':
            try:
                ast.parse(context.read(path), filename=path.relative_to(folder).as_posix())
            except (SyntaxError, UnicodeError, ValueError):
                errors.append('Python syntax is invalid: ' + path.relative_to(folder).as_posix())
        if path.suffix != '.md':
            continue
        content = context.read(path).decode('utf-8-sig')
        for _, link, _ in markdown_links(content):
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc:
                warnings.append('External reference not checked: ' + link)
                continue
            target = Path(path.parent / unquote(parsed.path)) if parsed.path else path
            target = Path(os.path.abspath(target))
            context.access.require(target)
            no_links(target)
            if not target.is_file():
                errors.append('Local reference is missing: ' + link)
            elif parsed.fragment and target.suffix == '.md' and unquote(parsed.fragment) not in heading_anchors(context.read(target).decode('utf-8-sig'))[0]:
                errors.append('Local reference heading is missing: ' + link)
    return {'status': 'invalid' if errors else 'valid', 'skill': str(folder), 'errors': list(dict.fromkeys(errors)), 'warnings': list(dict.fromkeys(warnings)),
            'limits': 'No generated code was executed; remote references and semantic correctness are not verified. Generated/dependency folders are excluded.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name')
    add_context(parser)
    args = parser.parse_args()
    return run(lambda: validate_skill(LocalSkills.from_args(args), args.name))


if __name__ == '__main__':
    raise SystemExit(main())
