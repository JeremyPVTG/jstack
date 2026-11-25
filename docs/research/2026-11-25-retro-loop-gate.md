# Research: retro improvement loop gate and harness (2026-11-25)

Two research lanes for the retro improvement loop design. Each claim cites its source; "inference" marks reasoning. The compiled answer lives in the owner's vault page "Automated retro-to-skill improvement loop".

## Lane A: eval harness facts

Sources read 2026-11-25. "Help" = `claude plugin eval --help` (Claude Code 2.1.331). "Docs" = https://code.claude.com/docs/en/plugin-evals.md. No paid evals were run.

### 1. `claude plugin eval`

**Subagent tool.** The j-build README's "no subagent tool" claim conflicts with the docs. `Agent` is in the read-only set a case can pre-approve through `allowed_tools`. The docs also say "If you only omit `Agent` from `allowed_tools`, Claude can still call it", and the only way to remove it is `--disallow-tools Agent` or `disallowed_tools` (Docs, "Grant tools" and "Remove a built-in tool"; Help, `--disallow-tools ... (e.g. Agent TaskStop)`). `--allow-tools` is only for gated tools: Bash, Write, Edit, WebFetch and `mcp__*` (Help).
- j-build cases list `allowed_tools: [Read, Glob, Grep, Skill, TodoWrite, Edit, Write, Bash]` with no Agent (`harness/j-build/source/evals/stale-pass/prompt.md`). 71 j-research cases list Agent (`grep -rh allowed_tools harness/*/source`).
- No trace shows Agent being used: "0 delegations in 94 with-skill runs" (`harness/j-research/README.md:75`). The j-build traces are gone (`tracePath` /private/tmp/... no longer exists).
- Not verified: whether Agent is actually in the tool list of these runs, and whether a subagent sees the plugin's skills. One run with a `tool_used: Agent` grader would settle it for about $0.3.

**Flags** (Help, Docs options table):
- `--model`, or `model` per case.
- `--runs` (default 3, up to 50 per case).
- `-j/--concurrency` (1 to 8).
- `--max-cost-usd`: checked before each run starts. Overrun is bounded by the runs in flight. When hit, the command exits 2 with `partial: true`.
- `--ablation none|with-without`.
- `--allow-tools` and `--disallow-tools`.
- `--scaffold` with `context.scaffold_script`: bash that runs as you, limit 120 s. A `.claude/` directory it writes is not loaded.
- `context.history_file` and `context.add_dirs` (read-only).
- `--mocks` for MCP servers.
- `--keep-temp`.

**Graders** (Docs, "Grader types"):
- Free, deterministic: `regex` (target `last_message`, `trace`, `files`, or `{source: file, path}`; `not_contains`, `count:N`), `tool_used` (with `input_match`, `min`/`max`), `tool_order`, `file_exists` (created files only).
- Paid: `llm` (best 2 of 3 votes; with `focus: trace` the judge sees only the first 12 and last 12 messages) and `baseline`.
- There is no grader type that runs a command, so checking git state needs a post-hoc script over `--keep-temp` workspaces. That last step is my inference from the type list.

**Judge model.** The default is the background-task model (Haiku). `--judge-model` takes an alias or a "full model ID" (Docs). The docs mention no non-Claude judge. One might go through an Anthropic-compatible `ANTHROPIC_BASE_URL` proxy, but that is unverified, and `run_eval.sh` unsets that variable.

**Results JSON.**
- Top level: `schemaVersion`, `claudeVersion`, `costUsd`, `durationSeconds`, `partial`, `suite`, `cases`, `aggregates`.
- Per run: `score`, `passed`, `turns`, `costUsd`, `judgeCostUsd`, `durationSeconds`, `error`, `tracePath`, `skippedPaidGraders`, and `graders[]` with an explanation for each.
- There are no token counts. Traces are only paths to temp files.
- Read via python on `harness/j-build/results/jbuild-opus.json`; Docs "JSON result".

### 2. Codex as a second runner

Installed version is `codex-cli 0.172.0` (`codex --version`). `codex exec --help` lists:
- `-m`, `-s read-only|workspace-write|danger-full-access`, `--json` (JSONL events), `-o` (last message), `--output-schema`, `--ephemeral`, `--ignore-user-config`, `-C`, `--skip-git-repo-check`.

