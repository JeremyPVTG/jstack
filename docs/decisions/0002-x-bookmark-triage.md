# 0002: X bookmark triage

Date: 2026-11-07. Status: accepted.

## Context

Saved X posts pile up unread. The useful ones belong to a few areas the owner configures; many are noise, and some are content that must never reach the vault. The owner wants to check later what was decided about any bookmark.

## Decision

- One ledger file in the research vault with four states: unseen (derived: on X, not in the ledger), to-research, researched, ignored. Researched rows link to where the decision lives: a vault page, or a GitHub issue for the company area.
- Ignored rows keep only the post ID. Nothing else about them is written anywhere.
- Read with the bird CLI using browser cookies, by the owner's explicit choice and at their risk. Only `bird bookmarks` and `bird read` are used; X is never changed (no unbookmarking, no folder moves).
- Classification runs on a model with no tools and a JSON schema. Post text can contain instructions, so the step that reads untrusted text cannot act; a deterministic script validates decisions and does every write, including opening issues.
- Deep research runs only on request; the weekly sweep only sorts.

## Rejected

- Official X API: pay per read and a developer app for one person's bookmarks; revisit if cookie access breaks.
- Unbookmarking processed posts: irreversible and unnecessary once the ledger holds the state.
- Letting the classifying agent open issues or write files directly: one injected post could act.

## Results so far

First run, 2026-11-07: 195 bookmarks; 39 queued across the configured areas, 156 ignored, including every post in the never-record category. A second run changed nothing.

## Revisit when

bird stops working (it is marked deprecated on npm at 0.8.0), the ignored share hides things the owner wanted, or the issue volume is unwelcome in the company repository.
