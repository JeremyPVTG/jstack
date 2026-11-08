---
name: j-scope
description: Decide how far to go before building. Draw the MVP line by questioning the user on an honest options brief, and push back on additions that add little. Use after j-research's landscape step, or when asked "how much do we build", "is this overkill", or "what's the MVP".
---

# Scope

The default answer to "should we add this?" is no, until it earns its place. The job is a short, explicit line between what gets built now and what waits.

## Input

An honest brief: options with what each gives, costs, and risks, ideally from j-research's landscape step. If there is none, write a short one from what you know and say it is unresearched. If a research vault is in use, search it for earlier decision pages on the topic and say so if this scope would contradict one.

## Question the user

Ask one decision at a time with the host's structured question tool (`AskUserQuestion` in Claude Code); otherwise ask in chat with numbered options. Each question:

- is a decision only the user can make (goals, budget, risk, taste); settle facts yourself from the brief or code;
- offers 2 to 4 options, recommended first, each saying what it costs and what you give up;
- takes a position: say what evidence would change your recommendation;
- comes from the brief's evidence, not from hypotheticals.

Good questions: what is done today without this, and what does that workaround cost (if little, propose not building); what result would prove this works; adopt the existing tool or build; which capability can wait; the budget in money and time; what failure is acceptable in the first version.

For every proposed capability, ask yourself first: what does this give us that we don't already have, and what breaks if we leave it out? If nothing breaks, propose cutting it rather than asking. Push back when the user adds scope too; say plainly when something looks like over-engineering. The exception: an addition that is cheap and changes the outcome a lot gets one question rather than a silent cut.

Stop when the line is drawn, usually within 3 to 6 questions. Do not interview for completeness.

## Output

A scope decision:

- **Goal and proof:** the smallest outcome that shows it works, checked by something other than your or the user's say-so (a test, a user, a number).
- **In:** what gets built now, and whether each part is adopted or built.
- **Out:** what waits, each with the signal that would bring it back.
- **Risks accepted.**
- **Against the recommendation:** each choice the user made against your recommendation, so later results can be judged against it.

Use [the decision template](assets/decision-template.md). If a research vault is in use, record it as a `decision` page there. Then hand it back to j-research for implementation research or to the build.

Grilling approach adapted from Matt Pocock's [grilling skill](https://github.com/mattpocock/skills); status quo and position-taking from gstack's [office-hours](https://github.com/garrytan/gstack/tree/main/office-hours).
