#!/usr/bin/env python3
"""Retro improvement loop runner: move one retro finding one legal step at a time (ADR 0005).

A finding's state lives in its GitHub labels and closure; spend, attempts, frozen case hashes and
outcomes live in an append-only ledger file. The runner never calls a paid model. The loop skill
asks `next` for the step (it changes nothing and applies every stop), runs any agent or eval work
the step needs, then records the result with that step's command. Each command prints a JSON
report; it exits 0 when it acted, 3 when it refused (changing nothing) and 1 on an error.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
KILL_SWITCH = 'loop.disabled'

STATE_LABELS = {
    'Filed': ('needs-triage',),
    'Investigate': ('loop:investigate',),
    'Ready': ('loop:ready', 'ready-for-agent'),
    'In progress': ('loop:in-progress',),
    'Verify': ('loop:verify',),
    'With owner': ('ready-for-human',),
    'Dismissed': ('wontfix',),
    'Done': (),
}
CLOSE_REASON = {'Done': 'completed', 'Dismissed': 'not planned'}
LABELS = {
    'retro-finding': ('5319E7', 'Finding from a j-launch retrospective, handled by the improvement loop'),
    'needs-triage': ('FBCA04', 'Maintainer needs to evaluate this issue'),
    'ready-for-agent': ('0E8A16', 'Fully specified, ready for an AFK agent'),
    'ready-for-human': ('1D76DB', 'Requires human implementation'),
    'wontfix': ('FFFFFF', 'This will not be worked on'),
    'loop:investigate': ('D4C5F9', 'Retro loop: needs more evidence or a better eval case'),
    'loop:ready': ('0E8A16', 'Retro loop: triaged, waiting for its next loop step'),
    'loop:in-progress': ('1D76DB', 'Retro loop: an implementer attempt is running'),
    'loop:verify': ('5319E7', 'Retro loop: gate accepted, draft PRs wait for the owner'),
    'loop:rejected': ('B60205', 'Retro loop: an attempt was rejected by the gate'),
    'loop:inconclusive': ('C5DEF5', 'Retro loop: an attempt or step was inconclusive'),
}

TRIAGE = {
    # decision: (states it may leave, state it enters)
    'ready': (('Filed', 'Investigate'), 'Ready'),
    'investigate': (('Filed',), 'Investigate'),
    'dismiss': (('Filed', 'Investigate'), 'Dismissed'),
}

PER_FINDING_CAP = 100
MONTH_CAP = 500
CHECK_IN_AT = 300
ATTEMPT_CAP = 2
RUNS = {'reproduce': 6, 'full': 90, 'reuse': 50}
COST_PER_RUN = 0.51  # recent j-build average per run (ADR 0005)
GATE_OUTCOMES = {
    'reproduce': {'reproduced', 'not_reproduced', 'rejected', 'retry', 'inconclusive'},
    'gate': {'accepted', 'rejected', 'inconclusive', 'retry'},
}


class GitHubError(Exception):
    pass


class GateError(Exception):
    pass


class Refused(Exception):
    pass


def check_cases(cases):
    def check(kind, case):
        if not (isinstance(case, dict) and isinstance(case.get('name'), str) and case['name']
                and re.fullmatch(r'[0-9a-f]{64}', str(case.get('sha256')))):
            raise Refused(f'The {kind} case needs a name and a sha256 hash.')
    if not isinstance(cases, dict):
        raise Refused('Cases must be an object with target, holdout and controls.')
    check('target', cases.get('target'))
    check('holdout', cases.get('holdout'))
    if not isinstance(cases.get('controls'), list) or not cases['controls']:
        raise Refused('At least one over-refusal control case is required.')
    for case in cases['controls']:
        check('control', case)


def check_gate_output(result, mode):
    """Keep only the fields the runner reads (contract: outcome, reasons, cost_usd, runs, infra_retry_used)."""
    if not isinstance(result, dict):
        raise GateError('Malformed gate output: not an object')
    out = {key: result.get(key) for key in ('outcome', 'reasons', 'cost_usd', 'runs')}
    out['infra_retry_used'] = result.get('infra_retry_used', False)
    problems = [name for name, ok in (
        ('outcome', out['outcome'] in GATE_OUTCOMES[mode]),
        ('reasons', isinstance(out['reasons'], list) and all(isinstance(r, str) for r in out['reasons'])),
        ('cost_usd', isinstance(out['cost_usd'], (int, float)) and not isinstance(out['cost_usd'], bool)
         and out['cost_usd'] >= 0),
        ('runs', isinstance(out['runs'], int) and not isinstance(out['runs'], bool) and out['runs'] >= 0),
        ('infra_retry_used', isinstance(out['infra_retry_used'], bool)),
    ) if not ok]
    if problems:
        raise GateError(f'Malformed gate output for {mode} mode: ' + ', '.join(problems))
    out['cost_usd'] = round(float(out['cost_usd']), 4)
    for key in ('incumbent_reused', 'reused_runs'):
        if key in result:
            out[key] = result[key]
    return out


def cases_match(given, frozen, mode):
    """A gate manifest names every frozen case; a reproduce manifest may name the target alone."""
    if mode == 'gate' or not isinstance(given, dict) or 'target' not in given:
        return given == frozen
    return all(frozen.get(role) == case for role, case in given.items())


def owning_skill(body):
    match = re.search(r'(?im)^[\s>*_-]*owning skill[*_\s]*:[*_\s`]*([a-z0-9][a-z0-9-]*)', body or '')
    return match.group(1) if match else None


def state_of(issue):
    if issue.get('state', 'OPEN') != 'OPEN':
        return 'Done' if issue.get('state_reason') == 'COMPLETED' else 'Dismissed'
    labels = set(issue['labels'])
    if 'retro-finding' not in labels:
        raise Refused(f"#{issue['number']} is not a retro finding.")
    if 'ready-for-human' in labels:
        return 'With owner'
    found = [state for state, names in STATE_LABELS.items() if names and names[0] in labels and state != 'Dismissed']
    if len(found) != 1:
        raise Refused(f"#{issue['number']} has labels for {len(found)} loop states; fix its labels by hand.")
    return found[0]


def money(value):
    return round(max(value, 0), 2)


class Ledger:
    """Append-only record of loop events; every total is folded from the entries."""

    def __init__(self, path):
        self.path = Path(path)
        self.entries = json.loads(self.path.read_text())['entries'] if self.path.exists() else []

    def add(self, entry):
        self.entries.append(entry)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, prefix='.ledger-')
        try:
            with os.fdopen(fd, 'w') as stream:
                json.dump({'version': 1, 'entries': self.entries}, stream, indent=2)
                stream.write('\n')
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def of(self, number):
        return [e for e in self.entries if e.get('finding') == number]


def reported(method):
    """Turn a Refused into a report that changed nothing."""
    def run(self, number, *args, **kwargs):
        try:
            return method(self, number, *args, **kwargs)
        except Refused as refusal:
            return {'finding': number, 'step': method.__name__, 'refused': str(refusal)}
    run.__name__ = method.__name__
    return run


class Runner:
    def __init__(self, github, ledger, kill_switch, gate=None, now=None, skills=ROOT / 'skills',
                 cost_per_run=COST_PER_RUN):
        self.github = github
        self.ledger = Ledger(ledger)
        self.kill_switch = Path(kill_switch)
        self.evals = gate
        self.now = now or (lambda: datetime.now(timezone.utc))
        self.skills = Path(skills)
        self.cost_per_run = cost_per_run

    def ledger_entries(self, number=None):
        return list(self.ledger.entries if number is None else self.ledger.of(number))

    def record(self, number, step, usd=0, **fields):
        at = self.now().astimezone(timezone.utc).isoformat()
        self.ledger.add({'at': at, 'finding': number, 'step': step, 'usd': usd, **fields})

    def month(self):
        return self.now().astimezone(timezone.utc).strftime('%Y-%m')

    def month_spent(self):
        return money(sum(e['usd'] for e in self.ledger.entries if e['at'].startswith(self.month())))

    def facts(self, issue):
        facts = {'owning_skill': owning_skill(issue['body']), 'frozen': None, 'reproduced': False, 'spent': 0,
                 'attempt': 0, 'infra_retry_used': False}
        for entry in self.ledger.of(issue['number']):
            facts['spent'] += entry['usd']
            step = entry['step']
            if entry.get('owning_skill'):
                facts['owning_skill'] = entry['owning_skill']
            if step in ('freeze', 'reproduce', 'implement', 'gate'):
                # One free infrastructure retry per reproduce or attempt; any other result ends it.
                facts['infra_retry_used'] = entry.get('outcome') == 'retry'
            if step == 'freeze':
                facts['frozen'], facts['reproduced'] = entry['cases'], False
            elif step == 'reproduce' and entry['outcome'] == 'reproduced':
                facts['reproduced'] = True
            elif step == 'reproduce' and entry['outcome'] in ('not_reproduced', 'rejected'):
                facts['frozen'] = None
            elif step == 'implement':
                facts['attempt'] = entry['attempt']
        facts['spent'] = money(facts['spent'])
        return facts

    def check_in_pending(self):
        month = self.month()
        checked = any(e['step'] == 'check-in' and e['at'].startswith(month) for e in self.ledger.entries)
        return self.month_spent() >= CHECK_IN_AT and not checked

    def guard(self, step=None):
        """Stops that apply to every finding. Settling a merged or closed PR only obeys the kill switch."""
        if self.kill_switch.exists():
            return f'The kill switch ({self.kill_switch}) is on: the loop does nothing.'
        if step == 'settle':
            return None
        spent = self.month_spent()
        if spent >= MONTH_CAP:
            return f'Monthly cap reached: ${spent:.2f} of ${MONTH_CAP} spent this month.'
        if self.check_in_pending():
            return f"Monthly spend passed ${CHECK_IN_AT} (${spent:.2f}): waiting for the owner's check-in."
        return None

    def stops(self, number, state):
        if state == 'With owner':
            return f'#{number} is with the owner (ready-for-human); the loop no longer picks it up.'
        if state in CLOSE_REASON:
            return f'#{number} is closed ({state}).'
        return None

    def handoff_reason(self, step, facts, runs):
        """Why this finding can no longer move inside the loop, or None."""
        if step == 'implement' and facts['attempt'] >= ATTEMPT_CAP:
            return f"Both attempts are used ({facts['attempt']} of {ATTEMPT_CAP})."
        estimate = money(runs * self.cost_per_run)
        if step in ('triage', 'freeze', 'reproduce', 'implement') and facts['spent'] + estimate > PER_FINDING_CAP:
            return (f"The next step ({step}) would cost about ${estimate:.2f} on top of ${facts['spent']:.2f} "
                    f'spent, over the ${PER_FINDING_CAP} per-finding cap.')
        return None

    def open_loop_pr(self, skill):
        heads = [h for h in self.github.open_pr_heads() if h.startswith(f'loop/{skill}/')]
        if heads:
            return f'{skill} already has an open loop draft PR ({heads[0]}): one per skill, so this finding waits.'
        return None

    def attempt_runs(self, attempt_before):
        return RUNS['reuse'] if attempt_before >= 1 else RUNS['full']

    def plan(self, issue):
        state = state_of(issue)
        facts = self.facts(issue)
        number = issue['number']
        step = {'Filed': 'triage', 'Investigate': 'triage', 'Ready': 'freeze', 'In progress': 'gate',
                'Verify': 'settle'}.get(state)
        if state == 'Ready' and facts['frozen']:
            step = 'implement' if facts['reproduced'] else 'reproduce'
        runs = {'reproduce': RUNS['reproduce'], 'implement': self.attempt_runs(facts['attempt']),
                'gate': self.attempt_runs(facts['attempt'] - 1)}.get(step, 0)
        branch = f"loop/{facts['owning_skill']}/{number}" if facts['owning_skill'] else None
        plan = {'finding': number, 'state': state, 'step': step, 'refused': None, 'reason': None,
                'owning_skill': facts['owning_skill'], 'attempt': facts['attempt'], 'attempt_cap': ATTEMPT_CAP,
                'infra_retry_used': facts['infra_retry_used'], 'estimate_runs': runs,
                'estimate_usd': money(runs * self.cost_per_run), 'max_cost_usd': self.max_cost(facts),
                'finding_spent_usd': facts['spent'], 'month_spent_usd': self.month_spent(), 'branch': branch}
        plan['refused'] = self.guard(step) or self.stops(number, state)
        if plan['refused']:
            return plan
        reason = self.handoff_reason(step, facts, runs)
        if reason:
            plan.update(step='handoff', reason=reason)
        elif step == 'implement':
            plan['refused'] = self.open_loop_pr(facts['owning_skill'])
        elif step == 'settle':
            pr = self.github.pr_state(branch)
            if pr not in ('MERGED', 'CLOSED'):
                plan['refused'] = f'Waiting for the owner to merge or close the draft PR from {branch}.'
        return plan

    def max_cost(self, facts):
        """Ceiling for --max-cost-usd: what is left of the per-finding cap and of the monthly cap."""
        return money(min(PER_FINDING_CAP - facts['spent'], MONTH_CAP - self.month_spent()))

    def next(self, finding=None):
        """Plan the next legal step without changing anything.

        With no finding, an attempt already in progress comes first, then a Verify finding whose PR the owner
        has merged or closed, then the oldest Filed or Ready finding that is free to move.
        """
        if finding is not None:
            try:
                return self.plan(self.github.issue(finding))
            except Refused as refusal:
                return {'finding': finding, 'step': None, 'refused': str(refusal)}
        rank = {'In progress': 0, 'Verify': 1, 'Filed': 2, 'Ready': 2}
        candidates = []
        for issue in self.github.findings():
            try:
                state = state_of(issue)
            except Refused:
                continue  # labels for two states: left for the owner, never guessed at
            if state in rank:
                candidates.append((rank[state], issue['number'], issue))
        plans = []
        for _, _, issue in sorted(candidates, key=lambda c: c[:2]):
            plan = self.plan(issue)
            if not plan['refused']:
                return plan
            plans.append(plan)
        unsettled = [p for p in plans if p['state'] != 'Verify']
        if unsettled:
            return unsettled[0]
        return {'finding': None, 'step': None, 'refused': self.guard() or 'No Filed or Ready finding can move.'}

    def move(self, issue, to, comment, outcome=None):
        number = issue['number']
        current = state_of(issue)
        add = [l for l in STATE_LABELS[to] + ((f'loop:{outcome}',) if outcome else ()) if l not in issue['labels']]
        remove = [l for l in STATE_LABELS[current] if l not in STATE_LABELS[to] and l in issue['labels']]
        if add or remove:
            self.github.edit_labels(number, add, remove)
        if to == 'With owner' and current != to:
            comment += ('\n\nTo return it to the loop, remove ready-for-human and add loop:ready and '
                        'ready-for-agent (or loop:investigate).')
        if to in CLOSE_REASON and current != to:
            self.github.close(number, CLOSE_REASON[to], comment)
        else:
            self.github.comment(number, comment)

    def spend_note(self, facts, result):
        """Totals after a recorded gate command result; facts are the ones read before recording it."""
        spent = money(facts['spent'] + result['cost_usd'])
        return (f"Runs: {result['runs']}. Cost: ${result['cost_usd']:.2f}. "
                f'Spent on this finding: ${spent:.2f} of ${PER_FINDING_CAP}. Month to date: ${self.month_spent():.2f}.')

    def open_issue(self, number, step):
        """The finding and its state, after the stops that apply to every step."""
        refused = self.guard(step)
        if refused:
            raise Refused(refused)
        issue = self.github.issue(number)
        state = state_of(issue)
        refused = self.stops(number, state)
        if refused:
            raise Refused(refused)
        return issue, state

    @reported
    def triage(self, number, decision, reason, owning=None):
        issue, state = self.open_issue(number, 'triage')
        sources, to = TRIAGE[decision]
        if state not in sources:
            raise Refused(f'Triage cannot move a {state} finding to {to}; it acts on {" or ".join(sources)} findings.')
        skill = owning or self.facts(issue)['owning_skill']
        lines = [f'Loop triage: {to}.', '', reason]
        if decision == 'ready':
            if not skill:
                raise Refused('Ready needs an owning skill: name it in the issue body or pass one.')
            if not (self.skills / skill / 'SKILL.md').is_file():
                raise Refused(f'Owning skill {skill} is not a jstack skill.')
            lines += ['', f'Owning skill: {skill}']
        self.move(issue, to, '\n'.join(lines))
        self.record(number, 'triage', decision=decision, owning_skill=owning)
        return {'finding': number, 'step': 'triage', 'from': state, 'to': to, 'refused': None}

    @reported
    def freeze(self, number, cases):
        issue, state = self.open_issue(number, 'freeze')
        if state != 'Ready':
            raise Refused(f'The eval author writes cases only for a Ready finding; #{number} is {state}.')
        if self.facts(issue)['frozen']:
            raise Refused('Cases are already frozen. Changing them now would let results shape the eval.')
        check_cases(cases)
        listed = [('target', cases['target']), ('holdout', cases['holdout'])] + [('control', c) for c in cases['controls']]
        lines = ['Loop freeze: eval cases frozen by the eval author.', '']
        lines += [f"- {kind} `{case['name']}`: `{case['sha256']}`" for kind, case in listed]
        self.github.comment(number, '\n'.join(lines))
        self.record(number, 'freeze', cases=cases)
        return {'finding': number, 'step': 'freeze', 'from': state, 'to': state, 'refused': None}

    def decide(self, number, manifest_path, mode, frozen, **expected):
        manifest = json.loads(Path(manifest_path).read_text())
        if not isinstance(manifest, dict) or manifest.get('mode') != mode or manifest.get('finding') != number:
            raise Refused(f'The manifest is not a {mode} manifest for #{number}.')
        if not cases_match(manifest.get('cases'), frozen, mode):
            raise Refused('The manifest cases differ from the cases frozen on this finding.')
        for key, value in expected.items():
            if manifest.get(key, False if key == 'infra_retry_used' else None) != value:
                raise Refused(f'The manifest says {key} {manifest.get(key)!r}; the ledger says {value!r}.')
        return check_gate_output(self.evals.decide(str(manifest_path)), mode)

    def gate_result(self, number, step, result, facts, rerun_runs, **fields):
        """Record a gate command result. A retry is inconclusive when the free retry is used or unaffordable."""
        outcome, reasons = result['outcome'], list(result['reasons'])
        rerun = money(rerun_runs * self.cost_per_run)
        spent = money(facts['spent'] + result['cost_usd'])
        if outcome == 'retry' and facts['infra_retry_used']:
            outcome = 'inconclusive'
            reasons.append('A second infrastructure fault: the free retry was already used.')
        elif outcome == 'retry' and spent + rerun > PER_FINDING_CAP:
            outcome = 'inconclusive'
            reasons.append(f'The free retry would cost about ${rerun:.2f} on top of ${spent:.2f} spent, '
                           f'over the ${PER_FINDING_CAP} per-finding cap.')
        extra = {k: result[k] for k in ('incumbent_reused', 'reused_runs') if k in result}
        self.record(number, step, usd=result['cost_usd'], runs=result['runs'], outcome=outcome, reasons=reasons,
                    **fields, **extra)
        return outcome, reasons

    @reported
    def reproduce(self, number, manifest_path):
        issue, state = self.open_issue(number, 'reproduce')
        facts = self.facts(issue)
        if state != 'Ready' or not facts['frozen']:
            raise Refused('Reproduce needs frozen cases on a Ready finding.')
        if facts['reproduced']:
            raise Refused('The failure is already reproduced; the incumbent has not changed.')
        result = self.decide(number, manifest_path, 'reproduce', facts['frozen'],
                             owning_skill=facts['owning_skill'], infra_retry_used=facts['infra_retry_used'])
        outcome, reasons = self.gate_result(number, 'reproduce', result, facts, RUNS['reproduce'])
        to, head = {
            'reproduced': ('Ready', 'Loop reproduce: the incumbent fails the target case, so the failure is reproduced.'),
            'not_reproduced': ('Investigate', 'Loop reproduce: the incumbent passes the target case, so the failure is '
                               'not reproduced. Back to Investigate with the cases unfrozen, for a better case.'),
            'rejected': ('Investigate', 'Loop reproduce: a frozen case changed after freezing. Back to Investigate '
                         'with the cases unfrozen; they must be written and frozen again.'),
            'retry': ('Ready', 'Loop reproduce: infrastructure fault. One free retry.'),
            'inconclusive': ('With owner', 'Loop reproduce: inconclusive after a second infrastructure fault. '
                             'Handed to the owner.'),
        }[outcome]
        lines = [head, ''] + ['- ' + reason for reason in reasons] + ['', self.spend_note(facts, result)]
        self.move(issue, to, '\n'.join(lines), outcome='inconclusive' if outcome == 'inconclusive' else None)
        return {'finding': number, 'step': 'reproduce', 'from': state, 'to': to, 'outcome': outcome,
                'reasons': reasons, 'refused': None}

    @reported
    def implement(self, number):
        issue, state = self.open_issue(number, 'implement')
        facts = self.facts(issue)
        if state != 'Ready' or not facts['reproduced']:
            raise Refused('The implementer starts only on a Ready finding whose failure reproduced.')
        plan = self.plan(issue)
        if plan['step'] == 'handoff':
            raise Refused(f"{plan['reason']} Run handoff instead.")
        if plan['refused']:
            raise Refused(plan['refused'])
        attempt = facts['attempt'] + 1
        self.move(issue, 'In progress', f'Loop implement: attempt {attempt} of {ATTEMPT_CAP} started on '
                  f"{facts['owning_skill']}. The implementer sees the finding, not the assertions.")
        self.record(number, 'implement', attempt=attempt)
        return {'finding': number, 'step': 'implement', 'from': state, 'to': 'In progress', 'attempt': attempt,
                'estimate_usd': plan['estimate_usd'], 'max_cost_usd': plan['max_cost_usd'],
                'branch': plan['branch'], 'refused': None}

    @reported
    def gate(self, number, manifest_path):
        issue, state = self.open_issue(number, 'gate')
        facts = self.facts(issue)
        if state != 'In progress':
            raise Refused(f'The gate runs only on a finding in progress; #{number} is {state}.')
        result = self.decide(number, manifest_path, 'gate', facts['frozen'], owning_skill=facts['owning_skill'],
                             attempt=facts['attempt'], infra_retry_used=facts['infra_retry_used'])
        outcome, reasons = self.gate_result(number, 'gate', result, facts, self.attempt_runs(facts['attempt'] - 1),
                                            attempt=facts['attempt'])
        if outcome == 'retry':
            to, head = state, 'Loop gate: infrastructure fault. One free retry: the attempt is not used up.'
        elif outcome == 'accepted':
            to, head = 'Verify', 'Loop gate: accepted. Draft pull requests follow.'
        elif facts['attempt'] >= ATTEMPT_CAP:
            to, head = 'With owner', f'Loop gate: {outcome}. The attempt cap is reached, so the finding goes to the owner.'
        else:
            to, head = 'Ready', f"Loop gate: {outcome}. Back to Ready for attempt {facts['attempt'] + 1}."
        lines = [head, '', f"Attempt {facts['attempt']} of {ATTEMPT_CAP}.", '']
        lines += ['- ' + reason for reason in reasons] + ['', self.spend_note(facts, result)]
        self.move(issue, to, '\n'.join(lines), outcome=outcome if outcome in ('rejected', 'inconclusive') else None)
        return {'finding': number, 'step': 'gate', 'from': state, 'to': to, 'outcome': outcome, 'reasons': reasons,
                'refused': None}

    @reported
    def handoff(self, number):
        issue, state = self.open_issue(number, 'handoff')
        plan = self.plan(issue)
        if plan['step'] != 'handoff':
            raise Refused(f"#{number} can still move (next step: {plan['step']}); handoff is for a finding the "
                          'attempt cap or the per-finding cap stops.')
        over_budget = 'per-finding cap' in plan['reason']
        self.move(issue, 'With owner', f"Loop handoff: {plan['reason']} The finding goes to the owner.",
                  outcome='inconclusive' if over_budget else None)
        self.record(number, 'handoff', reason=plan['reason'])
        return {'finding': number, 'step': 'handoff', 'from': state, 'to': 'With owner', 'reason': plan['reason'],
                'refused': None}

    @reported
    def settle(self, number):
        issue, state = self.open_issue(number, 'settle')
        if state != 'Verify':
            raise Refused(f'Only a Verify finding is settled; #{number} is {state}.')
        branch = self.plan(issue)['branch']
        pr = self.github.pr_state(branch)
        if pr == 'MERGED':
            to, comment = 'Done', f'Loop settle: the owner merged the draft PR from {branch}. Closed as completed.'
        elif pr == 'CLOSED':
            to, comment = 'With owner', f'Loop settle: the owner closed the draft PR from {branch} without merging.'
        else:
            raise Refused(f'Waiting for the owner to merge or close the draft PR from {branch}.')
        self.move(issue, to, comment)
        self.record(number, 'settle', pr=pr)
        return {'finding': number, 'step': 'settle', 'from': state, 'to': to, 'refused': None}

    @reported
    def spend(self, number, usd, role, note=None):
        """Record what an agent step cost. Never refused for caps: the money is already spent."""
        if isinstance(usd, bool) or not isinstance(usd, (int, float)) or usd < 0:
            raise Refused('usd must be a non-negative number.')
        self.record(number, 'spend', usd=round(float(usd), 4), role=role, note=note)
        return {'finding': number, 'step': 'spend', 'usd': round(float(usd), 4), 'refused': None,
                'month_spent_usd': self.month_spent(), 'check_in_pending': self.check_in_pending()}

    def file(self, title, body, decision, duplicate_of=None):
        """File an owner-approved retrospective draft, or add it as evidence to a matching finding.

        Filing belongs to the retrospective, not the loop, so the kill switch and caps do not apply.
        """
        report = {'finding': duplicate_of, 'step': 'file', 'filed': None, 'commented': None, 'refused': None}
        if decision == 'rejected':
            return {**report, 'note': 'The owner rejected the text: nothing filed.'}
        if decision != 'approved':
            return {**report, 'refused': 'The owner decision must be approved or rejected.'}
        if not owning_skill(body):
            return {**report, 'refused': 'The text must name its owning skill on an "Owning skill: <name>" line.'}
        if duplicate_of is not None:
            issue = self.github.issue(duplicate_of)
            if issue.get('state', 'OPEN') != 'OPEN' or 'retro-finding' not in issue['labels']:
                return {**report, 'refused': f'#{duplicate_of} is not an open retro finding.'}
            self.github.comment(duplicate_of, 'More evidence from a retrospective:\n\n' + body)
            return {**report, 'commented': duplicate_of}
        number = self.github.create_issue(title, body, ['retro-finding', 'needs-triage'])
        return {**report, 'finding': number, 'filed': number}

    def ensure_labels(self):
        """Create the labels the loop uses that the repository lacks. Running it again changes nothing."""
        existing = self.github.label_names()
        created = []
        for name, (color, description) in LABELS.items():
            if name not in existing:
                self.github.create_label(name, color, description)
                created.append(name)
        return {'step': 'ensure-labels', 'created': created, 'existing': sorted(set(LABELS) & existing),
                'refused': None}

    def check_in(self):
        """The owner clears this month's check-in pause."""
        if not self.check_in_pending():
            return {'finding': None, 'step': 'check-in', 'refused': 'No check-in is pending this month.'}
        self.record(None, 'check-in')
        return {'finding': None, 'step': 'check-in', 'refused': None, 'month_spent_usd': self.month_spent()}


