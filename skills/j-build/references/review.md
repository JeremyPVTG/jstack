# Review stage

Three lenses on every task, each a fresh reviewer that sees only the diff and the brief:

- **Correctness:** wrong results, crashes, leaks, races, error paths that leave state behind, contract mismatches with callers (read the caller's code).
- **Repo rules:** the repository's AGENTS.md, principles and build file review rules; decisions the change contradicts without a new decision record.
- **Tests:** new behaviour no test exercises, tests that pass for the wrong reason, timing races, fakes that diverge from what they stand in for.

Report only defects with a concrete failure path. No style or formatting notes; hooks handle those. An empty list is a valid result.

## Refute, merge, fix

1. **Merge by root cause.** Lenses often report one defect in different words or places; group findings that one fix would resolve, keep the most severe wording.
2. **Refute each group independently.** A refuter reads the code itself and refutes the finding unless it can trace the failure path; out-of-diff findings are refuted.
3. **Fix only confirmed findings,** smallest change each, with a test where practical; re-run the checks.
4. **Verdict:** end with `VERDICT: CLEAN` (nothing confirmed, or all confirmed fixed and checks pass) or `VERDICT: FINDINGS` (something confirmed is still open, or a fix failed its checks). A prose review without the verdict line does not count as clean.

## Running it

- **Claude Code with the Workflow tool** (when the user has asked for a workflow): `Workflow({scriptPath: "<this skill>/references/workflow.js", args: {goal, base, checks: [...]}})`, with `base` and `checks` from the build file. The result has `verdict`, `confirmed`, `refuted`, `unverified` and `fix`. Read `unverified` yourself.
- **Elsewhere:** three subagents (in T3, `delegate_task` or the host's native agent tool), one refuter per merged finding, then fix what survives yourself.
