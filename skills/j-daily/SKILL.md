---
name: j-daily
description: Use this skill when the owner asks what they did today (or on a given day), wants to plan or draft a daily log or blog post about what they learned, or when a scheduled run asks for the daily draft. It gathers the day's research, pull requests, commits and agent conversations, then opens a draft post PR with questions for the owner to answer. Not for writing finished opinion pieces in the owner's name, and not for publishing.
---

# Daily log

The owner wants a short daily log of what they learned, written by them, from a record of what they actually did. You gather the facts and ask good questions; they write the take and decide what goes public.

## Rules

- Never write an opinion, lesson or conclusion as the owner. "What I did" is facts; "What I learned" is the owner's questions to answer.
- Open a PR only when the owner asks for a draft post or PR, or a scheduled run asks for the daily draft. "What did I do?" and planning requests stop after step 3; a request to see a draft stops after step 5.
- Never merge, publish, or push to the blog's default branch. Merging the PR is the owner's approval.
- The leak check flags; it never blocks or edits. Put every hit in the PR body.
- A quiet day gets no PR. Say what was there and why it is not worth a post.
- Run once per day: if a PR for that day's branch already exists, report it and stop.

## Config

In `~/.config/jstack/config.json`, beside `research_vault`:

```json
"daily": {
  "blog_repo": "~/path/to/site",
  "posts_dir": "content/blog",
  "denylist": "~/.config/jstack/daily-denylist.txt",
  "voice": "~/path/to/voice.md",
  "repo_roots": ["~"],
  "author_emails": [],
  "t3_state": "~/.t3/userdata/statev2.sqlite"
}
```

Only `blog_repo` is needed to open a PR; without it, do a dry run. The deny list is one term per line (people, places, clients, internal names). `voice` is the owner's writing rules; follow them for the facts you write.

## Steps

1. **Collect.** Run `python3 scripts/collect_day.py --out <tmp>/day.json` (`--date YYYY-MM-DD` for another day). Read its summary line; a source with an error is a gap to mention, not a reason to stop.
2. **Digest.** Group the day into 3 to 6 threads of work. Join the sources: a vault entry, the PR it led to, and the messages and answers where the owner decided it are one thread. Use the owner's answers to questions as the record of their decisions.
3. **Plan.** Pick the one or two threads with a real surprise or decision. Write 2 or 3 questions, each naming the fact behind it. Say which thread could grow into an essay.
4. **Draft.** Fill [the template](references/post-template.md) as `YYYY-MM-DD-<slug>.mdx`, in a temporary folder until step 6 places it in `<posts_dir>`. Link only public evidence. Keep private repo names, people and internal numbers out unless the owner has already made them public.
5. **Check.** Run `python3 scripts/leak_check.py <draft> --day <tmp>/day.json`.
6. **Open the PR** in `blog_repo`: branch `blog/YYYY-MM-DD` from the latest default branch, one commit with the draft, committed as the owner's normal git identity, then `gh pr create --draft`. Title `Daily log: YYYY-MM-DD`. Body: the questions, the thread digest, the leak check output, and which sources had gaps.

Without `blog_repo`, or when the "Open a PR only" rule does not allow one, stop at the step that rule names and show what you have (the digest and questions, or the draft and leak check).

## Essays

When the owner asks for an essay on a topic: search the vault and past posts for it and show an outline with the evidence list. Do not write the essay. If they ask for a PR, open a draft one with `kind: "essay"` the same way as step 6.

## Report

The PR link (or the dry-run draft), the questions, the leak check hits, and any source gaps.
