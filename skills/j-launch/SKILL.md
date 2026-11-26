---
name: j-launch
description: Start a piece of work in a new T3 thread with the right skills from each installed collection (mattpocock, pstack, jstack) loaded or named, a brief that carries what only this conversation knows, and a check that the skills actually loaded. Use when asked to start, launch or hand off work "in a new thread", or for "j-launch".
---

# Launch

A new thread starts cold: it reads its project's files and its own memory, and nothing else from this conversation. The launch decides which skills drive it and hands over what this conversation learned that no file records yet. Everything the thread gets from you is its first message.

## 1. Pin the work

- Name the work item and its done line: a ticket, a map, a PR, a question. Read its state from the tracker immediately before you launch, the item itself included (open or closed, claimed by whom, which PRs are merged, what merged on the base since you last looked). Other sessions move the same tracker while you prepare; a brief written from an earlier read sends the thread after work that is already finished.
- Find the base: the trunk the project's instruction file names. Whatever the work depends on must already be on that base, or the brief names its branch or PR. An unmerged dependency is the usual reason a cold thread cannot find a decision; when one is ready, ask the owner whether to merge it first.

## 2. Pick the skills

Before selecting the owner or launching, evaluate **all three collections**: mattpocock, pstack, and jstack. Put a selection record in the launch brief with exactly one row per collection: candidates considered, skills selected with their role, or a task-specific reason for selecting none. An unavailable collection is recorded as unavailable, never silently skipped. Consideration is mandatory; using a skill from every collection is not.

This is a launch gate: do not call the launch tool until all three rows are complete and project-required workflows are accounted for. Resolve conflicts through the project's instructions, and choose one owner rather than stacking competing end-to-end workflows.

- Name one **owner** skill: the workflow that runs the work end to end. Add the helpers it calls or the work needs, and the skill that ships the result. [Routing](references/routing.md) lists the usual pairings.
- Pick from this session's skill catalog, not from memory: each name must exist and its description must fit the work. The project's instruction file wins: when it names a workflow for this kind of work, or restricts a skill, follow it.
- Read each chosen skill's frontmatter. `disable-model-invocation: true` marks a **user-only** skill: no agent can load it, but a message that starts with its slash command does. Every other skill loads when the brief names it ("use j-deliver to merge the PR").
- One slash command can lead a message. When the work needs a second user-only skill, launch with the owner and tell the owner the second command to type in that thread.

## 3. Write the brief

- With a user-only owner, the message is `/<skill> <brief>`: the command, then the brief as its arguments. Otherwise the message is the brief.
- The brief includes the three-collection selection record and a closing retrospective requirement from step 5 that names j-launch, so the thread loads the filing steps from their source.
- The brief holds: the goal and done line; links to the work item and its inputs; each skill by name with when to use it; decisions made in this conversation that no file holds yet; traps found here, with their evidence; what is ruled out; and when to stop for the owner.
- Leave out what the thread reads for itself: the project's instruction files, the owner's standing rules and memory, each skill's own steps. A restated rule drifts from its source.

## 4. Launch and check

- Start one top-level thread under the host's rules for new threads: a fresh worktree from the base, the owner's model and modes unless the owner named others, and a title naming the work item.
- Read the thread's activity once after it starts. Each user-only skill must show as loaded (its instructions in the thread, not your command as plain text), and the thread must be working on the item you named. If a command arrived as text, give the owner the exact command to type there.
- Hand back the thread's link, each skill with how it was loaded, the work item's link, and anything the owner must type or decide.

## 5. Close with a routing retrospective

Require the launched thread to finish with a short retrospective after verification, or when blocked. Use mattpocock `retro` if available and permitted by its invocation metadata; otherwise perform this bounded review directly. Do not start a replacement thread, delegate, or extra model call for this step or its filing.

Compare the selection record with actual execution: which skills were loaded and used, which helped, which duplicated or conflicted, and whether any omitted collection offered a better fit. Ground findings in observed rework, missed checks, blockers, or unnecessary tool calls. Recommend the best owner/helper/shipping combination for the next similar task, with a reason; if evidence is insufficient, say so. A successful result alone does not prove the skill choice was best.

Report concrete routing improvements to the owner. A recommendation does not authorize edits to skills, project instructions, settings, or memory. Preserve the task's existing approval boundaries.

File each **retro finding** in jstack's public tracker (`JeremyPVTG/jstack` on GitHub), whatever project the thread ran in. A retro finding is a concrete failure, repeated friction, missed check or workflow conflict the review observed, with its evidence; a preference or an untested idea stays in the report. For each one:

1. **Evidence.** Save the raw evidence (thread excerpts, commands and output) as a page in the owner's private research vault. A vault checkout counts (see j-research's vault access); with neither the vault server nor the vault's git repository reachable, report the finding and file nothing.
2. **Search.** List open findings with `gh issue list --repo JeremyPVTG/jstack --label retro-finding --search "<keywords>"` and read the likely matches. A match is an open finding about the same failure in the same owning skill.
3. **Draft.** Write sanitized text: no thread transcripts, personal paths, account or provider routing, secrets or customer details. Name the **owning skill** and its collection (the skill whose text would change, not necessarily j-launch), then state what the agent did, what should have happened, how to check it, and the vault page's path. For a match, draft a comment adding this evidence; otherwise draft a new issue titled with what should happen.
4. **Approve and file.** Show the owner the exact text and file only what they approve: the comment on the match, or a new issue labelled `retro-finding` and `needs-triage`. A rejected draft files nothing. Filing is done when every finding is filed, added to its match or rejected, and the report links each issue or comment.
