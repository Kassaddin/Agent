"""Resolve approved worker profiles; no dispatch, permission changes, or writes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import yaml

PROFILE_ORDER = ('Routine', 'Standard', 'Demanding')
EFFORT_ORDER = ('low', 'medium', 'high', 'xhigh', 'max', 'ultra')
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
    if type(data['schema_version']) is not int or data['schema_version'] != 1:
        raise RouteError('Unsupported profile configuration version')
    limit = data['max_automatic_escalations']
    if type(limit) is not int or not 0 <= limit <= 1:
        raise RouteError('At most one automatic escalation is supported')
    profiles = data['profiles']
    if not isinstance(profiles, dict) or set(profiles) != set(PROFILE_ORDER):
        raise RouteError('Configure Routine, Standard, and Demanding profiles')
    for name, profile in profiles.items():
        keys = {'model', 'effort'}
        if not isinstance(profile, dict) or not keys <= set(profile) or set(profile) - keys - {'escalated_effort'}:
            raise RouteError('Invalid profile fields')
        if not isinstance(profile['model'], str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]*', profile['model']):
            raise RouteError('Invalid model identifier')
        if profile['effort'] not in EFFORT_ORDER:
            raise RouteError('Invalid initial effort')
        if 'escalated_effort' in profile:
            effort = profile['escalated_effort']
            if name != 'Demanding' or effort not in EFFORT_ORDER or EFFORT_ORDER.index(effort) <= EFFORT_ORDER.index(profile['effort']):
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


def route(config, skill, *, profile=None, escalate_from=None, used_escalations=None, capabilities=None):
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
    effort = config['profiles'][name]['effort']
    if name == escalate_from:
        effort = config['profiles'][name].get('escalated_effort')
        if effort is None:
            raise RouteError('No stronger configured route is available')
    selected = {'skill': skill, 'profile': name, 'model': config['profiles'][name]['model'],
                'effort': effort, 'automatic_escalations_used': used_escalations}
    if capabilities is not None:
        if not isinstance(capabilities, dict) or any(not isinstance(model, str) or not isinstance(efforts, list) or not all(isinstance(value, str) for value in efforts) for model, efforts in capabilities.items()):
            raise RouteError('Capabilities must map host model IDs to supported effort lists')
        if effort not in capabilities.get(selected['model'], []):
            return {'status': 'blocked', 'reason': 'Selected model/effort is not supported by supplied host capabilities',
                    'proposed_route': selected}
    return {'status': 'ready', 'capabilities_checked': capabilities is not None, **selected}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=DEFAULT_CONFIG)
    parser.add_argument('--skill', required=True)
    parser.add_argument('--profile', choices=PROFILE_ORDER)
    parser.add_argument('--escalate-from', choices=PROFILE_ORDER)
    parser.add_argument('--used-escalations', type=int, help='Known assignment count, required for escalation')
    parser.add_argument('--capabilities', help='JSON object supplied from actual host model/effort metadata')
    args = parser.parse_args(argv)
    try:
        capabilities = None
        if args.capabilities is not None:
            capabilities = json.loads(args.capabilities)
            if not isinstance(capabilities, dict):
                raise RouteError('Capabilities must be supplied as a JSON object')
        result = route(load_config(args.config), args.skill, profile=args.profile,
                       escalate_from=args.escalate_from, used_escalations=args.used_escalations,
                       capabilities=capabilities)
    except (OSError, UnicodeError, ValueError, yaml.YAMLError):
        # Do not echo malformed config/JSON snippets that could contain private text.
        print(json.dumps({'status': 'error', 'reason': 'Invalid or unreadable routing input/configuration'}))
        return 2
    print(json.dumps(result))
    return 0 if result['status'] == 'ready' else 3


if __name__ == '__main__':
    raise SystemExit(main())