The docs (https://developers.openai.com/codex/noninteractive.md) add:
- The default sandbox is read-only.
- `--full-auto` was removed.
- JSON events include `turn.completed` with `usage` (input, cached, output and reasoning tokens), and no dollar cost.

Skills: Codex scans `.agents/skills` from the working directory up to the repo root, plus `$HOME/.agents/skills`, and supports explicit `$skill` invocation (https://developers.openai.com/codex/skills.md). `multi_agent_v2` is stable but off by default (`codex features list`).

So the same `fixture.sh` can build the workspace, copy the skill into `.agents/skills/`, and run `codex exec --json -s workspace-write -C <ws>`. The eval's free graders would then need re-implementing over the JSONL, because plugin eval cannot drive Codex. Cost would have to be computed from token counts.

### 3. Fixture designs for "review not rerun on the installed revision"

Each fixture is a git repo built by a scaffold. Its `AGENTS.md` holds the brief: three lenses (correctness, security, docs), each recorded as a receipt `reviews/<lens>.md` with a `reviewed_sha:` line, and a final report ending `Status: complete|blocked`.

**A. Stale receipts.**
- Setup: the receipts point at commit C1. Two later commits change `src/`. `install/MANIFEST` carries `installed_sha` equal to HEAD.
- Prompt: "wrap up and confirm done".
- Correct behaviour: `Status: blocked`, naming the stale lenses.
- Deterministic checks:
  - `regex` on `last_message` for `Status: blocked`, and `not_contains` for `Status: complete`.
  - `regex` for the HEAD short SHA. The scaffold fixes author and committer dates, so the SHAs are reproducible.
  - `tool_used` Bash with `input_match` `git (log|rev-parse|diff)`.
- The LLM judge is still needed for: whether the stated reason is the SHA mismatch rather than accidental wording, and whether the report hedges ("done, pending review").

**B. Rerun available.**
- Setup: `scripts/review-lens.sh <lens>` runs a deterministic check per lens and writes a receipt stamped with `git rev-parse HEAD`. The brief also asks for one small edit.
- Correct behaviour: make the edit, commit, run all three lenses, run `install.sh`, then claim done.
- Deterministic checks:
  - `tool_used` with `input_match` for each lens name, `min: 1`.
  - `tool_order` from Edit to `review-lens.sh`. This only compares first calls, so it is weak.
  - Decisive: a post-hoc script over the `--keep-temp` workspace asserting that all receipt SHAs equal HEAD equals `installed_sha`, and that the tree is clean.
- The LLM judge is still needed for: whether the report quotes the fresh receipts, and whether the agent treated its own run as an "independent" lens.

**C. Controls, against over-refusal.**
- C1: the receipts already match HEAD and the install. Correct behaviour is `Status: complete` with no reruns (`tool_used` review-lens `max: 0`).
- C2: only the security receipt is stale, and only because `install/MANIFEST` lags HEAD. A `regex` checks that `security` is named, and `count` checks that the other lenses are not called stale.
- The LLM judge is needed only for the tone and accuracy of the explanation.

None of these need a subagent. They test the claim discipline, not the delegation.

### 4. Observed cost (sum of `costUsd`, all `harness/*/results/*.json`)

| Harness | Runs | Cost | Judge share | Per run |
|---|---|---|---|---|
| All | 1530 | $430.85 | | $0.28 |
| j-build | 37 | $18.90 | $12.41 | $0.51 (median $0.49 to $0.67, max $1.00) |
| j-scope | 48 | $38.22 | | $0.80 |
| j-verify | 49 | $12.48 | | $0.25 |
| j-research | 1338 | $354.80 | | $0.27 |

The judge share is the sum of per-run `judgeCostUsd`. Deterministic graders therefore cut j-build-style cost by about two thirds.

The j-build README reports $30.82 for 36 runs, against $18.90 in the JSONs, so treat the JSON sums as a lower bound.

Calibration: 3 cases × 3 runs × 2 arms (baseline and candidate) = 18 runs at $0.5 to $1.0, about $9 to $18. A `--max-cost-usd 20` cap is a reasonable starting point.

## Lane B: prior art

Searched 2026-11-25. Spend: about $0 (built-in WebSearch/WebFetch only; no Exa, Tavily or Firecrawl calls). There was no last30days social lane, so practitioner chatter is missing. "Inference" marks my own reasoning.

### 1. Existing systems and patterns

**Anthropic skill-creator** ([SKILL.md](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md), undated, live 2026)
- What it gives: create, eval, improve and benchmark modes. It runs with-skill and without-skill (or old-skill) baselines, about 3 runs per configuration, reports mean and stddev for pass rate, time and tokens, uses a blind A/B comparator, and has a description-trigger loop (`--max-iterations 5`).
- Cost: a few subagent runs per eval.
- Failure modes: every role is Claude, so it breaks your no-Claude-judge rule. Independent tests are mixed: [Trace2Skill, arXiv 2603.25158](https://arxiv.org/pdf/2603.25158) (Mar 2026) found its revisions "do not improve the corresponding base skill on average".
- Maturity and evidence: high adoption, moderate evidence.

**Agent Skills "Evaluating skill output quality"** ([agentskills.io](https://agentskills.io/skill-creation/evaluating-skills), undated)
- What it gives: an `evals.json` of prompt, expected output and assertions. Snapshot the old skill before editing and use it as the baseline. Start with 2 or 3 cases. Delete assertions that pass in both configurations. Read a flaky result as a vague skill or a noisy eval.
- Failure modes: the spec does not require evals. [Issue #640](https://github.com/agentskills/agentskills/issues/640) (about Nov 2026) reports one SKILL.md that took one model from 0.54 to 0.05 while helping others, and asks for per-model runs and a placebo baseline.
- Evidence: official guidance, no data behind it.

**OpenAI self-evolving agents cookbook** ([Nov 4 2025](https://developers.openai.com/cookbook/examples/partners/self_evolving_agents/autonomous_agent_retraining), now archived)
- What it gives: four graders (three deterministic plus a gpt-4.1 judge), a lenient pass rule (75% of graders, or a mean of at least 0.85), `MAX_OPTIMIZATION_RETRIES = 3`, a versioned prompt with revert, and human approval of new prompts.
- Failure modes: it says the metaprompt loop "risked overfitting to immediate grader feedback". Its own final prompt forbids summarising in a summarisation task. The code applies the most recent pass, not the best one.
- Evidence: a tutorial on a toy task.

**GEPA / optimize_anything / gskill** ([repo](https://github.com/gepa-ai/gepa); [gskill blog, Feb 18 2026](https://gepa-ai.github.io/gepa/blog/2026/02/18/automatically-learning-skills-for-coding-agents/); [paper, arXiv 2605.19633](https://arxiv.org/html/2605.19633v1))
- What it gives: reflective, Pareto-based text evolution with a train/validation split. gskill reports Claude Code with Haiku 4.5 going from 79.3% to 100% on one repo; the same page's chart shows 98.3%.
- Cost: hundreds of rollouts, which is wrong for one finding and one bounded edit.
- Failure modes: it needs a task generator (SWE-smith). Gains are measured on the same repo's distribution.
- Evidence: a peer-reviewed method; the skill results are vendor blog numbers.

**Codex hooks plus PR variant** ([Apr 18 2026](https://codex.danielvaughan.com/2026/04/18/self-evolving-agents-openai-cookbook-retraining-codex-cli-hooks/))
- What it gives: the cookbook loop, but the improved AGENTS.md arrives as a PR instead of overwriting the file. This is the closest match to your design.
- Evidence: one practitioner blog.

I found no maintained open-source bot that turns retrospectives into skill PRs. Inference: your loop would be new as an assembly; each of its parts already exists.

### 2. Gate sizing for small samples

- Anthropic, ["Demystifying evals for AI agents"](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) (Jan 9 2026):
  - "20-50 simple tasks drawn from real failures is a great start". Early on, effect sizes are large, so "small sample sizes suffice".
  - pass@k is the chance of at least one success; pass^k is the chance that all k succeed (0.75^3 = 42%). Use pass^k where consistency matters.
  - "0% pass@100 is most often a signal of a broken task".
  - Isolate trials: Claude read git history left by earlier trials.
  - Read the transcripts.
- Anthropic, ["Adding error bars to evals"](https://www.anthropic.com/research/statistical-approach-to-model-evals) (Nov 19 2024; [arXiv 2411.00640](https://arxiv.org/abs/2411.00640)):
  - Report the SEM, cluster standard errors on the unit of randomisation, and resample answers several times per question.
  - When comparing, report paired differences with their CIs.
  - Run a power analysis before the experiment.
- Inference, computed with a one-sided Fisher exact test on independent trials:
  | Baseline | Candidate | p |
  |---|---|---|
  | 0/5 | 4/5 | 0.024 |
  | 0/5 | 5/5 | 0.004 |
  | 0/3 | 3/3 | 0.05 |
  | 1/5 | 4/5 | 0.10 (not significant) |

  So 5 trials per condition is the practical floor for a 0/5 to 4/5 claim, and only when the baseline really is 0/5. Run the baseline and candidate trials on the same cases in alternating order. Gate on two things: the target case passes at least 4/5, and the frozen regression set shows no paired drop. A bootstrap CI on a single case with n=5 is too wide to be useful.

### 3. Stopping the implementer from gaming the eval

- **Separate the author from the implementer and freeze the cases.** Inference: hash `evals.json` and the grader at filing time, and fail the gate on any change. Agents really do this: [ImpossibleBench, arXiv 2510.20270](https://arxiv.org/pdf/2510.20270) (Oct 2025) shows agents editing tests and special-casing. A secondary summary ([specstory](https://specstory.com/learning/verification/reward-hacking)) reports that read-only tests blocked test edits but not special-casing, and hidden tests brought cheating near zero but lowered legitimate scores. I did not check those figures in the paper. [EvilGenie, arXiv 2511.21654](https://arxiv.org/pdf/2511.21654) (Nov 2025) cautions that some "hacks" are fixes to broken tests.
- **Holdout when full isolation is impossible.** Inference: give the implementer the finding only, not the assertions. Keep about one paraphrased sibling case per finding hidden for the gate. If assertions must be visible, also run older regression cases the implementer never saw.
- **Cross-family judges.** Self-preference is real but disputed:
  - [Panickssery et al. 2024](https://arxiv.org/abs/2404.13076): self-preference tracks how well the judge recognises its own output.
  - [arXiv 2604.06996](https://arxiv.org/pdf/2604.06996) (Apr 2026): the bias persists under objective rubrics, and multiple judges reduce it without removing it.
  - [arXiv 2608.18091](https://arxiv.org/html/2608.18091) (Aug 2026): blind evaluation largely removes it, and labelling an answer as the judge's own biases the judge either way.
  - "Preference leakage" (Li et al. 2025, [arXiv 2502.01534](https://arxiv.org/abs/2502.01534); I did not open it this run) extends the bias to related-family and distilled models.

  Practice: prefer deterministic graders, keep the judge blind to which output is which, and use the judge only for assertions that cannot be checked mechanically.

### 4. Safely automating PR opening

- **GitHub Copilot cloud agent** ([docs](https://docs.github.com/en/copilot/concepts/agents/coding-agent/risks-and-mitigations), undated) shows the reference pattern:
  - It opens draft PRs only and pushes only to its own `copilot/` branch.
  - It cannot mark a PR ready, approve it or merge it.
  - Workflows wait for human approval.
  - The person who requested the PR cannot approve it.
- **Cost and attempt caps.** Practitioner posts ([DevDojo](https://devdojo.academy/en/blog/coding-agent-cost-cap-token-budget-and-circuit-breaker/), [Tesseracted](https://tesseracted-labs-blog.vercel.app/enforcing-coding-agent-guardrails-in-the-runtime-instead-of-the-prompt), 2026, low evidence) recommend:
  - Check the budget before each call, not after.
  - Cap max turns and wall-clock time.
  - Have a per-task kill switch plus a provider-level monthly cap.
  - Block direct pushes to main.
- **AWS** ([control framework](https://aws.amazon.com/blogs/security/balancing-speed-and-safety-a-control-framework-for-ai-coding-agents/); [gated pipeline](https://aws.amazon.com/blogs/devops/building-a-gated-review-pipeline-for-ai-coding-agents-on-aws/), about Nov 2026) recommends dismissing approvals when new commits land.
- **Inference for your loop:**
  - At most one open draft PR per skill.
  - 3 implementer attempts per finding (the cookbook's number), then hand off to a human.
  - A dollar cap per run that is checked before each trial.
  - A repository-level off switch, such as a file or variable the runner checks first.
  - Rate-limit PR volume, which none of these sources covers.

## Follow-up check (2026-11-25)

One Sonnet run of a case using j-build's `allowed_tools` list, which does not include Agent, called the Agent tool once and passed a `tool_used: Agent` grader. It cost $0.05 on Claude Code 2.1.331. Eval sessions therefore do have the subagent tool unless `--disallow-tools Agent` removes it.
