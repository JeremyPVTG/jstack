---
name: j-bookmarks
description: Triage saved X (Twitter) bookmarks into a ledger in the research vault, queue the relevant ones for research or as GitHub issues, and work through the queue. Use for "sweep my bookmarks", "what's in my bookmark queue", or "research the bookmark queue".
---

# Bookmarks

Saved posts are a backlog of half-made decisions. This skill gives every bookmark a state in a ledger the owner can check later: **unseen** (on X, not in the ledger yet), **to-research**, **researched** (with the decision and a link to where it lives), or **ignored** (post ID only). It never changes anything on X.

## Requirements

- The [bird CLI](https://github.com/steipete/bird) (`npm i -g @steipete/bird@0.8.0`) reading x.com cookies from a browser the owner is logged in to. That is the owner's choice and risk: it uses X's internal web API, not the official one, and runs only on that machine. Use only `bird bookmarks` and `bird read`.
- A research vault (see [j-research](../j-research/SKILL.md)) and `gh` for areas that file issues.
- `x_bookmarks` in `~/.config/jstack/config.json`:

```json
{
  "research_vault": "~/path/to/vault",
  "x_bookmarks": {
    "ledger": "triage/x-bookmarks.md",
    "areas": {
      "work": {"about": "What counts for this area", "repo": "org/repo", "label": "x-bookmark"},
      "tooling": {"about": "What counts for this area"}
    }
  }
}
```

An area with `repo` gets a GitHub issue for each queued bookmark; the issue is where the research and decision happen. Other areas are researched into the vault.

## Sweep

Run `python3 scripts/x_bookmarks.py sweep`. It:

1. syncs issues (opens any missing, marks bookmarks researched when their issue closes),
2. lists unseen bookmarks, expanding link-only posts to their article,
3. classifies them with a model that has no tools, using [the triage rules](references/triage.md) and the configured areas,
4. records the decisions in the ledger and a line in the vault's `log.md`.

To run it weekly, load a launchd agent that runs `scripts/sweep.sh` (it shows a notification with the counts). To sweep by hand with your own judgement instead, run `new`, decide each item by the triage rules, write the decisions as JSON (`[{"id", "state", "area", "author", "title", "note"}]`) and run `record`.

## Work the queue

When asked to research the queue: run `queue` (optionally with an area), pick what the owner asks for, or the most valuable few, and stay within the j-research budget.

- Vault areas: run j-research on the question the bookmark raises, then record the outcome: `{"id", "state": "researched", "note": "<the decision in one line>", "outcome": "[[Vault page]]"}`.
- Issue areas: work happens in the issue; closing it moves the bookmark to researched on the next sync.

Report what moved and link the ledger.
