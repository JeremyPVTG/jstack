---
name: j-research
description: Research how to build something, answer an open question, or compare options from current sources, compiling what is learned into a persistent research vault. Use for "find a way to build X", "what's best practice for Y", "is there something that already does Z", or decisions that need evidence.
---

# Research

Research compounds: check what is already known, find what is current, and leave the vault better than you found it. Answer the user's actual question; scale the effort to the decision it supports.

## 0. Locate the vault

Use the first that is available:

1. **Vault MCP server** (tools named `guide`, `search`, `read`, `write_page`, `capture_source`, `append_log`, `lint`; see [vault-server](../../vault-server/)). Call `guide` once for the rules and index. Use `search` and `read` to find pages, `capture_source` for raw sources, `write_page` (with the `sha` from `read`) for wiki pages and the index, `append_log`, then `lint`. Works from any device.
2. **Local folder**: `$J_RESEARCH_VAULT`, else `research_vault` in `~/.config/jstack/config.json`. Read its `AGENTS.md` before writing; finish with `scripts/vault_lint.py`.
3. **Neither**: research without a vault and offer once to create one from [the template](assets/vault/).

The vault's own rules override this section.

## 1. Pick the mode

- **Lookup.** A single fact with an authoritative source. Check the vault, search, answer with the source. No pipeline, no new pages unless the fact is reusable.
- **Question.** Explain, compare, or decide. Run steps 2 to 4 and 6.
- **Build.** "Find a way to build X." Run steps 2 to 6 in order. Do not research implementation detail before scope is decided.

## 2. Start from the vault

Read the vault's `index.md`, then the relevant pages. A page is reusable if its `reviewed` date is inside its volatility window (high: 30 days, medium: 90, low: 365). Inside the window, reuse it and cite it. Outside, re-verify only the claims the decision depends on, then update the page. Say which parts came from the vault.

## 3. Landscape: what already exists

Before proposing to build anything, find what people already use. Cover:

- Mature options to adopt or buy: open source projects (activity, last release, licence, issues), hosted services (pricing page, limits), and the platform's own built-in way.
- What practitioners use now and what they regret: run `last30days` on the topic when it is installed, for Reddit, X, YouTube, Hacker News and GitHub discussion. If it is not installed, say the social lane is missing; do not imitate it with a few web searches and call it covered.
- Official docs and primary sources for each serious option, at the current version.

Write an honest brief: each option with what it gives, what it costs, its known failure modes, and evidence quality. Include "adopt X as is" and "don't build this" when the evidence supports them. In Build mode, stop here and hand the brief to `j-scope` (or, if it is unavailable, ask the user the scope decisions directly). Resume at step 5 with the agreed scope.

## 4. Weigh the evidence

Record the version and date for every decisive claim; the vault's freshness checks depend on it. Social and forum posts, including everything last30days returns, are leads and experience reports: confirm how a system behaves against primary sources before relying on it.

## 5. Implementation research (Build mode, after scope)

Research only what is inside the agreed scope. Iterate in rounds:

1. Official docs and reference implementations for the chosen approach; read the code of a good example, not only its README.
2. Gotchas: GitHub issues on the chosen projects, Stack Overflow (check answer date against the version), Reddit and X threads via `last30days`, conference or tutorial videos (transcripts) from practitioners.
3. Follow the strongest sources' own links and citations one hop.
4. After each round, list the questions still open that would change the build. Search those next.

Stop when a round adds nothing that would change the build, or the budget is reached. Deliver a build plan: steps, versions, the reference you are copying from, known pitfalls with their sources, and what is deliberately out of scope.

## 6. Compile into the vault

Follow the vault's `AGENTS.md`. In short: save each decisive source to `raw/` (never edit raw files afterwards), create or update the `wiki/` pages the findings touch, record contradictions on the page instead of silently picking one, update `index.md`, and append one line to `log.md`. Do not save every search hit; save what a future you would need to check the conclusion. Finish with lint (the server's `lint` tool, or `python3 scripts/vault_lint.py <vault>` from this skill's directory) and fix any errors it reports.

## Report

Lead with the answer and link the vault page; the detail lives there.

## Cost

Free sources first. Before paid calls beyond normal search (deep-research agents, X post fetches, scraping credits), state the expected cost; stay under about $2 per run unless the user sets a budget. Tool notes and current pricing: [sources](references/sources.md).
