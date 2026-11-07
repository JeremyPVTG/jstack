---
name: j-deliver
description: Diagnose or fix PR checks, publish a change, or assess merge readiness using revision-specific evidence and the target repository's release rules.
---

# Deliver a change

Identify the requested outcome: CI diagnosis or repair, validation, publishing, readiness, or merge. Read the repository's actual release rules; record the branch, head, base, required checks, and applicable approval scope.

For failing CI, inspect logs for that revision. Distinguish a code defect from infrastructure failure or a flake; reproduce with the narrowest useful check. Do not weaken a gate to make it pass.

For validation, record what ran, where, its revision, and the result. A dispatched job is pending evidence. Use the project's allowed execution environment.

Before an authorized push, inspect the remote head and preserve collaborator changes. Confirm the resulting remote revision. Follow current T3 instructions for PR linking and pending-check handoff.

Assess readiness from the current head's required checks, review findings, and approval rules. Do not add blanket requirements for zero comments, another reviewer, or a base-branch merge. Recheck the head before an authorized merge.

Report verified state and the remaining blocker or completed action. Existing authorization remains valid within its scope; readiness assessment alone does not grant merge permission.
