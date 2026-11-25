# Draft PR pair

Open the pair only after the runner recorded `accepted` (the finding is in Verify). Both pull requests are drafts, each links the other, neither is marked ready or merged, and nothing in them credits an AI: no Co-Authored-By trailer, "Generated with" line or session link. Write each body to a file and pass it with `--body-file`. The bodies follow the PR template (`mattpocock-skills:pr`), and the owner's PR hook refuses `gh pr create`, or a body edit, that lacks `## Summary`, `## Evidence` with `**Before:**` and `**After:**`, or `## Merge Danger` with `**Door:**` and `**Blast Radius:**`.

The figures come from the gate's decision (`per_model`, `skill_growth_pct`, `runs`, `cost_usd`), the reproduce decision, the judges' tally and `python3 scripts/retro_loop.py ledger --finding <N>`.

## 1. Experiment record (jstack-evals)

In `<evals>`, from an up-to-date `main`, run `git switch -c loop/<skill>/<N> main` and write `experiments/<date>-retro-<N>-<skill>/`:

- `cases/`: the target, the controls, `checker.py` and `FROZEN.md`, from `<work>/cases/<N>/`.
- `holdout/`: the soft holdout from `<work>/holdout/<N>/`. Its gate has run, so it may be public now.
- `runs/<run directory name>/` for the reproduce run and every gate run of this finding, retries included: `manifest.json`, `decision.json`, `results/*.json`, `checker/*.json`, and the two SKILL.md files as `skill-incumbent.md` and `skill-candidate.md`. Plugins, logs, traces and the judge bundle stay in `<work>`.
- `ledger.json`: the ledger output above.
- `README.md`: the record, shaped as below.

In each copied manifest, point `case_dir`, `holdout_dir`, `skill_md` and `reuse_incumbent_from` at the copies with relative paths. The record is done when `python3 harness/retro-loop/gate.py decide` on every copied manifest gives the outcome recorded for that run, and `python3 -m unittest discover -s tests` passes. Commit with a plain message, push the branch and open the draft with the record PR body from section 3, its last Summary line reading "Skill change: opened next.":

```sh
gh pr create --draft --base main --head loop/<skill>/<N> \
  --title "Experiment record: retro finding #<N> (<skill>)" --body-file <file>
```

Record README:

```markdown
# Retro finding #<N>: <finding title> (<skill>)

<What the finding saw, and the one change the candidate makes.>

| | Incumbent | Candidate |
|---|---|---|
| jstack revision | `<sha12>` (main) | `<sha12>` (loop/<skill>/<N>, attempt <k>) |
| Target, Opus / Sonnet | <a>/5, <b>/5 | 5/5, 5/5 |
| Soft holdout, Opus / Sonnet | not run | <x>/5, <y>/5 |
| Largest control drop | | <z> of 3 |
| SKILL.md | <bytes> | <bytes> (<+g>%) |

## Runs and cost

<Per step (reproduce, each gate run, retries): planned and recorded runs, failures, cost. Finding total and month to date from the ledger.>

## Advisory judges

<GPT Sol and Grok fast, blind to condition: verdicts per condition and model. Advice only; the gate decided.>

## Limits

- Development evidence with a soft holdout, not a sealed set: the holdout was outside the implementer's workspace, not beyond its reach.
- Tested on Claude models only (Opus and Sonnet) through `claude plugin eval` <version>.
- One target case at 5 runs per condition can show a large effect, not a small one. The thresholds are engineering choices (jstack ADR 0005), not statistical guarantees.

Skill change: <jstack PR URL>
```

## 2. Skill change (jstack)

In `<jstack>`: `git push -u origin loop/<skill>/<N>`, then:

```sh
gh pr create --draft --base main --head loop/<skill>/<N> \
  --title "<skill>: <what changes> (retro finding #<N>)" --body-file <file>
```

Name the finding with "Refs #<N>". A closing keyword would close it on merge before the runner's settle step, which closes it itself.

````markdown
## Summary

<One line: the behaviour that changes, from retro finding #<N>.>

```diff
<the smallest diff sketch of the SKILL.md change>
```

Refs #<N>. Experiment record: <record PR URL>.

## Evidence

- **Before:** incumbent `<sha12>` on the target case: Opus <a>/5, Sonnet <b>/5 (reproduce: Opus <c>/3, Sonnet <d>/3).
  **After:** candidate `<sha12>`: target Opus 5/5, Sonnet 5/5; soft holdout Opus <x>/5, Sonnet <y>/5; largest control drop <z> of 3; no critical failure; SKILL.md <+g>%.
- Advisory judges (GPT Sol and Grok fast, blind to condition, not deciding): <tally>.
- Limits: development evidence with a soft holdout, not a sealed set; tested on Claude models only (Opus and Sonnet); one target case at 5 runs per condition shows a large effect, not a small one. <runs> runs, <cost> USD.

## Merge Danger

**Door:** two-way

A skill text change: reverting the commit restores the incumbent.

**Blast Radius:** <skill>

Every host that installs <skill> gets the new instructions at its next pull or install.
````

## 3. Record PR body, then the link back

Once the jstack PR exists, put its URL on the record body's "Skill change" line and pass the whole body again (`gh pr edit <record PR number> -R JeremyPVTG/jstack-evals --body-file <file>`), since the hook checks every body edit:

````markdown
## Summary

Experiment record for retro finding JeremyPVTG/jstack#<N> (<skill>), attempt <k>: frozen cases, the soft holdout, every run's results and checker output, the decisions and the ledger.

```text
experiments/<date>-retro-<N>-<skill>/
├── README.md     # the record
├── cases/        # target, controls, checker.py, FROZEN.md
├── holdout/      # soft holdout, public now its gate has run
├── runs/         # manifest, decision, results and checker output per run
└── ledger.json   # spend and outcomes for #<N>
```

Skill change: <jstack PR URL>.

## Evidence

- **Before:** incumbent `<sha12>`: target Opus <a>/5, Sonnet <b>/5.
  **After:** candidate `<sha12>`: target Opus 5/5, Sonnet 5/5; soft holdout Opus <x>/5, Sonnet <y>/5.
- Every copied manifest gives its recorded outcome again with `python3 harness/retro-loop/gate.py decide`.
- Limits: as stated in the record README.

## Merge Danger

**Door:** two-way

Adds files under experiments/ only.

**Blast Radius:** none

No harness, grader or threshold changes.
````
