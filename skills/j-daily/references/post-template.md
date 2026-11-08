# Daily log template

The blog renders MDX with YAML frontmatter. Keep these keys; the site reads them for the index, RSS and preview images.

```mdx
---
title: "<what the day was about, plain words, under 70 characters>"
date: "YYYY-MM-DD"
kind: "log"            # "essay" for a longer post
tags: ["<role-track tag>", "<topic>"]
summary: "<one sentence a reader can act on>"
draft: true            # the owner flips this when the take is written
---

## What I did

<3 to 6 short paragraphs or bullets, one per thread of work: what happened, what changed, a link to the
public evidence (a merged PR in a public repo, a published page). Facts only, past tense.>

## What I learned

{/* Questions for the owner. Answer one or two in your own words, then delete these comments.
1. <a question that points at a real surprise from the day, with the number or result behind it>
2. <...>
3. <...>
*/}

## Links

- <public links only>
```

Rules for the draft:

- "What I did" is first person and factual ("I merged...", "I measured..."), because the owner did the work. No adjectives about how it went, no claims about what it means.
- "What I learned" stays empty apart from the question comment. The owner writes the take.
- A question names the specific fact it is about ("60% of sessions came from data-centre IPs") so the owner can answer in one sitting.
- Essays use the same frontmatter with `kind: "essay"`, a working title, and a body that is only an outline plus an evidence list (vault pages, PRs, numbers with their sources).