class GhGitHub:
    """The runner's only route to GitHub: a few `gh` calls, with issues shaped as the runner reads them."""

    def __init__(self, repo=None, run=subprocess.run):
        self.repo = repo
        self.run = run

    def gh(self, *args, input=None):
        argv = ['gh', *args] + (['-R', self.repo] if self.repo else [])
        proc = self.run(argv, input=input, capture_output=True, text=True)
        if proc.returncode != 0:
            raise GitHubError(f"gh {' '.join(args[:2])} failed: {proc.stderr.strip()}")
        return proc.stdout

    @staticmethod
    def shape(raw):
        return {'number': raw['number'], 'title': raw.get('title', ''), 'body': raw.get('body') or '',
                'labels': [label['name'] for label in raw.get('labels', [])], 'state': raw.get('state', 'OPEN'),
                'state_reason': raw.get('stateReason') or None}

    def findings(self):
        out = self.gh('issue', 'list', '--label', 'retro-finding', '--state', 'open', '--limit', '500',
                      '--json', 'number,title,body,labels')
        return [self.shape(raw) for raw in json.loads(out)]

    def issue(self, number):
        out = self.gh('issue', 'view', str(number), '--json', 'number,title,body,labels,state,stateReason')
        return self.shape(json.loads(out))

    def edit_labels(self, number, add, remove):
        args = ['issue', 'edit', str(number)]
        args += ['--add-label', ','.join(add)] if add else []
        args += ['--remove-label', ','.join(remove)] if remove else []
        self.gh(*args)

    def comment(self, number, body):
        self.gh('issue', 'comment', str(number), '--body-file', '-', input=body)

    def close(self, number, reason, comment):
        self.gh('issue', 'close', str(number), '--reason', reason, '--comment', comment)

    def create_issue(self, title, body, labels):
        args = ['issue', 'create', '--title', title, '--body-file', '-']
        for label in labels:
            args += ['--label', label]
        url = self.gh(*args, input=body).strip()
        return int(url.rstrip('/').rsplit('/', 1)[1])

    def open_pr_heads(self):
        out = self.gh('pr', 'list', '--state', 'open', '--limit', '500', '--json', 'headRefName')
        return [pr['headRefName'] for pr in json.loads(out)]

    def pr_state(self, head):
        """OPEN, MERGED or CLOSED for the newest PR from this branch, or None when there is none."""
        prs = json.loads(self.gh('pr', 'list', '--head', head, '--state', 'all', '--limit', '20',
                                 '--json', 'number,state'))
        return max(prs, key=lambda pr: pr['number'])['state'] if prs else None

    def label_names(self):
        return {label['name'] for label in json.loads(self.gh('label', 'list', '--limit', '500', '--json', 'name'))}

    def create_label(self, name, color, description):
        self.gh('label', 'create', name, '--color', color, '--description', description)


