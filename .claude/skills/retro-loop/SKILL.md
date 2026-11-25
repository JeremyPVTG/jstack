---
name: retro-loop
description: Run jstack's retro improvement loop for one retro finding, one runner step per invocation, from triage through frozen cases, reproduce, implement and gate to the draft PR pair. Use for the daily retro loop task, or when asked to run the retro loop, or to run it now for finding N.
---

# Retro loop

Move one retro finding one step, then stop. `scripts/retro_loop.py` (the runner) owns the queue state, the caps and every refusal. This skill does the agent and eval work a step needs and records the result with the runner. Terms are in `GLOSSARY.md`; the gate is ADR 0005 (`docs/decisions/0005-retro-improvement-loop-gate.md`). The command surfaces are `python3 scripts/retro_loop.py --help` and `python3 <evals>/harness/retro-loop/run.py --help`.

## Before the step

1. Read `.claude/skills/retro-loop/config.local.json` (gitignored). It gives `<jstack>` (the main jstack checkout), `<evals>` (the jstack-evals checkout), `<work>` (where cases, holdouts, run directories and reports live, outside both repositories) and a delegate target per role. If it is missing, stop and ask the owner to copy `config.example.json` beside it and fill it in.
2. Work in `<jstack>` on `main`, clean and fast-forwarded to `origin/main` (`git pull --ff-only`), so that the incumbent and the implementer's starting point are the current base.
3. Plan: `python3 scripts/retro_loop.py next > <work>/plan.json`, or `next --finding <N>` for a run now on a named finding. If the plan has `refused` set (exit 3), report the refusal word for word and stop. That covers the kill switch, the monthly cap, the 300 USD check-in, the one-PR-per-skill rule and a draft PR waiting for the owner.

The plan names `finding` (`<N>`), `step`, `owning_skill` (`<skill>`), `attempt`, `max_cost_usd` and `branch`. Do that one step, record it, report, stop.

## Steps

The runner's global options go before its command: `python3 scripts/retro_loop.py --gate-script <evals>/harness/retro-loop/gate.py gate <N> --manifest M`. Delegate each agent step with T3's `delegate_task`, setting `target` to the role's entry in the config (`providerInstanceId`, `model`, `options`), `role` to the delegate role named in the step, and `task` to the brief from [references/briefs.md](references/briefs.md). Wait for the completion notice, then read the result with `task_status`. After every agent step, record its cost: `spend <N> --usd X --role <role>`, using the cost `task_status` reports, or 0 with `--note "no metered cost reported"` when it reports none. Eval runs reach the ledger through the runner's `reproduce` and `gate` commands, so they never go through `spend`.

### triage

Delegate the triage brief (delegate role `research`). Record its JSON reply: `triage <N> --decision <decision> --reason "<reason>"`, adding `--owning-skill <skill>` when it names one. A sanitization problem is recorded as `investigate`, described without repeating the leaked detail, and the owner is told: the issue text is theirs to edit.

### freeze

Create `<work>/cases/<N>/` and `<work>/holdout/<N>/`. When they hold an earlier freeze (the failure did not reproduce), first move each to `<N>-superseded-<date>` beside it, so earlier runs keep their cases. Then delegate the eval author brief (delegate role `test`). When it returns, hash every case yourself with `python3 <evals>/harness/retro-loop/gate.py hash <case dir>`; each hash must equal the one in `<work>/cases/<N>/cases.json`. A mismatch goes back to the eval author once, then to the owner. Record `freeze <N> --cases <work>/cases/<N>/cases.json`, then comment the checker's sha256 on the issue (`gh issue comment <N> --body "Checker sha256: ..."`). Case files stay in `<work>` until the record PR.

### reproduce

```sh
python3 <evals>/harness/retro-loop/run.py reproduce --plan <work>/plan.json \
  --cases <work>/cases/<N>/cases.json --case-dir <work>/cases/<N> \
  --checker <work>/cases/<N>/checker.py --jstack <jstack> --run-root <work>/runs > <work>/report.json
```

Exit 0: record `reproduce <N> --manifest <report's manifest>`. Exit 3: report the refusal and stop. Exit 1: report `error` and `spent_usd` and stop; running the driver again with the same inputs reuses its saved results, so nothing is paid or recorded twice.

### implement

1. `implement <N>`. A refusal ends the step.
2. On attempt 2, first keep attempt 1's candidate: `git branch -m loop/<skill>/<N> loop/<skill>/<N>-attempt-1`.
3. Delegate the implementer brief (delegate role `implementation`, `isolation: "worktree"`). The brief carries the finding text and, on attempt 2, attempt 1's diff. Everything in `<work>` and jstack-evals stays out of it: the implementer works from the finding alone.
4. Check its result: `loop/<skill>/<N>` exists; `git diff --stat main...loop/<skill>/<N>` touches only `skills/<skill>/`; `git log --format=%B main..loop/<skill>/<N>` has no AI credit. A failed check goes to the owner, with the finding left in progress.

The gate is the next invocation's step.

### gate

```sh
python3 <evals>/harness/retro-loop/run.py gate --plan <work>/plan.json \
  --cases <work>/cases/<N>/cases.json --case-dir <work>/cases/<N> --holdout-dir <work>/holdout/<N> \
  --checker <work>/cases/<N>/checker.py --jstack <jstack> --run-root <work>/runs > <work>/report.json
```

On attempt 2 add `--reuse-incumbent-from` with attempt 1's manifest: the `<work>/runs/<N>/gate-a1-*/manifest.json` whose `decision.json` outcome is not `retry`. Handle the exit code as in reproduce, then record `gate <N> --manifest <report's manifest>`. The runner moves the finding. Only `accepted` continues, in this same invocation:

1. **Advisory judges.** Delegate the judges brief to each `judges` target in parallel (delegate role `review`), pointing at the report's `judges.bundle`. Unblind their verdicts with the report's `judges.key` and tally them per condition and model. They advise; the gate's outcome stands whatever they say. Record their spend with role `judges`.
2. **Draft PR pair.** Follow [references/pr-pair.md](references/pr-pair.md).

### settle and handoff

`settle <N>` or `handoff <N>`, as the plan says. After a settle, remind the owner of the jstack-evals record PR, which they merge or close themselves.

## Owner stops

Stop and hand over, saying what the owner must do, when:

- the runner waits for the monthly check-in: clearing it with `check-in` is the owner's command alone;
- a pull request needs merging, marking ready or approving: the loop opens drafts and nothing more;
- a step would act outside jstack and jstack-evals: another repository, installed skills, agent or host configuration, the vault, secrets. Reading the evidence a finding cites is fine;
- a check above says the owner decides.

## Report

End with the finding and step, the runner's `from`, `to` and `outcome`, the spend recorded now and the month to date, links (issue, PRs, run directory) and the next step or the owner's action.

## Owner controls

- **Enable.** One-time setup: `config.local.json`, then `python3 scripts/retro_loop.py ensure-labels`. The daily T3 scheduled task is created disabled in the jstack project with the prompt "Use the retro-loop skill to move the next retro finding one step." The owner switches it on with `schedule_task` (its `scheduledTaskId`, `enabled: true`) or in T3's settings.
- **Pause.** `touch loop.disabled` in `<jstack>`: the runner refuses every step and the run driver stops before its next paid invocation. Delete the file to resume. It is gitignored, so it pauses this machine only.
- **Run now.** Ask for "the retro loop now for finding N". It is still one step.
- **Check-in.** `python3 scripts/retro_loop.py check-in` clears the 300 USD pause for the month.
- **Take back or return a finding.** Its handoff comment says which labels return it to the loop.
