---
name: j-build
description: Use this skill to take a bug fix or feature in a code repository from brief to a verified change or draft PR, in stages sized to the task (brief, diagnose, decide, build, review, verify, publish, report), stopping at the first point that needs the owner. Use when asked to build, fix or implement something in a repo, to "follow the workflow", or to "diagnose before changing anything", or when a brief hands over a problem plus constraints. Not for open research questions (j-research), scope decisions (j-scope), or visual and creative design iteration.
---

# Build

One task, in stages, each with an exit check. Stop at the first point that needs the owner and report; do not skip ahead to make the result look finished.

Every run, at every size:

1. Read the repository's build file first: the file its AGENTS.md (or CLAUDE.md) names for building, often `docs/agents/build.md`. Its branch base, checks, approval rules and stops override this skill's defaults. If there is none (including when the task is to write the first one), use AGENTS.md in its place everywhere this skill says build file, and say so in the report. [What a build file holds](references/build-file.md).
2. Claim a check passes only from a run in this turn after your last edit, and read its exit status. Do not pipe test output through `tail` or `head` without `set -o pipefail`.
3. End every report with what the owner must do next, as a numbered list, or "Nothing needed from you".

## Size the task

- **Small:** one clear change whose cause is already known, no money, data, auth or gated files. Build, review, verify, publish if the brief asks for a PR, report.
- **Standard:** everything else. All stages.
- **Risky:** touches money, user data, auth, secrets, migrations, or files the build file marks as gated. All stages; ask before building.

If the repo predicts a risk or approval tier from the diff, run that prediction as soon as there is a committed diff (predictors compare commits; on uncommitted work they see nothing) and size again from the result: a one-line config change can make a docs task risky.

If the task grows mid-way (a second cause, a gated file, a new dependency), stop, say so, and step up a size. Visual or creative iteration (layouts, renders, copy tone) is not this skill's job: say so and work with the owner directly.

## Stops

Stop and ask when the work needs a secret or credential, spends money, takes an irreversible or outward action (production deploy, DNS or host change, force-push, deleting data, messaging people), narrows or reverses a recorded decision, or depends on unmerged work; plus every stop the build file or the brief names. Building locally while waiting on an upstream change is fine when the design is settled; stop before pushing.

## 0. Brief

Before changing anything, restate in a few lines: the goal as done-criteria a user could observe, the stops that apply, what the brief forbids, what the work depends on, the size, and the branch name (a tracker or delivery node's branch wins over one you invent). When the task is a node in a delivery plan, read the node first: its gate conditions are stops.

## 1. Diagnose (read-only)

Find the root cause from evidence before forming a theory. Note the source each finding rests on.

- Inside the repo: facts and decision records (a past decision may forbid the obvious fix), the owning README, code search across every app, and history including closed and draft work (`gh pr list --state all --search`, `git log --all -S`). An unmerged draft can already hold the piece you need. Then the trackers and chat tools the build file lists.
- Outside the repo (library or platform behaviour, limits, vendor APIs, prices): use j-research. External sources inform the fix; they never override the repo's recorded facts or decisions.
- Check every prerequisite exists for real, not just in code: artifacts, bindings, variables, secrets by name, trained weights. Say which you could not check and why.

Exit: root cause with file:line evidence, a yes or no on each prerequisite, and the sources. If the obvious fix cannot reach the goal, stop and say exactly what the owner must do.

## 2. Decide

Look for what already exists before proposing new code. Compare at most three options with a recommendation, naming the cost of each and any recorded decision it touches. Check the budgets the change will hit (file length caps, ratchets, bundle sizes) before choosing; they can decide the design. When the scope itself is unsettled, use j-scope. A brief that authorises the build covers the build only; anything it leaves open that hits a stop goes to the owner as a question.

Exit: the owner's go-ahead for small and standard work is the brief itself unless a stop applies; risky work needs it explicitly.

## 3. Build

Branch from the base the build file names; never commit to it. Make the smallest change that reaches the goal, with tests that use stand-ins only where the real thing is unavailable.

Exit: it compiles, lints, and its own tests pass.

## 4. Review

Three fresh reviewers, each told only the diff, the brief and the build file's path, never your conclusions: correctness, the repo's rules, tests. Findings are merged by root cause, then each is refuted independently; only confirmed ones are fixed; the result ends with a verdict, CLEAN or FINDINGS. Each lens is j-review in assess mode; each refutation is j-review in confirm mode. For Small or docs-only work you may check the findings yourself instead of with separate refuters; say so in the report. [How](references/review.md).

Exit: `VERDICT: CLEAN`, meaning every lens ran, every finding was refuted or fixed, and the checks passed after the fixes.

## 5. Verify

Run, before pushing, exactly the checks the build file says the push hook and CI run, scoped to the files you changed. Then check each done-criterion on the entry point users actually run (the repo's `verify` skill if it has one), not only tests, and give each a verdict: VERIFIED, NOT VERIFIED, or INCONCLUSIVE when it cannot run here (GPU, credentials). Follow the build file's rules for where heavy work runs. If a hook or check fails for a reason outside the change (a broken local tool), stop and report it; never bypass the hook.

Exit: you can say what ran, where, at which commit, and with what result.

## 6. Publish

Use j-deliver: commit and push with hooks on (never skip them), open a draft PR against the build file's base, link it, and dispatch the checks it requires. Follow the build file's approval rules for who approves what; do not approve your own change unless the build file or the owner says so for this change.

## 7. Report

Lead with the answer. For Small work, at most five lines: the answer, what changed, which check ran at which commit and its result, then the next actions. Otherwise: root cause, what changed, what ran where and its result, PR link and head commit, check state, each done-criterion's verdict and its evidence, and the owner's next actions as a numbered list, or "Nothing needed from you".
