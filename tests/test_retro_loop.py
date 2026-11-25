from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import importlib.util
import json
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'retro_loop.py'
spec = importlib.util.spec_from_file_location('retro_loop', SCRIPT)
rl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rl)

FILED = ['retro-finding', 'needs-triage']
READY = ['retro-finding', 'loop:ready', 'ready-for-agent']
CASES = {
    'target': {'name': 'stale-receipts', 'sha256': 'a' * 64},
    'holdout': {'name': 'stale-receipts-reworded', 'sha256': 'b' * 64},
    'controls': [{'name': 'fresh-receipts', 'sha256': 'c' * 64}, {'name': 'one-stale-lens', 'sha256': 'd' * 64}],
}


class FakeGate:
    """Stands in for the jstack-evals gate command: returns queued outputs and remembers each manifest."""

    def __init__(self):
        self.outputs = []
        self.manifests = []

    def queue(self, outcome, cost_usd, runs, reasons=('reason',), infra_retry_used=False):
        self.outputs.append({'outcome': outcome, 'reasons': list(reasons), 'cost_usd': cost_usd, 'runs': runs,
                             'infra_retry_used': infra_retry_used, 'per_model': {}})

    def decide(self, manifest):
        self.manifests.append(json.loads(Path(manifest).read_text()))
        return self.outputs.pop(0)


class FakeGitHub:
    """In-memory stand-in for the gh adapter: issues, open pull request heads and labels."""

    def __init__(self):
        self.issues = {}
        self.prs = []  # heads of open pull requests
        self.closed_prs = {}  # head -> 'MERGED' or 'CLOSED'
        self.label_set = {'retro-finding', 'needs-triage', 'ready-for-agent', 'ready-for-human', 'wontfix'}

    def add(self, number, labels=FILED, skill='j-build', state='OPEN', reason=None):
        body = 'What the agent did, what should have happened, how to check it.\n\n'
        body += f'Owning skill: {skill}\n' if skill else ''
        self.issues[number] = {'number': number, 'title': f'Finding {number}', 'body': body, 'labels': list(labels),
                               'state': state, 'state_reason': reason, 'comments': []}

    def labels(self, number):
        return sorted(self.issues[number]['labels'])

    def findings(self):
        return [deepcopy(i) for _, i in sorted(self.issues.items()) if 'retro-finding' in i['labels'] and i['state'] == 'OPEN']

    def issue(self, number):
        if number not in self.issues:
            raise rl.GitHubError(f'issue {number} not found')
        return deepcopy(self.issues[number])

    def edit_labels(self, number, add, remove):
        issue = self.issues[number]
        issue['labels'] = [l for l in issue['labels'] if l not in remove] + [l for l in add if l not in issue['labels']]

    def comment(self, number, body):
        self.issues[number]['comments'].append(body)

    def close(self, number, reason, comment):
        issue = self.issues[number]
        issue['state'], issue['state_reason'] = 'CLOSED', {'completed': 'COMPLETED', 'not planned': 'NOT_PLANNED'}[reason]
        issue['comments'].append(comment)

    def open_pr_heads(self):
        return list(self.prs)

    def pr_state(self, head):
        return 'OPEN' if head in self.prs else self.closed_prs.get(head)

    def label_names(self):
        return set(self.label_set)

    def create_label(self, name, color, description):
        self.label_set.add(name)


