---
name: j-deliver
description: Use this skill to publish a finished change (push the exact commit with hooks on and open or update the PR), to watch an open pull request through conflicts, review threads and CI until it is ready, to diagnose and fix a failing check, or to decide whether a PR is ready to merge. Use when a brief says publish, push commit X, test and publish, fix CI, checks failed, babysit the PR, is PR N ready, or hand off PR N.
---

# Deliver a change

Pick the job: **publish**, **watch** an open PR, **fix CI**, or **readiness**. The repository's build file (or AGENTS.md) holds its rules: base branch, required checks, preflight, risk tier, who approves, where heavy work and publishing run. The host's own instructions hold the PR rules for linking, watching and waiting; follow them rather than inventing a loop.

Every run:

1. Pin the PR, branch, base and head commit. Everything you report is about that head; results for an older head do not count.
2. Never force-push, rebase someone else's branch, push with hooks skipped, or merge, approve or mark ready without the owner's say-so for this change.
3. Never turn a check green by weakening it (baselines, budgets, workflows, test edits, widened types). Flag it as a decision for the owner.
4. An approval or verdict covers one head. Batch every fix you know about into one push, so the owner approves once, not per fix.

## Publish

Check the remote branch tip is an ancestor of the commit you push (`git merge-base --is-ancestor`); if not, stop rather than lose someone's work. Push the exact commit with hooks on (`git push origin <sha>:refs/heads/<branch>`), then confirm with `git ls-remote`. A push alone does not prove the hooks or checks passed. Open or update the PR as the build file says, link it, and dispatch the checks it requires once.

If you cannot push from here (no login, a host without memory for the hooks), look for the route the build file or earlier runs used (a runner, a cloud session, the owner's machine) before stopping; if none works, report the exact attempt and error and the one thing the owner must do.

## Watch

Work an open PR in this order, one push wave at a time:

1. **Conflicts:** report them; do not resolve a conflict by rebasing or rewriting history unless the owner says so.
2. **Review threads:** triage them with j-review's triage mode (fix, dismiss with proof, or ask).
3. **CI:** classify each failure before touching it. [CI rules](references/ci.md).

Stop after three fix waves, or when only the owner can move it (an approval, an ask-level finding, a conflict). Owner approval is a wait, not a blocker to fix.

## Fix CI

Read the failing job's log for this head and quote the error. Reproduce with the cheapest local command that shows it, within the build file's limits on where heavy work runs. Fix only what the check flags, with a test where it is behaviour, and push in the next wave.

## Readiness

Ready means, at the current head: every required check passes, the review the build file requires covers this head (a verdict on an older head counts only if the diff since is empty), no unresolved thread that the build file treats as blocking, and any required approval names this head. A green check list or an approving bot is not a verdict by itself. An auto-merge request is not a merge: read the PR state back.

## Report

Keep it short. Head, what changed or ran (with run ids), each readiness item that is not met, and the single decision left for the owner. End with: `PR <full URL>, head <sha>, checks and reviews <state>`.
