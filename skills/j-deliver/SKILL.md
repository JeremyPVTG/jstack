---
name: j-deliver
description: Validate, publish, or assess readiness of a software change against the repository release rules. Use for CI repair, publishing, merge readiness, or an authorized delivery task.
---

# Deliver a change

Determine the authorized outcome: diagnose CI, fix CI, validate, publish, assess readiness, or merge. Do the authorized work without adding approval stages. A request to assess readiness does not grant merge permission.

Read repository instructions and release configuration. Record the branch, current head, target base, and required checks. Discover the actual tools and execution environments; do not assume a host, workflow filename, approval actor, branch name, or provider.

For CI failure, inspect the job log for this revision and distinguish code failure from infrastructure failure or a flake. Reproduce with the narrowest useful check. Fix within scope, preserve others' work, and do not weaken gates to make the check pass.

Run appropriate checks in an allowed environment. Respect the user's machine limits and existing runner policy. Do not bypass hooks or required checks. Report exact commands or run receipts and the tested revision; do not equate a dispatched run with a passing result.

When publishing is authorized, verify that the remote has not diverged, push normally, and confirm the resulting remote head. Link a created, taken-over, or pushed PR using the host's required integration immediately. Keep the PR description aligned with the final change.

Assess readiness using the repository's actual required checks, review rules, unresolved findings, and approval scope. Do not add universal requirements for zero unresolved comments, a fresh base merge, multiple reviewers, or a special risk comment. Recheck the head before an authorized merge.

For pending checks or reviews, use the host's supported watch/handoff mechanism. Follow current host rules for delegates and monitoring; do not invent a polling loop. Report current head, verified state, and the remaining blocker or completed action. For project-specific gates read [the adapter contract](references/project-adapter.md).
