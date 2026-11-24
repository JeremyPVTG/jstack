# Evaluation boundary

jstack contains skills, installation tooling, and deterministic package tests. [jstack-evals](https://github.com/JeremyPVTG/jstack-evals) owns task fixtures, grading, versioned suites, run receipts, and published behavioral results.

The evaluation repository pins an exact clean jstack commit and records model, host, tools, budgets, and evaluation revision. Public development cases are hill-climb targets, not hidden tests. Release evidence must include separate held-out tasks and complete results, including regressions.

Current status (2026-11-21): package checks and installer tests pass. Behavioral results for j-research, j-build, j-review with j-deliver, j-scope, j-verify and jvault search are in the [jstack-evals results table](https://github.com/JeremyPVTG/jstack-evals#results). Native host discovery remains uncertified. No improvement is claimed beyond the recorded results.

Keep the repositories as sibling directories named jstack and jstack-evals; from the latter, see PROTOCOL.md and docs/hill-climb.md. This is a repository relationship, not an installation dependency; using jstack does not require its evaluation tooling.
