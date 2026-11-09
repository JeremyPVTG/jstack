# 0003: What the research hook sends and keeps

Date: 2026-11-09. Status: accepted.

## Context

`skills/j-research/scripts/research_hook.py` is an optional UserPromptSubmit hook. A skill description alone did not get j-research loaded reliably, so the hook classifies each prompt and adds a one-line reminder when the prompt needs current facts. An audit on 2026-11-09 found that what it sends and stores was written down only in the script's own docstring.

## Decision

Keep the hook as it is, and state its data flow here so that enabling it is an informed choice.

- **Sent to a third party.** The first 4,000 characters of each prompt it classifies go to TypeSafe's API (`api.typesafe.ai`, or `TYPESAFE_ENDPOINT`) with four yes/no questions. Prompts under 12 characters, slash commands, and results or notices the host delivers as prompts are skipped and never sent.
- **Kept locally.** The scores, the decision and the first 300 characters of each classified prompt are appended to `~/.local/state/jstack/research-hook.jsonl` (or `JSTACK_HOOK_LOG`; `off` disables it). The log exists so false fires can be labelled before anyone changes the questions.
- **Off unless enabled.** The installer does not add the hook. It runs only where someone adds it to their agent's settings and provides a TypeSafe key.
- **Fails open.** With no key, a timeout or any error, it adds nothing and the prompt goes through unchanged.

Anyone who enables it should expect prompts that contain pasted text, names or internal details to reach TypeSafe, and should leave it off in sessions where that is not acceptable.

## Rejected

- A Haiku call as the classifier: on the 71 labelled prompts in the comparison the script cites it missed one research prompt and took about four times as long.
- Redacting prompts before sending: a redactor that is good enough is its own project, and a weak one gives false comfort.

## Revisit when

False reminders become a nuisance (label the log first, then tune), TypeSafe's terms or retention change, or a host loads skills reliably from their descriptions.
