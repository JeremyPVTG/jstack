# 0001: Research sources and the research vault

Date: 2026-11-07. Status: accepted.

## Context

Research was the request I made most often across 120 days of agent history, and the pushback I gave most was about agents building things I didn't need, or recommending without checking whether a mature option already existed. I wanted one research skill I could give any agent, that stays current, covers practitioner sources (Reddit, X, YouTube, Stack Overflow) as well as docs, and compounds across runs instead of starting from zero.

## Decisions

**Landscape before implementation, with scope in between.** j-research first establishes what already exists, including "adopt X" and "don't build this". j-scope then questions me to set the MVP line, and only then does j-research go deep on implementation, within that line. This puts the "is there something fully cooked?" and "what does this give us that we don't already have?" checks before effort is spent.

**Depend on last30days for the social lane.** [last30days](https://github.com/mvanhorn/last30days-skill) (MIT, about 67k stars, active on 2026-11-07) already searches Reddit, X, YouTube transcripts, Hacker News and GitHub with engagement scoring and works across agent hosts. Rebuilding that would be the kind of duplication j-scope exists to stop. Costs accepted: it is heavy (a 31 KB skill and a Python 3.12 engine), its default window is 30 days, so it reports current practice rather than durable reference material, and a host without it loses the social lane. j-research says so instead of faking coverage with a few web searches. Docs, code, Stack Overflow and issues come from ordinary search and `gh`.

**X through xAI's API, not browser cookies.** `x_search` costs $5 per 1,000 posts fetched (from 2026-09-21), so a typical run costs well under $1. The cookie route is free but uses my logged-in X session. The skills.sh scan rates last30days as high risk; the safeguards are refusing cookie access, keeping keys in the secrets manager, and pinning the reviewed revision.

**A dedicated research vault using Karpathy's LLM wiki pattern.** Raw captures are immutable; the agent compiles wiki pages; `index.md` and `log.md` keep it navigable; a schema file in the vault holds the rules. I added two fields for staying current: `reviewed` and `volatility` on every page, so a run reuses fresh pages and re-verifies only stale, decision-relevant claims. A separate vault keeps high-volume captures out of my personal thinking vault. No vector database: Karpathy reports the index file works at moderate scale, and a search tool such as qmd can be added when it stops fitting.

## Rejected

- Building my own social adapters: duplicates last30days.
- Embeddings or RAG infrastructure up front: unneeded at current size.
- A fixed "search every source every time" pipeline: wasteful for lookups. The skill has lookup, question and build modes.

## Revisit when

- Evals show the landscape step doesn't change recommendations compared with no skill.
- last30days changes licence, stops being maintained, or its security posture gets worse.
- `index.md` no longer fits comfortably in an agent's context.
