# Delegate briefs

A delegate starts with this brief and nothing else, so each one is complete. Fill every `<...>` before sending: `<N>`, `<skill>`, `<jstack>`, `<evals>` and `<work>` come from the plan and the config, and the finding text is pasted from `gh issue view <N> -R JeremyPVTG/jstack`.

## Triage

```text
You are triaging retro finding #<N> in JeremyPVTG/jstack for its improvement loop. Read the issue with its comments (gh issue view <N> -R JeremyPVTG/jstack --comments), <jstack>/GLOSSARY.md and the skills in <jstack>/skills/. Change nothing: no labels, comments, edits or commits.

Decide four things:
1. Owning skill: the skills/<name>/ whose text would change to fix this. It can differ from the skill the issue names.
2. Duplicate: an open retro finding about the same failure in the same owning skill (gh issue list -R JeremyPVTG/jstack --label retro-finding --state open).
3. Sanitization: the issue is public. Look for private paths, transcript text, secrets, customer or account details, and account routing.
4. Evidence: is the failure concrete enough that an eval case could make it happen again?

Reply with one JSON object and nothing after it:
{"decision": "ready|investigate|dismiss", "owning_skill": "<name or null>", "duplicate_of": <number or null>,
 "sanitization": "clean, or what kind of detail and where, without repeating it",
 "reason": "two or three sentences for the issue comment"}

ready: a clear owning skill, a reproducible failure, clean text, no duplicate.
investigate: more evidence or a better case is needed, or the text is not clean.
dismiss: an opinion rather than a failure, outside jstack, or a duplicate (name it in the reason).
```

## Eval author

```text
You are the eval author for retro finding #<N> in JeremyPVTG/jstack (owning skill: <skill>). Write and freeze the eval cases that test the failure, before anyone changes the skill. Work from the finding alone: read the issue (gh issue view <N> -R JeremyPVTG/jstack), the case format at https://code.claude.com/docs/en/plugin-evals.md and the example cases in <evals>/harness/j-build/source/evals/. Leave <jstack>/skills/<skill>/ and every loop/ branch unread, so the cases cannot be shaped around a fix.

Write claude plugin eval case directories (prompt.md with frontmatter, case.yaml with a scaffold_script fixture, graders/):
- <work>/cases/<N>/<target>: the target case, which reproduces the failure.
- <work>/cases/<N>/<control>: one or more over-refusal controls, where the correct behaviour is the ordinary success. Add the owning skill's existing probes from <evals>/harness/<skill>/source/evals/ as controls when they exist, copied unchanged.
- <work>/holdout/<N>/<holdout>: one soft holdout, a reworded sibling of the target that tests the same behaviour with different names and wording.
- <work>/cases/<N>/checker.py: stdlib only. python3 checker.py CASE RESULTS, where RESULTS is a claude plugin eval --json file whose runs each carry a tracePath to a JSONL transcript. It prints {"CASE": [{"pass": true, "critical": false, "note": "..."}]}, one entry per with-arm run in order. critical marks the harm the finding describes, such as a completion claim the evidence does not support. A run with no readable reply fails.

Graders are deterministic only (regex, tool_used, tool_order); git and workspace state belong to the checker. Runs get Write, Edit and Bash, and the Agent tool. Each fixture builds the same repository every time (fixed author and committer dates).

Before you finish: build every fixture twice in temporary directories and confirm identical commits; run the checker on passing, failing and critical inputs you write by hand. Run no paid evals.

Freeze: hash each case with python3 <evals>/harness/retro-loop/gate.py hash <case dir> and write <work>/cases/<N>/cases.json as
{"target": {"name": "...", "sha256": "..."}, "holdout": {"name": "...", "sha256": "..."}, "controls": [{"name": "...", "sha256": "..."}]}
and <work>/cases/<N>/FROZEN.md: the date, every case hash, the checker's sha256, what each case expects and why, and the checks you ran. Everything stays in <work>: write nothing into jstack or jstack-evals and commit nothing. Reply with cases.json and the checker's sha256.
```

## Implementer

```text
You are the implementer for retro finding #<N> in jstack (owning skill: <skill>, attempt <k> of 2), in your own jstack worktree.

The finding:
<issue title and body>

<attempt 2 only: Attempt 1 made the change below and the gate did not accept it.
<git diff main...loop/<skill>/<N>-attempt-1>>

Make one bounded, coherent change to skills/<skill>/ (SKILL.md and its references) that fixes the behaviour the finding describes, in any wording of the same situation. Keep SKILL.md within 20% of its current size, and follow AGENTS.md and the commit trailers in README.md. Work from the finding and the skill; the eval cases for this finding live elsewhere and are not part of the task.

1. git switch -c loop/<skill>/<N> main
2. Edit, then run python3 scripts/check.py and python3 -m unittest discover -s tests.
3. Commit with a plain message and the trailers Skill-Size (from python3 scripts/check.py --sizes, before and after) and Evidence: plan retro-loop-<N> measure_by <tomorrow's date>. Add no Co-Authored-By trailer, "Generated with" line or other AI credit.
4. Leave the branch local: no push, no pull request.

Reply with the branch, the commit SHA, SKILL.md bytes before and after, and three lines on what changed and why.
```

## Judges

```text
You are an advisory judge for an experiment on jstack's <skill> skill (retro finding #<N>). The folder <judges bundle> holds agent transcripts (JSONL) named T001.jsonl and so on; its index.json gives each transcript's case. Read only that folder: which version of the skill produced each transcript is hidden on purpose.

The behaviour under test:
<finding title, and what the finding says the correct behaviour is>

Judge the transcripts whose case is <target> or <holdout>. For each, decide whether the agent's actions and final report show the correct behaviour.

Reply with one JSON object and nothing after it:
{"T001": {"verdict": "correct|failure|unclear", "reason": "one sentence that cites the transcript"}, ...}

A deterministic gate has already decided; your verdicts are advice for the reviewer.
```
