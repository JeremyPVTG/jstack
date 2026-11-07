# Evaluation boundary

jstack contains skills, installation tooling, and deterministic package tests. The separate jstack-evals repository owns task fixtures, grading, versioned suites, run receipts, and published behavioral results.

The evaluation repository pins an exact clean jstack commit and records model, host, tools, budgets, and evaluation revision. Public development cases are hill-climb targets, not hidden tests. Release evidence must include separate held-out tasks and complete results, including regressions.

Current status: package checks and installer tests pass locally. Behavioral trials and native host discovery remain unexecuted. No comparative improvement is claimed.

Until GitHub remotes are established, clone or keep the repositories as sibling directories named jstack and jstack-evals. From the latter, see PROTOCOL.md and docs/hill-climb.md. This is a repository relationship, not an installation dependency; using jstack does not require its evaluation tooling.
