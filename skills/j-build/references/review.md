# Review stage

Three lenses on every task, each a fresh reviewer running j-review in assess mode that sees only the diff and the brief:

- **Correctness:** wrong results, crashes, leaks, races, error paths that leave state behind, contract mismatches with callers (read the caller's code).
- **Repo rules:** the repository's AGENTS.md, principles and build file review rules; decisions the change contradicts without a new decision record.
- **Tests:** new behaviour no test exercises, tests that pass for the wrong reason, timing races, fakes that diverge from what they stand in for.

Report only defects with a concrete failure path. No style or formatting notes; hooks handle those. An empty list is a valid result.

## Refute, merge, fix

1. **Merge by root cause.** Lenses often report one defect in different words or places; group findings that one fix would resolve, keep the most severe wording.
2. **Refute each group independently.** A refuter (j-review in confirm mode) reads the code itself and refutes the finding unless it can trace the failure path; out-of-diff findings are refuted. For Small or docs-only work you may refute the findings yourself, reading the code for each; say so in the report.
3. **Fix only confirmed findings,** smallest change each, with a test where practical; re-run the checks.
4. **Verdict:** end with `VERDICT: CLEAN` (nothing confirmed, or all confirmed fixed and checks pass) or `VERDICT: FINDINGS` (something confirmed is still open, or a fix failed its checks). A prose review without the verdict line does not count as clean.

## Running it

- **Claude Code with the Workflow tool** (when the user has asked for a workflow): `Workflow({scriptPath: "<this skill>/references/workflow.js", args: {goal, base, checks: [...]}})`, with `base` and `checks` from the build file. The result has `verdict`, `confirmed`, `refuted`, `unverified` and `fix`. Read `unverified` yourself.
- **Elsewhere:** three subagents (the host's native agent tool, or `delegate_task` in T3) each told to use j-review in assess mode, one refuter per merged finding told to use j-review in confirm mode, then fix what survives yourself (j-review fix mode).