class GateCommand:
    """The jstack-evals gate command: `python3 <gate.py> decide <manifest>` prints one JSON decision."""

    def __init__(self, script, run=subprocess.run):
        self.script = Path(script)
        self.run = run

    def decide(self, manifest):
        proc = self.run([sys.executable, str(self.script), 'decide', str(manifest)], capture_output=True, text=True)
        if proc.returncode != 0:
            raise GateError(f'gate command exited {proc.returncode}: {proc.stderr.strip() or "no message"}')
        try:
            return json.loads(proc.stdout)
        except ValueError:
            raise GateError('gate command printed no JSON decision') from None


def default_ledger():
    return Path(os.environ.get('JSTACK_RETRO_LEDGER', '~/.local/state/jstack/retro-loop/ledger.json')).expanduser()


def parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--ledger', type=Path, default=None, help='spend and outcome ledger (default: $JSTACK_RETRO_LEDGER '
                   'or ~/.local/state/jstack/retro-loop/ledger.json)')
    p.add_argument('--kill-switch', type=Path, default=ROOT / KILL_SWITCH,
                   help=f'the loop does nothing while this file exists (default: {KILL_SWITCH} in the jstack checkout)')
    p.add_argument('--repo', help='OWNER/REPO for gh (default: the current checkout)')
    p.add_argument('--gate-script', type=Path, help='jstack-evals gate.py, needed by reproduce and gate')
    p.add_argument('--cost-per-run', type=float, default=COST_PER_RUN, help='estimate per eval run in USD')
    sub = p.add_subparsers(dest='command', required=True)
    n = sub.add_parser('next', help='plan the next legal step; changes nothing')
    n.add_argument('--finding', type=int)
    t = sub.add_parser('triage', help="record triage's decision")
    t.add_argument('finding', type=int)
    t.add_argument('--decision', required=True, choices=sorted(TRIAGE))
    t.add_argument('--reason', required=True)
    t.add_argument('--owning-skill')
    f = sub.add_parser('freeze', help="record the eval author's frozen case hashes")
    f.add_argument('finding', type=int)
    f.add_argument('--cases', type=Path, required=True, help='JSON: {target, holdout, controls} with name and sha256')
    for name, about in (('reproduce', 'decide a reproduce manifest with the gate command'),
                        ('gate', "decide an attempt's gate manifest with the gate command")):
        g = sub.add_parser(name, help=about)
        g.add_argument('finding', type=int)
        g.add_argument('--manifest', type=Path, required=True)
    for name, about in (('implement', 'start the next attempt (In progress) before the implementer runs'),
                        ('handoff', 'hand a finding the caps stop to the owner'),
                        ('settle', "close or hand back a Verify finding once its draft PR is merged or closed")):
        sub.add_parser(name, help=about).add_argument('finding', type=int)
    s = sub.add_parser('spend', help='record what an agent step cost')
    s.add_argument('finding', type=int)
    s.add_argument('--usd', type=float, required=True)
    s.add_argument('--role', required=True, help='triage, eval-author, implementer, judges, ...')
    s.add_argument('--note')
    sub.add_parser('check-in', help="the owner clears this month's check-in pause")
    fi = sub.add_parser('file', help='file an owner-approved retrospective draft, or add it to a duplicate')
    fi.add_argument('--title', required=True)
    fi.add_argument('--body-file', type=Path, required=True)
    fi.add_argument('--owner', required=True, choices=['approved', 'rejected'], help="the owner's decision on the text")
    fi.add_argument('--duplicate-of', type=int)
    sub.add_parser('ensure-labels', help='create the loop labels the repository lacks; safe to repeat')
    le = sub.add_parser('ledger', help='print ledger entries')
    le.add_argument('--finding', type=int)
    return p


