"""Observable routing decisions using approved profiles and host capabilities."""
from contextlib import redirect_stdout
from copy import deepcopy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

SKILL = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('orchestrator_route', SKILL / 'scripts/route.py')
routing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(routing)


class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.config = routing.load_config()

    def test_search_starts_at_approved_routine_model_and_effort(self):
        result = routing.route(self.config, 'search')
        self.assertEqual((result['profile'], result['model'], result['effort']), ('Routine', 'gpt-6-luna', 'low'))
        self.assertFalse(result['capabilities_checked'])
        self.assertEqual(result['automatic_escalations_used'], 0)

    def test_all_other_distributable_workflows_have_defaults(self):
        skills = SKILL.parent
        expected = {folder.name for folder in skills.iterdir() if (folder / 'SKILL.md').is_file()} - {'orchestrator'}
        self.assertEqual(set(self.config['skill_profiles']), expected)

    def test_implementation_and_refinement_route_differently(self):
        self.assertEqual(routing.route(self.config, 'implement')['profile'], 'Standard')
        self.assertEqual(routing.route(self.config, 'refine')['profile'], 'Demanding')

    def test_complex_search_can_select_stronger_initial_profile(self):
        result = routing.route(self.config, 'search', profile='Demanding')
        self.assertEqual(result['model'], 'gpt-6.2-astra')
        self.assertEqual(result['automatic_escalations_used'], 0)

    def test_standard_requires_known_unused_escalation(self):
        for count in (None, 1):
            with self.subTest(count=count), self.assertRaises(routing.RouteError):
                routing.route(self.config, 'implement', escalate_from='Standard', used_escalations=count)

    def test_standard_escalates_once_to_demanding(self):
        result = routing.route(self.config, 'implement', escalate_from='Standard', used_escalations=0)
        self.assertEqual((result['profile'], result['effort'], result['automatic_escalations_used']), ('Demanding', 'high', 1))

    def test_routine_can_skip_to_suitable_stronger_profile(self):
        result = routing.route(self.config, 'search', escalate_from='Routine', profile='Demanding', used_escalations=0)
        self.assertEqual(result['profile'], 'Demanding')

    def test_demanding_escalates_effort_on_same_model(self):
        initial = routing.route(self.config, 'smokes')
        result = routing.route(self.config, 'smokes', escalate_from='Demanding', used_escalations=0)
        self.assertEqual(result['model'], initial['model'])
        self.assertEqual(result['effort'], 'xhigh')

    def test_replacement_cannot_receive_second_automatic_escalation(self):
        with self.assertRaises(routing.RouteError):
            routing.route(self.config, 'implement', escalate_from='Demanding', used_escalations=1)

    def test_escalation_cannot_be_downgrade_or_reset(self):
        with self.assertRaises(routing.RouteError):
            routing.route(self.config, 'refine', escalate_from='Demanding', profile='Standard', used_escalations=0)
        with self.assertRaises(routing.RouteError):
            routing.route(self.config, 'implement', used_escalations=1)

    def test_unsupported_host_route_is_blocked_without_fallback(self):
        result = routing.route(self.config, 'search', capabilities={'gpt-6.2-sol': ['medium']})
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['proposed_route']['profile'], 'Routine')

    def test_supported_host_route_is_confirmed(self):
        result = routing.route(self.config, 'search', capabilities={'gpt-6-luna': ['low']})
        self.assertEqual(result['status'], 'ready')
        self.assertTrue(result['capabilities_checked'])

    def test_host_without_xhigh_blocks_demanding_escalation(self):
        result = routing.route(self.config, 'smokes', escalate_from='Demanding', used_escalations=0, capabilities={'gpt-6.2-astra': ['high']})
        self.assertEqual(result['status'], 'blocked')

    def test_new_local_skill_needs_explicit_profile(self):
        with self.assertRaises(routing.RouteError):
            routing.route(self.config, 'local-lore')
        self.assertEqual(routing.route(self.config, 'local-lore', profile='Standard')['profile'], 'Standard')

    def test_new_local_demanding_assignment_can_escalate_effort(self):
        initial = routing.route(self.config, 'local-lore', profile='Demanding')
        model = initial['model']
        available = {model: ['high', 'xhigh']}
        route = routing.route(self.config, 'local-lore', escalate_from=initial['profile'],
                              used_escalations=0, capabilities=available)
        self.assertEqual((route['status'], route['model'], route['effort'], route['automatic_escalations_used']),
                         ('ready', model, 'xhigh', 1))
        unsupported = routing.route(self.config, 'local-lore', escalate_from=initial['profile'],
                                    used_escalations=0, capabilities={model: ['high']})
        self.assertEqual(unsupported['status'], 'blocked')
        with self.assertRaises(routing.RouteError):
            routing.route(self.config, 'local-lore', escalate_from=initial['profile'],
                          used_escalations=route['automatic_escalations_used'], capabilities=available)

    def cli(self, *arguments):
        with redirect_stdout(io.StringIO()) as stdout:
            status = routing.main(arguments)
        return status, json.loads(stdout.getvalue())

    def test_cli_escalation_requires_known_unused_count(self):
        initial_status, initial = self.cli('--skill', 'implement')
        self.assertEqual((initial_status, initial['automatic_escalations_used']), (0, 0))
        args = ('--skill', 'implement', '--escalate-from', 'Standard')
        for suffix, expected in (((), 2), (('--used-escalations', '0'), 0), (('--used-escalations', '1'), 2)):
            with self.subTest(suffix=suffix):
                status, result = self.cli(*args, *suffix)
                self.assertEqual(status, expected)
                if expected == 0:
                    self.assertEqual((result['profile'], result['automatic_escalations_used']), ('Demanding', 1))
                else:
                    self.assertEqual(result['status'], 'error')

    def test_cli_capability_option_requires_object_when_present(self):
        args = ('--skill', 'search')
        status, result = self.cli(*args)
        self.assertEqual((status, result['status'], result['capabilities_checked']), (0, 'ready', False))
        status, result = self.cli(*args, '--capabilities', 'null')
        self.assertEqual((status, result['status']), (2, 'error'))
        status, result = self.cli(*args, '--capabilities', '{}')
        self.assertEqual((status, result['status']), (3, 'blocked'))
        status, result = self.cli(*args, '--capabilities', '{"gpt-6-luna":["low"]}')
        self.assertEqual((status, result['status'], result['capabilities_checked']), (0, 'ready', True))

    def test_disabling_automatic_escalation_is_respected(self):
        self.config['max_automatic_escalations'] = 0
        with self.assertRaises(routing.RouteError):
            routing.route(self.config, 'search', escalate_from='Routine', used_escalations=0)

    def test_configuration_does_not_accept_permission_fields(self):
        self.config['elevated_rights'] = True
        with self.assertRaises(routing.RouteError):
            routing.validate_config(self.config)

    def test_configuration_cannot_raise_automatic_limit(self):
        self.config['max_automatic_escalations'] = 2
        with self.assertRaises(routing.RouteError):
            routing.validate_config(self.config)

    def test_duplicate_mapping_and_yaml_references_are_rejected(self):
        original = routing.DEFAULT_CONFIG.read_text(encoding='utf-8')
        for raw in (original + '\nskill_profiles: {}\n', original.replace('profiles:', 'profiles: &shared', 1)):
            with tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / 'profiles.yaml'
                path.write_text(raw, encoding='utf-8')
                with self.assertRaises(routing.RouteError):
                    routing.load_config(path)

    def test_routing_has_no_side_effect_on_configuration(self):
        previous = deepcopy(self.config)
        routing.route(self.config, 'search')
        self.assertEqual(self.config, previous)


if __name__ == '__main__':
    unittest.main()
