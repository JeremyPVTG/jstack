---
name: j-skill-audit
description: Audit and improve a skill collection for routing, overlap, portability, and demonstrated usefulness. Use when pruning, packaging, updating, or evaluating agent skills.
---

# Improve a skill collection

Inventory entrypoints, references, scripts, licenses, install locations, and callers. Distinguish installed availability from demonstrated use. Preserve origin and revision information.

For each skill choose keep, merge, split, delegate upstream, project-local, or retire. Merge only when invocation and outcomes overlap; package related independent skills without loading them all. Move project facts and host mechanics to the owning project or adapter. Remove generic reminders and historical incident details that no longer change a decision.

For upstream choices inspect the actual skill and dependency closure at a recorded revision. Check tool assumptions, invocation policy, external effects, and update behavior. Link rather than copy where possible. A README description alone supports a candidate, not a compatibility claim.

Write concise discriminating descriptions. Keep the entrypoint focused on decisions and essential constraints; load conditional detail from references. Prefer deterministic scripts for repeated computation and extraction.

Evaluate routing with both intended requests and nearby requests that should not trigger. Evaluate behavior on realistic artifacts and observable outcomes, including missing tools, moved revisions, and existing authorization. Compare baseline and candidate on the same cases, recording quality, time, tokens when available, and unintended effects. Independent behavioral runs need permitted tools and sufficient task scope; static validation alone is not a capability benchmark.

Stage changes with rollback and migration notes. Do not call a skill frontier or state of the art without comparative evidence. Report tested behavior separately from planned evaluations.