def main(argv=None, github=None, gate=None):
    args = parser().parse_args(argv)
    github = github or GhGitHub(args.repo)
    if gate is None and args.gate_script:
        gate = GateCommand(args.gate_script)
    try:
        if args.command in ('reproduce', 'gate') and gate is None:
            raise GateError('pass --gate-script: the jstack-evals gate.py')
        runner = Runner(github, args.ledger or default_ledger(), args.kill_switch, gate=gate,
                        cost_per_run=args.cost_per_run)
        command = args.command
        if command == 'next':
            report = runner.next(args.finding)
        elif command == 'triage':
            report = runner.triage(args.finding, args.decision, args.reason, owning=args.owning_skill)
        elif command == 'freeze':
            report = runner.freeze(args.finding, json.loads(args.cases.read_text()))
        elif command in ('reproduce', 'gate'):
            report = getattr(runner, command)(args.finding, args.manifest)
        elif command in ('implement', 'handoff', 'settle'):
            report = getattr(runner, command)(args.finding)
        elif command == 'spend':
            report = runner.spend(args.finding, args.usd, args.role, note=args.note)
        elif command == 'check-in':
            report = runner.check_in()
        elif command == 'file':
            report = runner.file(args.title, args.body_file.read_text(), args.owner, duplicate_of=args.duplicate_of)
        elif command == 'ensure-labels':
            report = runner.ensure_labels()
        else:
            report = runner.ledger_entries(args.finding)
    except (GitHubError, GateError, OSError, ValueError) as error:
        print('retro_loop:', error, file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 3 if isinstance(report, dict) and report.get('refused') else 0


if __name__ == '__main__':
    sys.exit(main())
