---
name: j-research
description: Use this skill before answering any question that depends on facts that can change: versions, prices, limits, best practice, what tools or services exist, whether something is ready for production, or how to build or choose something. It checks the research vault first, searches current sources, and saves what it learns. Training knowledge is not enough for these questions. Not for code edits, writing, or explaining stable concepts.
---

# Research

Research compounds: check what is already known, find what is current, and leave the vault better than you found it. Answer the user's actual question; scale the effort to the decision it supports.

## 0. Vault

Use the vault MCP server if connected (call its `guide` once), else the local vault folder, else work without one ([vault access](references/vault.md)). The vault's own rules override this skill.

## 1. Pick the mode

- **Lookup.** A single fact with an authoritative source. Check the vault, search, answer with the source. No pipeline, no new pages unless the fact is reusable.
- **Question.** Explain, compare, or decide. Run steps 2 to 4 and 6.
- **Build.** "Find a way to build X." Run steps 2 to 6 in order. Do not research implementation detail before scope is decided.

## 2. Start from the vault

Read `index.md`, then the relevant pages. A page is reusable inside its volatility window (high: 30 days, medium: 90, low: 365): cite it. Outside, re-verify only the claims the decision depends on, then update the page. A page superseded by another is history: read its successor. Say which parts came from the vault.

## 3. Landscape: what already exists

Before proposing to build anything, find what people already use: mature open source projects (activity, last release, licence, issues), hosted services (pricing, limits), the platform's built-in way, and official docs for each at the current version. For what practitioners use and regret, run `last30days`; if it is not installed, say the social lane is missing rather than imitating it with a few web searches.

Pick search tools per lane from [sources](references/sources.md). When two or more lanes need real digging, give each to a subagent with a fresh context and a short brief (the question, its lane, what the vault already says), all in one message, and synthesize the results yourself. One-lane questions stay inline.

Write an honest brief: each option with what it gives, what it costs, its failure modes, and evidence quality, including "adopt X as is" and "don't build this" when the evidence supports them. In Build mode, stop here and hand the brief to `j-scope` (or ask the user the scope decisions directly), then resume at step 5 inside the agreed scope.

## 4. Weigh the evidence

Record the version and date of every decisive claim; freshness checks depend on it. Social and forum posts are leads: confirm behaviour against primary sources. Keep what sources say (cited), what you infer, and what is still unknown separate.

When sources conflict, are thin, or are only vendor claims, and a small experiment would settle it (a test call, a trial run, a benchmark on your own data), run it within budget and save its setup and results to `raw/` as a dataset. A measured result outranks any number of posts about it.

## 5. Implementation research (Build mode, after scope)

Work in rounds, inside the scope only: official docs and the code of a good reference implementation; then gotchas from GitHub issues, Stack Overflow (check answer dates against the version), practitioner threads via `last30days` and talk transcripts; then one hop along the best sources' own links. After each round, list the open questions that would change the build and search those next. Stop when a round changes nothing or the budget is reached.

Deliver a build plan: steps, versions, the reference you copy from, known pitfalls with sources, and what is deliberately out of scope.

## 6. Compile into the vault

Follow the vault's `AGENTS.md`: save each decisive source to `raw/` (never edited afterwards), create or update the `wiki/` pages the findings touch, record contradictions on the page instead of silently picking one, update `index.md`, append one line to `log.md`, then lint and fix errors. Save what a future you needs to check the conclusion, not every search hit.

## Report

Lead with the answer and link the vault page; the detail lives there. End with one coverage line: each lane searched, the providers used and what each gave, including empty or missing ones (for example "social: last30days not installed").

When the research feeds a build, buy, or scope decision and the vault has a research council brief, offer that review before the decision is acted on.

## Cost

Free sources first. State the expected cost before paid calls; stay under about $2 per run unless the user sets a budget, and record the approximate paid spend in the log line. Tools and pricing: [sources](references/sources.md).
