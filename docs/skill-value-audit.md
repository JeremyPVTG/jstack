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

## Remaining proof

Run matched baseline/candidate trials on the existing development cases in T3. Include a no-added-skill condition: if T3 and the model already handle a behavior reliably, repeating it in jstack may add no value. Track unnecessary loading, questions, artifacts, tool calls, and cost alongside task success.

Use negative controls: simple lookup, clean diff, already-fixed finding, and an accurate status claim. A skill that adds ceremonies or creates work on these cases fails the value test even if its prose sounds rigorous.

Retain separate skills only if discovery can distinguish them. If j-research and j-evidence repeatedly misroute, revise their descriptions before merging their different outcomes. Do not expand the stack until these candidates show a useful tradeoff.
