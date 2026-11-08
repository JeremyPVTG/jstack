# Research vault

A persistent, compounding research wiki maintained by agents and read by a person in Obsidian. Pattern from [Karpathy's LLM wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f): raw sources stay untouched, the agent compiles them into linked pages, and this file holds the rules. Edit this file as the vault's needs change.

## Layout

- `raw/YYYY-MM/` captured sources. One file per source. Never edit after capture; if a source changes, capture it again.
- `wiki/` compiled pages, flat, one idea per page. The agent writes these.
- `index.md` every wiki page with a one-line summary, grouped by type. Read it first.
- `log.md` append-only record of ingests, research runs, and lint passes.

## Raw source files

Name: `YYYY-MM-DD short-slug.md`. Frontmatter:

```yaml
url:
title:
author:
published:       # YYYY-MM-DD, or unknown
captured:        # YYYY-MM-DD
kind:            # docs | code | paper | forum | video | social | article | dataset
version:         # software version the source describes, if any
```

Body: the relevant extract (not the whole page unless it is short), with the passages that support a conclusion kept verbatim. For video, keep timestamps.

## Wiki pages

Name: plain title, e.g. `Postgres row level security.md`. Frontmatter:

```yaml
type:            # topic | entity | comparison | decision
reviewed:        # YYYY-MM-DD, when the claims were last checked
volatility:      # high (30 days) | medium (90) | low (365)
sources:         # one quoted wikilink per line
  - "[[raw/YYYY-MM/YYYY-MM-DD short-slug]]"
supersedes:      # optional: pages this one replaces
  - "[[Older page]]"
contradicts:     # optional: pages whose claims this one disputes
  - "[[Other page]]"
```

- **topic**: a question researched, with the current answer first.
- **entity**: a tool, library, service, organisation, or person.
- **comparison**: options weighed against each other.
- **decision**: what was chosen, what was ruled out, and why, including scope decisions.

Rules:

- Every non-obvious claim links to a raw source, with the version or date it applies to.
- When sources disagree, keep both under `## Contradictions` with their dates. Do not delete the older claim; mark it superseded.
- When a page replaces another, list it under `supersedes` and add a link back from the old page to the new one; when a page disputes another, list it under `contradicts` and link back under the other page's `## Contradictions`. Lint checks both.
- Link pages with `[[wikilinks]]`. Prefer updating an existing page over creating a near-duplicate.
- Mark your own inferences as inference.
- No emoji.

## Operations

- **Research run.** Read `index.md` and relevant pages, research, capture decisive sources to `raw/`, update the pages they touch, update `index.md`, log it.
- **Ingest.** A person drops a file in `raw/`: summarise it, update the pages it touches, log it.
- **Lint.** End every session that writes here with `python3 <j-research skill>/scripts/vault_lint.py <this vault>`. Fix every error (broken links, missing frontmatter, pages missing from the index). Warnings list stale pages and orphans; re-verify stale pages the next time their topic comes up, and link orphans from a related page. Contradictions between pages need judgement, not the script: check them when updating a page.

## Log format

One line per event, greppable. Add `| spend: ~$X` when the run paid for searches, scraping or models:

```
## [YYYY-MM-DD] research | Question or topic | pages: [[A]], [[B]] | spend: ~$0.10
## [YYYY-MM-DD] ingest | Source title | pages: [[A]]
## [YYYY-MM-DD] lint | 3 stale, 1 contradiction
```
