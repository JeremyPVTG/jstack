# Review stage

Three lenses on every task, each a fresh reviewer running j-review in assess mode that sees only the diff, the brief and the build file's path:

- **Correctness:** wrong results, crashes, leaks, races, error paths that leave state behind, contract mismatches with callers (read the caller's code).
- **Repo rules:** the repository's AGENTS.md, principles and build file review rules; decisions the change contradicts without a new decision record.
- **Tests:** new behaviour no test exercises, tests that pass for the wrong reason, timing races, fakes that diverge from what they stand in for.

Report only defects with a concrete failure path. No style or formatting notes; hooks handle those. An empty list is a valid result.

## Refute, merge, fix

1. **Merge by root cause.** Lenses often report one defect in different words or places; group findings that one fix would resolve, keep the most severe wording.
2. **Refute each group independently.** A refuter (j-review in confirm mode) reads the code itself and refutes the finding unless it can trace the failure path; out-of-diff findings are refuted. For Small or docs-only work you may refute the findings yourself, reading the code for each; say so in the report.
3. **Fix only confirmed findings,** smallest change each, with a test where practical; re-run the checks.
4. **Verdict:** end with `VERDICT: CLEAN` (all three lenses ran, every finding was refuted or fixed, and the checks pass) or `VERDICT: FINDINGS` (anything confirmed or unchecked is still open, a lens or refuter failed to run, or after a fix a check failed or was not run). With nothing to fix the code is unchanged; Verify runs the checks. A prose review without the verdict line does not count as clean.

## Running it

- **Claude Code with the Workflow tool** (when the user has asked for a workflow): `Workflow({scriptPath: "<this skill>/references/workflow.js", args: {goal, base, buildFile, checks: [...]}})`, with `base` and `checks` from the build file and `buildFile` its path. Keep `goal` to one neutral sentence; your conclusions go nowhere near the reviewers. The result has `verdict`, `failedLenses`, `confirmed`, `refuted`, `unverified` and `fix`; FINDINGS with `failedLenses` or `unverified` entries means the review did not finish: re-run those lenses, or check those findings yourself.
- **Elsewhere:** three subagents (the host's native agent tool, or `delegate_task` in T3) each told to use j-review in assess mode, one refuter per merged finding told to use j-review in confirm mode, then fix what survives yourself (j-review fix mode).
