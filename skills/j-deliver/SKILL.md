---
name: j-deliver
description: Use this skill to publish a finished change (push the exact commit with hooks on and open or update the PR), to work an open pull request through conflicts, review threads and CI until it is ready, to diagnose and fix a failing check, or to decide whether a PR is ready to merge. Use when a brief says publish, push commit X, test and publish, fix CI, checks failed, babysit the PR, address the review comments on PR N, is PR N ready, or hand off PR N.
---

# Deliver a change

Pick the job: **publish**, **watch** an open PR, **fix CI**, or **readiness**. The repository's build file (or AGENTS.md) holds its rules: base branch, required checks, preflight, risk tier, who approves, where heavy work and publishing run. The host's instructions hold the rules for linking, watching and waiting on PRs; if the host gives none, report and return rather than polling.

Every run:

1. `git fetch origin` first, then pin the PR, branch, base and head commit. Everything you report is about that head; results for an older head do not count.
2. Never force-push, rebase someone else's branch, push with hooks skipped, or approve your own change. Merge or mark ready only with the owner's say-so for this change or a standing go the owner or build file records.
3. Never turn a check green by weakening it (baselines, budgets, workflows, test edits, widened types). Flag it as a decision for the owner.
4. A review verdict covers one head. The owner's authorization stays valid within its stated scope unless the build file requires a fresh approval per head; when it does, batch every fix you know about into one push so the owner approves once.

## Publish

If the branch exists on the remote and its tip is not an ancestor of your commit (`git merge-base --is-ancestor origin/<branch> <sha>`), someone else pushed: merge their tip (never force), re-run the required checks on the merged head, and stop only on a conflict. A new branch skips that check. Push the exact commit with hooks on (`git push origin <sha>:refs/heads/<branch>`) and confirm with `git ls-remote origin refs/heads/<branch>`. A push alone does not prove the hooks or checks passed. Open or update the PR as the build file says, link it, and dispatch the checks it requires once.

If you cannot push from here, use only a route the build file names (a runner, a cloud session); otherwise report the exact attempt and error and the one thing the owner must do.

## Watch

Work an open PR one push wave at a time:

1. **Conflicts:** report them; resolve one only by merging the base when the build file allows it, never by rebasing.
2. **Review threads:** decide each with j-review's triage mode; fix the fix items in fix mode.
3. **CI:** classify each failure before touching it. [CI rules](references/ci.md).
4. **One push** with every thread and CI fix together. Then reply in each thread (fix: the commit; already fixed: the commit or line; dismiss: the disproof), resolve only those, and leave ask threads open. Write reply text to a file and post it from there; never put comment or reply text in a shell command.

Stop after three waves, or when only the owner can move it (an approval, an ask item, a conflict). Owner approval is a wait, not a blocker to fix.

## Fix CI

Read the failing job's log for this head and quote the error. Classify it first ([CI rules](references/ci.md)): a failure in code the diff never touches is the base's (already fixed there, or red there too), so update from the base or report it; never patch code outside the diff on the branch. Otherwise reproduce with the cheapest local command that shows it, within the build file's limits on where heavy work runs. Fix only what the check flags, with a test where it is behaviour, and push it in the next wave.

## Readiness

Ready means, at the current head: no merge conflicts (`gh pr view <n> --json mergeable,mergeStateStatus`) and the branch is current with the base if the build file requires it; every required check passes; the review the build file requires covers this head (a verdict on an older head counts only if the diff since is empty); no unresolved thread the build file treats as blocking; and any required approval covers this head. A green check list or an approving bot is not a verdict by itself. An auto-merge request is not a merge: read the PR state back.

## Report

Keep it short. Head, what changed or ran (with run ids), each readiness item not met, and the single decision left for the owner. End with: `PR <full URL>, head <sha>, checks and reviews <state>`.
