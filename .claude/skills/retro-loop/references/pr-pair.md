# Record and skill change pull requests

Every reproduce or gate outcome the runner records gets an experiment record pull request in jstack-evals (section 1), whatever the outcome: reproduced, not reproduced, accepted, rejected, inconclusive or retry. Only an accepted gate also gets the skill change pull request in jstack (section 2), and then the two link to each other (section 3). Every pull request is a draft, none is marked ready or merged, and nothing in them credits an AI: no Co-Authored-By trailer, "Generated with" line or session link. Write each body to a file and pass it with `--body-file`. The bodies follow the PR template (`mattpocock-skills:pr`), and the owner's PR hook refuses `gh pr create`, or a body edit, that lacks `## Summary`, `## Evidence` with `**Before:**` and `**After:**`, or `## Merge Danger` with `**Door:**` and `**Blast Radius:**`.

The figures come from the step's decision (`per_model`, `skill_growth_pct`, `runs`, `cost_usd`), the reproduce decision, the judges' tally (accepted only) and `python3 scripts/retro_loop.py ledger --finding <N>`.

## 1. Experiment record (every outcome)

After the runner recorded the step, with `<run dir>` the run driver report's `run_dir` and `<run>` its name:

1. In `<jstack>`: `python3 scripts/retro_loop.py ledger --finding <N> > <work>/ledger-<N>.json`.
2. In `<evals>`, from an up-to-date `main`: `git switch -c record/<N>/<run> main`.
3. Copy the run into `harness/retro-loop/records/<N>/`:

   ```sh
   python3 harness/retro-loop/record.py <run dir> --cases <work>/cases/<N> --ledger <work>/ledger-<N>.json
   ```

   A gate record adds `--holdout <work>/holdout/<N>`: the soft holdout joins the record after its gate and never in a reproduce record. record.py makes the layout (its `--help` describes it): the frozen cases under `cases/<freeze>/`, the holdout under `holdout/<freeze>/`, and per run the manifest with relative paths, the decision, this ledger extract, the result and checker files and the SKILL.md copies. A second attempt's record also brings the incumbent runs it reused. Before writing anything it checks that `gate.py decide` gives every copied manifest its recorded decision, and it never overwrites a recorded file with other bytes. Exit 1: report its `error` and stop; the owner decides.
4. Run `python3 -m unittest discover -s tests`, commit with a plain message, `git push -u origin record/<N>/<run>`, and open the draft with the body below:

   ```sh
   gh pr create --draft --base main --head record/<N>/<run> \
     --title "Experiment record: retro finding #<N> <step>, <outcome> (<skill>)" --body-file <file>
   ```

````markdown
## Summary

Experiment record for retro finding JeremyPVTG/jstack#<N> (<skill>): <reproduce, or gate attempt <k>, or its infrastructure retry>, outcome <outcome>. The runner moved the finding from <from> to <to>.

```text
harness/retro-loop/records/<N>/
├── cases/<freeze>/     # frozen target, controls, checker.py, FROZEN.md
├── holdout/<freeze>/   # soft holdout, from the first gate record on
└── runs/<run>/         # manifest, decision, ledger extract, results, checker output, SKILL.md copies
```

<Accepted: "Skill change: <jstack PR URL>." Any other outcome: "No skill change: <the finding's next step, or the owner's action>.">

## Evidence

- **Before:** incumbent `<sha12>`: target Opus <a>/<n>, Sonnet <b>/<n> (<n> is 3 in reproduce, 5 in a gate).
  **After:** <reproduce: reproduced or not reproduced, and what it means for the finding. Gate: candidate `<sha12>`: target Opus <x>/5, Sonnet <y>/5; soft holdout Opus <h>/5, Sonnet <i>/5; largest control drop <z> of 3; critical failures <c>; SKILL.md <+g>%.>
- Outcome <outcome>: <the decision's reasons>.
- <Accepted only: advisory judges (GPT Sol and Grok fast, blind to condition, not deciding): <tally>.>
- record.py rechecked every copied manifest: `gate.py decide` gives its recorded decision.
- <runs> runs and <cost> USD this step; finding total <t> USD of 100, month to date <m> USD (ledger extract).
- Limits: development evidence with a soft holdout, not a sealed set; tested on Claude models only (Opus and Sonnet) through `claude plugin eval` <version>; one target case at 5 runs per condition shows a large effect, not a small one. The thresholds are engineering choices (jstack ADR 0005), not statistical guarantees.

## Merge Danger

**Door:** two-way

Adds files under harness/retro-loop/records/<N>/ only.

**Blast Radius:** none

No harness, grader or threshold changes.
````

## 2. Skill change (accepted only)

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

## 3. Link back (accepted only)

Once the jstack PR exists, put its URL on the accepted record body's "Skill change" line and pass the whole body again (`gh pr edit <record PR number> -R JeremyPVTG/jstack-evals --body-file <file>`), since the hook checks every body edit.
