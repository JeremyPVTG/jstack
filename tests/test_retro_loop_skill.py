"""The repo-local retro-loop skill: outside every pack, routing kept local, PR templates the hook accepts."""
from pathlib import Path
import importlib.util
import json
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / '.claude' / 'skills' / 'retro-loop'
TRACKED = [SKILL / 'SKILL.md', *sorted((SKILL / 'references').glob('*.md')), SKILL / 'config.example.json']
spec = importlib.util.spec_from_file_location('retro_loop', ROOT / 'scripts' / 'retro_loop.py')
rl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rl)

# The sections the owner's PR hook requires in a gh pr create or body edit.
PR_SECTIONS = ['## Summary', '## Evidence', '**Before:**', '**After:**', '## Merge Danger', '**Door:**',
               '**Blast Radius:**']


class LoopSkill(unittest.TestCase):
    def test_skill_is_repo_local_and_in_no_pack(self):
        text = (SKILL / 'SKILL.md').read_text()
        match = re.match(r'---\nname: ([a-z0-9-]+)\ndescription: ([^\n]+)\n---\n', text)
        self.assertTrue(match)
        self.assertEqual(match.group(1), 'retro-loop')
        self.assertLessEqual(len(match.group(2)), 1024)
        self.assertFalse((ROOT / 'skills' / 'retro-loop').exists())
        packs = json.loads((ROOT / 'packs.json').read_text())
        self.assertFalse([pack for pack, names in packs.items() if 'retro-loop' in names])

    def test_no_argument_placeholders_claude_code_would_substitute(self):
        for path in TRACKED:
            self.assertFalse(re.search(r'\$(\d|ARGUMENTS)', path.read_text()), path)

    def test_local_config_and_kill_switch_are_gitignored(self):
        for rel in ('.claude/skills/retro-loop/config.local.json', rl.KILL_SWITCH):
            done = subprocess.run(['git', '-C', str(ROOT), 'check-ignore', '-q', rel])
            self.assertEqual(done.returncode, 0, rel)

    def test_example_config_has_every_role_and_only_placeholder_provider_instances(self):
        config = json.loads((SKILL / 'config.example.json').read_text())
        self.assertEqual(set(config['paths']), {'jstack', 'evals', 'work'})
        roles = config['roles']
        self.assertEqual(set(roles), {'triage', 'eval_author', 'implementer', 'judges'})
        targets = [roles['triage'], roles['eval_author'], roles['implementer'], *roles['judges']]
        self.assertEqual(len(roles['judges']), 2)
        for target in targets:
            self.assertEqual(set(target), {'providerInstanceId', 'model', 'options'})
            self.assertRegex(target['providerInstanceId'], r'^<[^<>]+>$')

    def test_tracked_skill_files_name_no_provider_instance_from_the_local_config(self):
        local = SKILL / 'config.local.json'
        if not local.exists():
            self.skipTest('no config.local.json on this machine')
        roles = json.loads(local.read_text())['roles']
        ids = {t['providerInstanceId'] for t in [roles['triage'], roles['eval_author'], roles['implementer'],
                                                 *roles['judges']]}
        for path in TRACKED:
            text = path.read_text()
            self.assertFalse([i for i in ids if i in text], path)

    def test_runner_commands_the_skill_names_exist(self):
        text = '\n'.join(p.read_text() for p in TRACKED[:-1])
        named = set(re.findall(r'`(triage|freeze|reproduce|implement|gate|settle|handoff|spend) <N>', text))
        named |= {'next', 'check-in', 'ensure-labels', 'ledger'}
        commands = rl.parser()._subparsers._group_actions[0].choices
        self.assertGreaterEqual(len(named), 10)
        self.assertEqual(named - set(commands), set())

    def test_the_implementer_brief_gives_the_finding_body_and_points_at_no_eval_material(self):
        text = (SKILL / 'references' / 'briefs.md').read_text()
        brief = re.search(r'^## Implementer\n\n```text\n(.*?)^```$', text, re.S | re.M).group(1)
        self.assertIn('<issue title and body>', brief)
        for forbidden in ('comments', 'jstack-evals', 'run directories'):
            self.assertIn(forbidden, brief)
        for placeholder in ('<work>', '<evals>', '<judges bundle>'):
            self.assertNotIn(placeholder, brief)

    def test_every_reproduce_and_gate_outcome_gets_a_record_pr_and_only_accepted_gets_a_skill_pr(self):
        skill = (SKILL / 'SKILL.md').read_text()
        pair = (SKILL / 'references' / 'pr-pair.md').read_text()
        for step in ('reproduce', 'gate'):
            section = re.search(rf'^### {step}\n(.*?)(?=^### )', skill, re.S | re.M).group(1)
            self.assertIn('references/pr-pair.md#1-experiment-record-every-outcome', section)
        self.assertIn('harness/retro-loop/record.py', pair)
        self.assertIn('harness/retro-loop/records/<N>/', pair)
        self.assertNotIn('experiments/', pair)
        self.assertRegex(pair, r'(?m)^## 1\. Experiment record \(every outcome\)$')
        self.assertRegex(pair, r'(?m)^## 2\. Skill change \(accepted only\)$')

    def test_pr_body_templates_carry_the_sections_the_pr_hook_requires(self):
        text = (SKILL / 'references' / 'pr-pair.md').read_text()
        bodies = [b for b in re.findall(r'^````markdown\n(.*?)^````$', text, re.S | re.M) if '## Summary' in b]
        self.assertEqual(len(bodies), 2)
        for body in bodies:
            self.assertEqual([s for s in PR_SECTIONS if s not in body], [])
            self.assertNotRegex(body, r'(?i)co-authored-by|generated with|closes #|fixes #')


if __name__ == '__main__':
    unittest.main()
