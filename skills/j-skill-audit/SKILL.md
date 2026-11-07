---
name: j-skill-audit
description: Prune or rework agent skills by checking instruction value, overlap, dependencies, and observed task outcomes. Use for skill audits and consolidation, not ordinary code review.
---

# Audit a skill collection

For each skill, identify its intended task and the decision it improves beyond the model and current host instructions. Inspect callers, references, scripts, and provenance before deleting or merging it. Installed availability is not usage evidence.

Choose keep, narrow, merge, move to the project, use upstream, or retire. Remove duplicated host rules and generic advice. Merge shared outcomes, not merely shared vocabulary; a pack need not load all its skills.

Inspect upstream entrypoints and dependencies at a recorded revision before recommending replacement. Preserve attribution and flag unverified compatibility.

Compare candidate and baseline on realistic tasks, including close non-triggers, with matched settings. Judge actual outcomes, friction, and cost. Shorter text and valid metadata do not prove improvement.

Stage reversible changes and identify what still needs behavioral evidence. Retain a skill only when its benefit justifies its maintenance and context cost.