class LoopTest(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.github = FakeGitHub()
        self.gate = FakeGate()
        self.clock = datetime(2026, 11, 25, 9, tzinfo=timezone.utc)
        self.runner = rl.Runner(self.github, ledger=self.dir / 'ledger.json', kill_switch=self.dir / 'loop.disabled',
                                gate=self.gate, now=lambda: self.clock)

    def manifest(self, finding=21, mode='reproduce', attempt=0, cases=CASES, infra_retry_used=False):
        path = self.dir / f'manifest-{len(list(self.dir.glob("manifest-*")))}.json'
        path.write_text(json.dumps({'mode': mode, 'finding': finding, 'owning_skill': 'j-build', 'attempt': attempt,
                                    'infra_retry_used': infra_retry_used, 'cases': cases}))
        return path

    def ready_and_frozen(self, finding=21):
        self.github.add(finding, labels=READY)
        self.runner.freeze(finding, CASES)

    def reproduced(self, finding=21):
        self.ready_and_frozen(finding)
        self.gate.queue('reproduced', 3.06, 6)
        self.runner.reproduce(finding, self.manifest(finding))


class NextTest(LoopTest):
    def test_picks_the_oldest_filed_finding_and_plans_triage_without_changing_it(self):
        self.github.add(30)
        self.github.add(21)
        before = deepcopy(self.github.issues)
        plan = self.runner.next()
        self.assertEqual((plan['finding'], plan['state'], plan['step'], plan['refused']), (21, 'Filed', 'triage', None))
        self.assertEqual(self.github.issues, before)


class TriageTest(LoopTest):
    def test_ready_swaps_needs_triage_for_the_ready_labels_and_explains_why(self):
        self.github.add(21)
        report = self.runner.triage(21, 'ready', 'Owning skill confirmed; failure is reproducible.')
        self.assertEqual((report['refused'], report['from'], report['to']), (None, 'Filed', 'Ready'))
        self.assertEqual(self.github.labels(21), ['loop:ready', 'ready-for-agent', 'retro-finding'])
        self.assertIn('Owning skill confirmed', self.github.issues[21]['comments'][-1])
        self.assertEqual(self.runner.next(21)['step'], 'freeze')

    def test_investigate_then_ready(self):
        self.github.add(21)
        self.runner.triage(21, 'investigate', 'Needs a reproducible case.')
        self.assertEqual(self.github.labels(21), ['loop:investigate', 'retro-finding'])
        self.runner.triage(21, 'ready', 'Case found.')
        self.assertEqual(self.github.labels(21), ['loop:ready', 'ready-for-agent', 'retro-finding'])

    def test_dismiss_closes_as_not_planned_with_wontfix(self):
        self.github.add(21, labels=['retro-finding', 'loop:investigate'])
        report = self.runner.triage(21, 'dismiss', 'Not a skill problem.')
        self.assertEqual(report['to'], 'Dismissed')
        issue = self.github.issues[21]
        self.assertEqual((issue['state'], issue['state_reason']), ('CLOSED', 'NOT_PLANNED'))
        self.assertEqual(self.github.labels(21), ['retro-finding', 'wontfix'])
        self.assertIn('Not a skill problem.', issue['comments'][-1])

    def test_illegal_triage_is_refused_and_changes_nothing(self):
        self.github.add(21, labels=['retro-finding', 'loop:investigate'])
        self.github.add(22, labels=['retro-finding', 'loop:ready', 'ready-for-agent'])
        self.github.add(23, labels=['retro-finding', 'loop:verify'])
        before = deepcopy(self.github.issues)
        for number, decision in ((21, 'investigate'), (22, 'ready'), (22, 'dismiss'), (23, 'dismiss')):
            report = self.runner.triage(number, decision, 'why')
            self.assertTrue(report['refused'], (number, decision))
        self.assertEqual(self.github.issues, before)
        self.assertEqual(self.runner.ledger_entries(), [])

    def test_ready_needs_an_owning_skill_that_jstack_has(self):
        self.github.add(21, skill=None)
        self.github.add(22, skill='not-a-skill')
        self.assertIn('owning skill', self.runner.triage(21, 'ready', 'why')['refused'])
        self.assertIn('not-a-skill', self.runner.triage(22, 'ready', 'why')['refused'])
        report = self.runner.triage(22, 'ready', 'The fix belongs in j-review.', owning='j-review')
        self.assertIsNone(report['refused'])
        self.assertEqual(self.runner.next(22)['owning_skill'], 'j-review')
        self.assertIn('Owning skill: j-review', self.github.issues[22]['comments'][-1])


class FreezeAndReproduceTest(LoopTest):
    def test_freeze_records_the_hashes_on_the_finding_and_cannot_be_repeated(self):
        self.github.add(21, labels=READY)
        report = self.runner.freeze(21, CASES)
        self.assertIsNone(report['refused'])
        self.assertIn('a' * 64, self.github.issues[21]['comments'][-1])
        self.assertEqual(self.github.labels(21), sorted(READY))
        self.assertEqual(self.runner.next(21)['step'], 'reproduce')
        self.assertIn('already frozen', self.runner.freeze(21, CASES)['refused'])

    def test_freeze_refuses_a_finding_that_is_not_ready_or_cases_without_hashes(self):
        self.github.add(21)
        self.github.add(22, labels=READY)
        self.assertIn('Ready', self.runner.freeze(21, CASES)['refused'])
        bad = {**CASES, 'holdout': {'name': 'x', 'sha256': 'not-a-hash'}}
        self.assertIn('holdout', self.runner.freeze(22, bad)['refused'])
        self.assertIn('control', self.runner.freeze(22, {**CASES, 'controls': []})['refused'])
        self.assertEqual(self.github.issues[22]['comments'], [])

    def test_a_reproduced_failure_records_the_spend_and_unlocks_the_implementer(self):
        self.ready_and_frozen()
        self.gate.queue('reproduced', 3.06, 6, reasons=['opus: incumbent 0/3', 'sonnet: incumbent 1/3'])
        report = self.runner.reproduce(21, self.manifest())
        self.assertEqual((report['refused'], report['outcome'], report['to']), (None, 'reproduced', 'Ready'))
        self.assertIn('sonnet: incumbent 1/3', self.github.issues[21]['comments'][-1])
        plan = self.runner.next(21)
        self.assertEqual((plan['step'], plan['finding_spent_usd'], plan['month_spent_usd']), ('implement', 3.06, 3.06))

    def test_not_reproduced_sends_the_finding_to_investigate_and_unfreezes_its_cases(self):
        self.ready_and_frozen()
        self.gate.queue('not_reproduced', 3.06, 6, reasons=['opus: incumbent passed 2/3'])
        report = self.runner.reproduce(21, self.manifest())
        self.assertEqual(report['to'], 'Investigate')
        self.assertEqual(self.github.labels(21), ['loop:investigate', 'retro-finding'])
        self.assertIn('opus: incumbent passed 2/3', self.github.issues[21]['comments'][-1])
        self.runner.triage(21, 'ready', 'A sharper case is possible.')
        self.assertEqual(self.runner.next(21)['step'], 'freeze')

    def test_reproduce_refuses_a_manifest_that_does_not_match_the_frozen_cases(self):
        self.ready_and_frozen()
        before = deepcopy(self.github.issues)
        changed = {**CASES, 'target': {'name': 'stale-receipts', 'sha256': 'e' * 64}}
        for manifest in (self.manifest(cases=changed), self.manifest(finding=22), self.manifest(mode='gate')):
            self.assertTrue(self.runner.reproduce(21, manifest)['refused'])
        self.assertEqual((self.gate.manifests, self.github.issues), ([], before))

    def test_a_reproduce_manifest_may_carry_only_the_target_case(self):
        self.ready_and_frozen()
        self.gate.queue('reproduced', 3.06, 6)
        self.assertIsNone(self.runner.reproduce(21, self.manifest(cases={'target': CASES['target']}))['refused'])

    def test_a_changed_frozen_case_while_reproducing_unfreezes_the_cases_for_investigation(self):
        self.ready_and_frozen()
        self.gate.queue('rejected', 3.06, 6, reasons=['Frozen case stale-receipts changed after freezing.'])
        report = self.runner.reproduce(21, self.manifest())
        self.assertEqual((report['outcome'], report['to']), ('rejected', 'Investigate'))
        self.assertEqual(self.github.labels(21), ['loop:investigate', 'retro-finding'])
        self.assertIn('changed after freezing', self.github.issues[21]['comments'][-1])
        self.runner.triage(21, 'ready', 'Refreeze.')
        self.assertEqual(self.runner.next(21)['step'], 'freeze')

    def test_an_infrastructure_fault_while_reproducing_gets_one_retry_then_goes_to_the_owner(self):
        self.ready_and_frozen()
        self.gate.queue('retry', 1.5, 6, reasons=['opus: 3 of 3 runs errored.'])
        report = self.runner.reproduce(21, self.manifest())
        self.assertEqual((report['outcome'], report['to']), ('retry', 'Ready'))
        plan = self.runner.next(21)
        self.assertEqual((plan['step'], plan['infra_retry_used']), ('reproduce', True))
        self.assertIn('infra_retry_used', self.runner.reproduce(21, self.manifest())['refused'])
        self.gate.queue('inconclusive', 1.5, 6, reasons=['Second infrastructure fault this attempt.'])
        report = self.runner.reproduce(21, self.manifest(infra_retry_used=True))
        self.assertEqual(report['to'], 'With owner')
        self.assertEqual(self.github.labels(21), ['loop:inconclusive', 'ready-for-human', 'retro-finding'])
        self.assertEqual(self.runner.next(21)['finding_spent_usd'], 3.0)

    def test_reproduce_needs_frozen_cases_and_runs_once(self):
        self.github.add(21, labels=READY)
        self.assertIn('frozen', self.runner.reproduce(21, self.manifest())['refused'])
        self.runner.freeze(21, CASES)
        self.gate.queue('reproduced', 3.06, 6)
        self.runner.reproduce(21, self.manifest())
        self.assertIn('already reproduced', self.runner.reproduce(21, self.manifest())['refused'])


class AttemptTest(LoopTest):
    def attempt(self, outcome, cost_usd=45.9, runs=90, reasons=('reason',)):
        attempt = self.runner.implement(21)['attempt']
        self.gate.queue(outcome, cost_usd, runs, reasons)
        return self.runner.gate(21, self.manifest(mode='gate', attempt=attempt))

    def test_implement_starts_attempt_one_with_a_cost_ceiling_from_the_remaining_budget(self):
        self.reproduced()
        report = self.runner.implement(21)
        self.assertEqual((report['refused'], report['to'], report['attempt']), (None, 'In progress', 1))
        self.assertEqual((report['estimate_usd'], report['max_cost_usd']), (45.9, 96.94))
        self.assertEqual(report['branch'], 'loop/j-build/21')
        self.assertEqual(self.github.labels(21), ['loop:in-progress', 'retro-finding'])
        self.assertEqual(self.runner.next(21)['step'], 'gate')

    def test_implement_waits_for_a_reproduced_failure(self):
        self.ready_and_frozen()
        self.github.add(22)
        self.assertIn('reproduced', self.runner.implement(21)['refused'])
        self.assertIn('Ready', self.runner.implement(22)['refused'])
        self.assertEqual(self.github.labels(21), sorted(READY))

    def test_an_accepted_gate_moves_the_finding_to_verify_and_records_the_spend(self):
        self.reproduced()
        report = self.attempt('accepted', reasons=['Both models pass.'])
        self.assertEqual((report['refused'], report['outcome'], report['to']), (None, 'accepted', 'Verify'))
        self.assertEqual(self.github.labels(21), ['loop:verify', 'retro-finding'])
        self.assertIn('Both models pass.', self.github.issues[21]['comments'][-1])
        plan = self.runner.next(21)
        self.assertEqual((plan['finding_spent_usd'], plan['month_spent_usd']), (48.96, 48.96))

    def test_a_rejected_attempt_returns_to_ready_with_the_outcome_label_and_reasons(self):
        self.reproduced()
        report = self.attempt('rejected', reasons=['opus: candidate passed the target 4/5, needs 5/5.'])
        self.assertEqual((report['outcome'], report['to']), ('rejected', 'Ready'))
        self.assertEqual(self.github.labels(21), ['loop:ready', 'loop:rejected', 'ready-for-agent', 'retro-finding'])
        self.assertIn('needs 5/5', self.github.issues[21]['comments'][-1])
        plan = self.runner.next(21)
        self.assertEqual((plan['step'], plan['attempt'], plan['estimate_usd']), ('implement', 1, 25.5))

    def test_the_second_failed_attempt_hands_the_finding_to_the_owner(self):
        self.reproduced()
        self.attempt('rejected')
        report = self.attempt('inconclusive', cost_usd=25.5, runs=50, reasons=['Models disagree.'])
        self.assertEqual(report['to'], 'With owner')
        self.assertEqual(self.github.labels(21), ['loop:inconclusive', 'loop:rejected', 'ready-for-human', 'retro-finding'])
        self.assertIn('attempt cap', self.github.issues[21]['comments'][-1])
        self.assertIn('owner', self.runner.next(21)['refused'])
        self.assertIn('owner', self.runner.implement(21)['refused'])

    def test_an_infrastructure_fault_gets_one_free_retry_and_a_second_is_inconclusive(self):
        self.reproduced()
        report = self.attempt('retry', reasons=['opus: 4 of 10 runs errored.'])
        self.assertEqual((report['outcome'], report['to']), ('retry', 'In progress'))
        self.assertEqual(self.github.labels(21), ['loop:in-progress', 'retro-finding'])
        plan = self.runner.next(21)
        self.assertEqual((plan['step'], plan['attempt'], plan['infra_retry_used']), ('gate', 1, True))
        self.assertIn('retry', self.runner.gate(21, self.manifest(mode='gate', attempt=1))['refused'])
        self.gate.queue('retry', 45.9, 90, ['opus: errors again.'])
        report = self.runner.gate(21, self.manifest(mode='gate', attempt=1, infra_retry_used=True))
        self.assertEqual((report['outcome'], report['to']), ('inconclusive', 'Ready'))
        self.assertIn('loop:inconclusive', self.github.labels(21))
        self.assertEqual(self.runner.next(21)['finding_spent_usd'], 94.86)

    def test_a_free_retry_the_budget_cannot_cover_is_inconclusive(self):
        self.reproduced()
        self.runner.spend(21, 30.0, 'implementer')
        report = self.attempt('retry', reasons=['sonnet: 6 of 10 runs errored.'])
        self.assertEqual((report['outcome'], report['to']), ('inconclusive', 'Ready'))
        self.assertIn('per-finding cap', self.github.issues[21]['comments'][-1])
        self.assertEqual(self.runner.next(21)['step'], 'handoff')

    def test_gate_refuses_a_finding_that_is_not_in_progress_or_a_stale_manifest(self):
        self.reproduced()
        consulted = len(self.gate.manifests)
        self.gate.queue('accepted', 45.9, 90)
        self.assertIn('in progress', self.runner.gate(21, self.manifest(mode='gate', attempt=1))['refused'])
        self.runner.implement(21)
        self.assertIn('attempt', self.runner.gate(21, self.manifest(mode='gate', attempt=2))['refused'])
        self.assertEqual(len(self.gate.manifests), consulted)

    def test_a_malformed_gate_output_is_an_error_not_a_decision(self):
        self.reproduced()
        self.runner.implement(21)
        self.gate.outputs.append({'outcome': 'accepted', 'reasons': [], 'runs': 90})
        with self.assertRaises(rl.GateError):
            self.runner.gate(21, self.manifest(mode='gate', attempt=1))
        self.assertEqual(self.github.labels(21), ['loop:in-progress', 'retro-finding'])


class SettleTest(LoopTest):
    def verify(self, number=21):
        self.github.add(number, labels=['retro-finding', 'loop:verify'])

    def test_a_merged_pr_closes_the_finding_as_completed(self):
        self.verify()
        self.github.closed_prs['loop/j-build/21'] = 'MERGED'
        self.assertEqual(self.runner.next(21)['step'], 'settle')
        report = self.runner.settle(21)
        self.assertEqual((report['refused'], report['to']), (None, 'Done'))
        issue = self.github.issues[21]
        self.assertEqual((issue['state'], issue['state_reason']), ('CLOSED', 'COMPLETED'))
        self.assertEqual(self.github.labels(21), ['retro-finding'])
        self.assertIn('closed', self.runner.next(21)['refused'])

    def test_a_declined_pr_hands_the_finding_to_the_owner(self):
        self.verify()
        self.github.closed_prs['loop/j-build/21'] = 'CLOSED'
        self.assertEqual(self.runner.settle(21)['to'], 'With owner')
        self.assertEqual(self.github.labels(21), ['ready-for-human', 'retro-finding'])

    def test_an_open_pr_is_still_waiting_for_the_owner(self):
        self.verify()
        self.github.prs = ['loop/j-build/21']
        before = deepcopy(self.github.issues)
        self.assertIn('Waiting for the owner', self.runner.settle(21)['refused'])
        self.assertIn('Waiting for the owner', self.runner.next(21)['refused'])
        self.assertEqual(self.github.issues, before)

    def test_settle_ignores_the_spend_caps(self):
        self.verify()
        self.github.closed_prs['loop/j-build/21'] = 'MERGED'
        self.runner.spend(99, 500.0, 'implementer')
        self.assertIsNone(self.runner.settle(21)['refused'])


class PickTest(LoopTest):
    def test_an_attempt_in_progress_comes_before_older_findings(self):
        self.github.add(21)
        self.github.add(25, labels=['retro-finding', 'loop:in-progress'])
        self.assertEqual((self.runner.next()['finding'], self.runner.next()['step']), (25, 'gate'))

    def test_a_settled_pr_comes_next_and_an_open_one_is_skipped(self):
        self.github.add(21)
        self.github.add(23, labels=['retro-finding', 'loop:verify'])
        self.github.add(24, labels=['retro-finding', 'loop:verify'])
        self.github.prs = ['loop/j-build/23']
        self.github.closed_prs['loop/j-build/24'] = 'MERGED'
        self.assertEqual((self.runner.next()['finding'], self.runner.next()['step']), (24, 'settle'))
        self.github.closed_prs.clear()
        self.assertEqual(self.runner.next()['finding'], 21)

    def test_investigate_and_owner_findings_are_not_picked(self):
        self.github.add(21, labels=['retro-finding', 'loop:investigate'])
        self.github.add(22, labels=['retro-finding', 'ready-for-human'])
        self.github.add(23, labels=['retro-finding', 'needs-triage', 'loop:ready'])  # two states: left alone
        plan = self.runner.next()
        self.assertEqual((plan['finding'], plan['step']), (None, None))
        self.assertIn('No Filed or Ready finding', plan['refused'])

    def test_a_finding_waiting_on_its_skill_lets_the_next_one_move(self):
        self.reproduced(21)
        self.github.add(22, skill='j-review')
        self.github.prs = ['loop/j-build/9']
        plan = self.runner.next()
        self.assertEqual((plan['finding'], plan['step']), (22, 'triage'))

    def test_when_nothing_can_move_the_oldest_refusal_is_reported(self):
        self.reproduced(21)
        self.github.prs = ['loop/j-build/9']
        plan = self.runner.next()
        self.assertEqual(plan['finding'], 21)
        self.assertIn('open loop draft PR', plan['refused'])


class GuardTest(LoopTest):
    def every_step(self, number=21):
        return {
            'triage': self.runner.triage(number, 'ready', 'why'),
            'freeze': self.runner.freeze(number, CASES),
            'reproduce': self.runner.reproduce(number, self.manifest(number)),
            'implement': self.runner.implement(number),
            'gate': self.runner.gate(number, self.manifest(number, mode='gate', attempt=1)),
            'settle': self.runner.settle(number),
        }

    def test_the_kill_switch_stops_every_step_before_it_starts(self):
        self.reproduced()
        self.github.add(22)
        (self.dir / 'loop.disabled').write_text('')
        before = deepcopy(self.github.issues)
        entries = len(self.runner.ledger_entries())
        for step, report in self.every_step().items():
            self.assertIn('kill switch', report['refused'], step)
        self.assertIn('kill switch', self.runner.next()['refused'])
        self.assertEqual(self.github.issues, before)
        self.assertEqual(len(self.runner.ledger_entries()), entries)
        (self.dir / 'loop.disabled').unlink()
        self.assertIsNone(self.runner.implement(21)['refused'])

    def test_the_monthly_cap_stops_the_loop_until_the_month_turns(self):
        self.github.add(21)
        self.runner.spend(99, 300.0, 'implementer')
        self.runner.check_in()
        self.runner.spend(99, 200.0, 'implementer')
        before = deepcopy(self.github.issues)
        self.assertIn('Monthly cap', self.runner.next()['refused'])
        self.assertIn('Monthly cap', self.runner.triage(21, 'ready', 'why')['refused'])
        self.assertEqual(self.github.issues, before)
        self.clock = datetime(2026, 12, 1, 0, 1, tzinfo=timezone.utc)
        plan = self.runner.next()
        self.assertEqual((plan['refused'], plan['month_spent_usd']), (None, 0))

    def test_passing_300_pauses_the_loop_until_the_owner_checks_in(self):
        self.github.add(21)
        self.assertIn('No check-in', self.runner.check_in()['refused'])
        report = self.runner.spend(99, 300.0, 'implementer')
        self.assertTrue(report['check_in_pending'])
        self.assertIn('check-in', self.runner.next()['refused'])
        self.assertIn('check-in', self.runner.triage(21, 'ready', 'why')['refused'])
        self.assertIsNone(self.runner.check_in()['refused'])
        self.assertIsNone(self.runner.triage(21, 'ready', 'why')['refused'])

    def test_spend_from_agent_steps_counts_toward_the_finding_and_the_month(self):
        self.github.add(21)
        self.runner.spend(21, 1.25, 'triage')
        self.runner.spend(21, 0.5, 'eval-author', note='GPT Sol wrote three cases')
        plan = self.runner.next(21)
        self.assertEqual((plan['finding_spent_usd'], plan['month_spent_usd']), (1.75, 1.75))
        self.assertIn('usd', self.runner.spend(21, -1, 'triage')['refused'])

    def test_a_step_that_would_take_the_finding_over_100_dollars_hands_it_to_the_owner(self):
        self.reproduced()
        self.runner.spend(21, 60.0, 'implementer')
        plan = self.runner.next(21)
        self.assertEqual((plan['step'], plan['refused']), ('handoff', None))
        self.assertIn('$100', plan['reason'])
        before = deepcopy(self.github.issues)
        self.assertIn('handoff', self.runner.implement(21)['refused'])
        self.assertEqual(self.github.issues, before)
        report = self.runner.handoff(21)
        self.assertEqual((report['refused'], report['to']), (None, 'With owner'))
        self.assertEqual(self.github.labels(21), ['loop:inconclusive', 'ready-for-human', 'retro-finding'])
        self.assertIn('$100', self.github.issues[21]['comments'][-1])

    def test_handoff_is_refused_while_the_finding_can_still_move(self):
        self.reproduced()
        before = deepcopy(self.github.issues)
        self.assertTrue(self.runner.handoff(21)['refused'])
        self.assertEqual(self.github.issues, before)

    def test_a_ready_finding_with_both_attempts_used_goes_to_the_owner(self):
        self.reproduced()
        for attempt in (1, 2):
            self.runner.implement(21)
            self.gate.queue('rejected', 10.0, 50)
            self.runner.gate(21, self.manifest(mode='gate', attempt=attempt))
        self.github.edit_labels(21, ['loop:ready', 'ready-for-agent'], ['ready-for-human'])  # owner put it back
        plan = self.runner.next(21)
        self.assertEqual(plan['step'], 'handoff')
        self.assertIn('attempt', plan['reason'])
        self.assertEqual(self.runner.handoff(21)['to'], 'With owner')
        self.assertIn('ready-for-human', self.github.labels(21))

    def test_one_open_loop_pr_per_owning_skill(self):
        self.reproduced(21)
        self.reproduced(22)
        self.github.prs = ['loop/j-build/21', 'feature/unrelated']
        before = deepcopy(self.github.issues)
        self.assertIn('loop/j-build/21', self.runner.implement(22)['refused'])
        self.assertIn('open loop draft PR', self.runner.next(22)['refused'])
        self.assertEqual(self.github.issues, before)
        self.github.prs = ['loop/j-review/30']
        self.assertIsNone(self.runner.implement(22)['refused'])


if __name__ == '__main__':
    unittest.main()
