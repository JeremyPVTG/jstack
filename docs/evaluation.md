# Evaluation boundary

jstack contains skills, installation tooling, and deterministic package tests. The separate jstack-evals repository owns task fixtures, grading, versioned suites, run receipts, and published behavioral results.

The evaluation repository pins an exact clean jstack commit and records model, host, tools, budgets, and evaluation revision. Public development cases are hill-climb targets, not hidden tests. Release evidence must include separate held-out tasks and complete results, including regressions.

Current status (2026-11-09): package checks and installer tests pass. Behavioral trials have been run for j-review and j-deliver; their results and limits are in [the skill value audit](skill-value-audit.md), which also holds dated measurement plans for three more skills. The remaining skills have no recorded result in this repository, and native host discovery remains uncertified. No improvement is claimed beyond the recorded results.

Until GitHub remotes are established, clone or keep the repositories as sibling directories named jstack and jstack-evals. From the latter, see PROTOCOL.md and docs/hill-climb.md. This is a repository relationship, not an installation dependency; using jstack does not require its evaluation tooling.
