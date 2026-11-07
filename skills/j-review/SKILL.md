---
name: j-review
description: Review a code change or address supplied review findings, with evidence tied to a specific revision. Use for review, red-team, confirmation, or bounded review fixes.
---

# Review a change

Choose the requested mode: assess, confirm earlier findings, or fix supplied findings. An assessment is read-only apart from requested report artifacts; a request to review alone does not authorize fixes or publishing.

Read the task and repository instructions. Record base and target revision and inspect the actual diff and relevant callers. For a moving branch, state which revision was reviewed; inspect new changes before extending the verdict to a newer head.

Find consequential defects within scope. For each finding show location, trigger, observed or traceable failure, impact, and the smallest remedy. Separate demonstrated failures from unresolved hypotheses. Prioritize correctness, security boundaries, data loss, and missing behavior over taste. Never invent findings to fill a quota.

In confirmation mode, reconcile each supplied finding as resolved, partial, unresolved, or no longer applicable. Check new defects introduced by the fixes without restarting an unrelated audit.

In fix mode, reproduce or trace the finding before changing code. Preserve others' edits. Add a regression test when it guards meaningful behavior; establish that it detects the original defect when practical. Build errors, prose edits, and already-fixed findings do not automatically need new tests. Use the project's permitted execution environment. Publishing requires task authorization; a review verdict alone does not grant it.

Report revision, findings ordered by impact, validation performed, and coverage limits. Say no actionable findings when warranted; that does not prove the whole system correct. Use [the evidence guide](references/evidence.md) when deciding whether a finding is substantiated.
