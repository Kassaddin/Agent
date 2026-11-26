"""Resolve approved worker profiles; no dispatch, permission changes, or writes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import yaml

PROFILE_ORDER = ('Routine', 'Standard', 'Demanding')
EFFORT_ORDER = ('low', 'medium', 'high', 'xhigh', 'max', 'ultra')
MAX_CANDIDATES = 8
DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / 'references/profiles.yaml'


class RouteError(ValueError):
    pass


class StrictLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if not isinstance(key, str) or key in mapping:
            raise RouteError('Profile YAML requires unique string keys')
        mapping[key] = loader.construct_object(value_node)
    return mapping


StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def validate_config(data):
    if not isinstance(data, dict) or set(data) != {'schema_version', 'max_automatic_escalations', 'profiles', 'skill_profiles'}:
        raise RouteError('Unsupported profile configuration fields')
    if type(data['schema_version']) is not int or data['schema_version'] != 2:
        raise RouteError('Unsupported profile configuration version')
    limit = data['max_automatic_escalations']
    if type(limit) is not int or not 0 <= limit <= 1:
        raise RouteError('At most one automatic escalation is supported')
    profiles = data['profiles']
    if not isinstance(profiles, dict) or set(profiles) != set(PROFILE_ORDER):
        raise RouteError('Configure Routine, Standard, and Demanding profiles')
    for name, profile in profiles.items():
        if not isinstance(profile, dict) or set(profile) != {'candidates'}:
            raise RouteError('Invalid profile fields')
        candidates = profile['candidates']
        if not isinstance(candidates, list) or not 1 <= len(candidates) <= MAX_CANDIDATES:
            raise RouteError('Each profile needs an ordered list of candidate models')
        models = set()
        for candidate in candidates:
            keys = {'model', 'effort'}
            if not isinstance(candidate, dict) or not keys <= set(candidate) or set(candidate) - keys - {'escalated_effort'}:
                raise RouteError('Invalid candidate fields')
            if not isinstance(candidate['model'], str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]*', candidate['model']):
                raise RouteError('Invalid model identifier')
            if candidate['model'] in models:
                raise RouteError('Candidate models must be unique within a profile')
            models.add(candidate['model'])
            if candidate['effort'] not in EFFORT_ORDER:
                raise RouteError('Invalid initial effort')
            if 'escalated_effort' in candidate:
                effort = candidate['escalated_effort']
                if name != 'Demanding' or effort not in EFFORT_ORDER or EFFORT_ORDER.index(effort) <= EFFORT_ORDER.index(candidate['effort']):
                    raise RouteError('Only Demanding supports a higher configured escalation effort')
    mapping = data['skill_profiles']
    if not isinstance(mapping, dict) or not mapping:
        raise RouteError('A skill profile mapping is required')
    for skill, name in mapping.items():
        if not isinstance(skill, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', skill) or name not in PROFILE_ORDER:
            raise RouteError('Invalid skill profile mapping')
    return data


def load_config(path=DEFAULT_CONFIG):
    raw = Path(path).read_text(encoding='utf-8-sig')
    if len(raw.encode('utf-8')) > 65536:
        raise RouteError('Profile configuration exceeds 64 KiB')
    for token in yaml.scan(raw):
        if isinstance(token, (yaml.tokens.AnchorToken, yaml.tokens.AliasToken, yaml.tokens.TagToken)):
            raise RouteError('Profile YAML cannot use anchors, aliases, or tags')
    return validate_config(yaml.load(raw, Loader=StrictLoader))


def route(config, skill, *, profile=None, escalate_from=None, used_escalations=None, capabilities=None, current_model=None):
    validate_config(config)
    if not isinstance(skill, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', skill):
        raise RouteError('A canonical skill or assignment name is required')
    limit = config['max_automatic_escalations']
    if used_escalations is not None and (type(used_escalations) is not int or not 0 <= used_escalations <= limit):
        raise RouteError('Invalid assignment escalation count')
    if profile is not None and profile not in PROFILE_ORDER:
        raise RouteError('Unknown requested profile')
    if escalate_from is not None and escalate_from not in PROFILE_ORDER:
        raise RouteError('Unknown current profile')
    if escalate_from is None:
        if used_escalations:
            raise RouteError('Resume the existing route; do not reset an escalated assignment')
        name = profile or config['skill_profiles'].get(skill)
        if name is None:
            raise RouteError('Unmapped work requires an explicitly selected approved profile')
        used_escalations = 0
    else:
        if used_escalations is None:
            raise RouteError('Automatic escalation requires a known assignment escalation count')
        if used_escalations >= limit:
            raise RouteError('Automatic escalation exhausted for this assignment')
        previous = PROFILE_ORDER.index(escalate_from)
        if profile is not None:
            if PROFILE_ORDER.index(profile) <= previous:
                raise RouteError('An explicit escalation must select a stronger profile')
            name = profile
        elif previous < len(PROFILE_ORDER) - 1:
            name = PROFILE_ORDER[previous + 1]
        else:
            name = escalate_from
        used_escalations += 1
    escalate_effort = name == escalate_from
    if escalate_effort and (not isinstance(current_model, str) or not current_model):
        raise RouteError('Demanding effort escalation requires the current worker model')
    options = []
    for candidate in config['profiles'][name]['candidates']:
        if escalate_effort and candidate['model'] != current_model:
            continue
        effort = candidate.get('escalated_effort') if escalate_effort else candidate['effort']
        if effort is not None:
            options.append((candidate['model'], effort))
    if not options:
        raise RouteError('No stronger configured route is available')

    def describe(option):
        return {'skill': skill, 'profile': name, 'model': option[0],
                'effort': option[1], 'automatic_escalations_used': used_escalations}

    if capabilities is None:
        return {'status': 'ready', 'capabilities_checked': False, **describe(options[0])}
    if not isinstance(capabilities, dict) or any(not isinstance(model, str) or not isinstance(efforts, list) or not all(isinstance(value, str) for value in efforts) for model, efforts in capabilities.items()):
        raise RouteError('Capabilities must map host model IDs to supported effort lists')
    for option in options:
        if option[1] in capabilities.get(option[0], []):
            return {'status': 'ready', 'capabilities_checked': True, **describe(option)}
    return {'status': 'blocked', 'reason': 'No candidate model/effort is supported by supplied host capabilities',
            'proposed_route': describe(options[0])}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    parser.add_argument('--skill', required=True)
    parser.add_argument('--profile', choices=PROFILE_ORDER)
    parser.add_argument('--escalate-from', choices=PROFILE_ORDER)
    parser.add_argument('--used-escalations', type=int, help='Known assignment count, required for escalation')
    parser.add_argument('--capabilities', help='JSON object supplied from actual host model/effort metadata')
    parser.add_argument('--current-model', help='Current worker model, required for Demanding effort escalation')
    args = parser.parse_args(argv)
    try:
        capabilities = None
        if args.capabilities is not None:
            capabilities = json.loads(args.capabilities)
            if not isinstance(capabilities, dict):
                raise RouteError('Capabilities must be supplied as a JSON object')
        result = route(load_config(args.config), args.skill, profile=args.profile,
                       escalate_from=args.escalate_from, used_escalations=args.used_escalations,
                       capabilities=capabilities, current_model=args.current_model)
    except (OSError, UnicodeError, ValueError, yaml.YAMLError):
        # Do not echo malformed config/JSON snippets that could contain private text.
        print(json.dumps({'status': 'error', 'reason': 'Invalid or unreadable routing input/configuration'}))
        return 2
    print(json.dumps(result))
    return 0 if result['status'] == 'ready' else 3


if __name__ == '__main__':
    raise SystemExit(main())
