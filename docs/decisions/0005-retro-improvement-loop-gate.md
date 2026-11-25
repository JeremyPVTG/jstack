# 0005: Gate automated skill changes on frozen, separately authored cases

Date: 2026-11-25. Status: accepted.

## Context

A loop now turns retro findings from j-launch retrospectives into skill changes and opens draft pull requests without the owner in the middle. The risk is "measurable improvement" manufactured by the agent that also wrote the change: agents edit or special-case visible tests (ImpossibleBench, arXiv 2510.20270), and published self-improvement loops warn about overfitting to their own grader. On the owner's machine every agent thread can reach GitHub and the private vault, so no case can be truly hidden from the implementer. `claude plugin eval` runs and judges with Claude models only, and the owner's rule is that Claude models never judge.

## Decision

- A separate eval author (GPT Sol) writes the target case, a reworded soft holdout and over-refusal controls before any skill text changes. They are frozen by hash; the gate fails if a hash changes. The implementer (Opus) gets the finding, not the assertions; the soft holdout stays outside its workspace until the gate runs.
- The baseline must reproduce the failure first (target case fails at least 2 of 3 runs per model), or the finding returns to Investigate.
- The gate is deterministic, per model (Opus and Sonnet), incumbent and candidate alternating on fresh workspaces: target 5/5 for the candidate and at most 1/5 for the incumbent; soft holdout at least 3/5; controls and the owning skill's existing probes drop by no more than one run of three; zero critical failures; SKILL.md grows no more than 20%. GPT Sol and Grok fast judge saved traces blind, as advice only.
- Caps: two attempts and $100 per finding, $500 per month with a check-in at $300, one open draft PR per skill, and a kill-switch file. Draft PRs only; the owner merges.

## Consequences

Accepted changes carry development evidence, not holdout evidence, and are tested on Claude models only; each PR says so. A GPT runner and a credential-isolated evaluator are follow-ups, not prerequisites.
