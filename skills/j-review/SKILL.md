---
name: j-review
description: Review a code diff, confirm earlier findings, or fix supplied findings. Tie each verdict to a revision and a reachable failure; distinguish confirmed defects from hypotheses.
---

# Review a change

Choose the requested mode: assess, confirm, or fix. Assess and confirm leave source unchanged. Pin the base and target revisions; inspect the diff and relevant callers before trusting the description. If the head changes, inspect the delta before extending the verdict.

A finding needs a location, reachable trigger, observable consequence, and supporting code path or reproduction. Label unresolved hypotheses separately. Accept a clean diff without manufacturing findings. Distinguish environment failures from defects in the change.

For confirmation, reconcile each earlier finding as resolved, partial, unresolved, or inapplicable. Check for defects introduced by the fix without restarting an unrelated audit.

For a requested fix, reproduce or trace the defect, then make the smallest correction. Add a regression test when it guards meaningful behavior; verify it detects the original defect when practical. An already-fixed finding does not automatically need another test.

Report the reviewed revision, actionable findings, validation, and material coverage limits. A local finding marked resolved does not itself authorize resolving an external review thread or publishing the change.
