# Skill value audit — 2026-11-07

Scope: the five owned jstack skills, their references, pack membership, and duplication with the T3 instructions available during this audit. Upstream collections and the full installed personal skill library are outside this pass.

Verdict: retain four task-facing skills as candidates and keep the audit skill optional. None has demonstrated incremental model performance yet. Installed usage and historical workflow frequency motivate the candidates; they do not establish that the rewritten skills help.

## What earns its place

- **j-review:** reachable-failure evidence, revision-scoped verdicts, and reconciliation of previous findings. Keep separate from delivery: correctness assessment is not release readiness. Prove value by finding a real defect without inventing one in the clean case; confirmation should avoid reopening unrelated work.
- **j-deliver:** current-head checks and approval scope, remote divergence, and distinctions between dispatch and completion. Keep PR operations governed by T3 and the repository. Prove value on stale green checks and collaborator updates, while still completing an authorized repair.
- **j-evidence:** the distinction between proposed, saved, executed, and observed state, plus tracker readback and claim support. This captures a repeated user need. Prove value by making supported updates and retaining uncertainty where evidence conflicts; blanket refusal is failure.
- **j-research:** source-level claim support, counterevidence, version conflicts, and stopping when evidence saturates. Prove value on an actionable comparison and a misleading set of repeated outdated summaries. Avoid imposing a report or ledger on a simple lookup.
- **j-skill-audit:** instruction value and overlap analysis. Keep in the optional maintainer pack. Its ongoing value is least established; if it adds no useful result over the host's skill-authoring guidance, retire it rather than preserving it for symmetry.

## Changes made

Removed generic planning reminders, repeated authorization and tool-discovery lists, and duplicated host mechanics. Folded both tiny reference files into the relevant entrypoints and removed them after checking their callers. Retained task-specific invariants rather than moving deleted prose into another always-loaded file.

Narrowed descriptions to distinguish investigation from reconciliation and code assessment from release state. No new orchestration, mandatory subagents, scorecards, or storage machinery was added.

The previous committed version remains recoverable from Git. Existing installations were not migrated. The evaluation repository preserves its previous subject pin as the comparison baseline and records the new candidate separately.

## 2026-11-08 rebuild of j-review and j-deliver

j-review and j-deliver were rebuilt to replace the owner's personal pr-* skills after a usage analysis of 157 sessions (decision recorded outside this repo). Each now has one reference file again (comment triage; CI classification) and j-deliver works an open PR through conflicts, threads and CI in push waves, which reverses "no new orchestration" for that skill. The boundary above holds: j-review decides (verdict, confirmation, triage decisions, code fixes); j-deliver changes external PR state (push, replies, thread resolution, readiness). Authorization keeps its stated scope; a fresh approval per head applies only where the build file requires it. Measured on four targeted probes (Sonnet, three runs each, with the old pr-* skills and no skill as controls): new 30/30, old 20/30, none 19/30. The gain is in comment triage (12/12 against 9/12 and 8/12) and in classifying a CI failure the base already fixes (6/6 against 0/6 for both controls, which patched the base's code on the branch). Two probes, round-two and gate-loosening, sit at ceiling in every arm and show nothing. j-deliver loaded on CI briefs only after its description led with failing checks. Harness and results: jstack-evals `harness/j-review-deliver/RESULTS.md` (commit 4d24d10). A live PR pilot is still pending.

## 2026-11-08 verification: pstack adopted, no j-verify

A jstack j-verify was built twice and dropped twice. The second version (create and maintain a repository's verify skill, plus an independent verdict on base and head) got its verdict right 1 of 3 times on a seeded probe where the author's own check without the skill caught the break 3 of 3 (jstack-evals d119977). Its create mode worked on a real repository, but that design is pstack's. So jstack points at pstack's create-verification-skill and maintain-verification-skill under their own name (pinned in upstreams.lock.json), j-build's Verify stage names them, and j-deliver's readiness takes pstack Shipping's rule: where the build file requires it, a pass from an agent that did not write the change, valid while the patch-id matches. Unmeasured; comes back as a skill only if a live PR shows authors missing breaks that driving the app catches.

## Remaining proof

Run matched baseline/candidate trials on the existing development cases in T3. Include a no-added-skill condition: if T3 and the model already handle a behavior reliably, repeating it in jstack may add no value. Track unnecessary loading, questions, artifacts, tool calls, and cost alongside task success.

Use negative controls: simple lookup, clean diff, already-fixed finding, and an accurate status claim. A skill that adds ceremonies or creates work on these cases fails the value test even if its prose sounds rigorous.

Retain separate skills only if discovery can distinguish them. If j-research and j-evidence repeatedly misroute, revise their descriptions before merging their different outcomes. Do not expand the stack until these candidates show a useful tradeoff.
