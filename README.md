# jstack

Skills and workflows I use in T3 Code, across models. Includes original skills, adaptations, and a short list of tools I recommend.

T3 Code is the primary host. Model choices stay in the session or evaluation configuration; the skills do not hardcode a provider or account. See [T3 integration and pinned upstream source paths](hosts/t3.md).

## Start here

| Skill | Use it for | Example |
|---|---|---|
| [j-research](skills/j-research/SKILL.md) | Finding how to build something, answering open questions, and comparing options from current sources. Compiles findings into a persistent research vault. | "Use j-research to find a way to build a self-hosted uptime monitor." |
| [j-scope](skills/j-scope/SKILL.md) | Drawing the MVP line by questioning you on an honest options brief, and cutting additions that add little | "Use j-scope: how far do we go for the first version?" |
| [j-evidence](skills/j-evidence/SKILL.md) | Checking completion or public claims against source evidence | "Which of these tasks can we actually mark complete?" |

Engineering pack: [j-review](skills/j-review/SKILL.md) for reviewing changes and [j-deliver](skills/j-deliver/SKILL.md) for CI repair and release readiness. Maintainer pack: [j-skill-audit](skills/j-skill-audit/SKILL.md). Personal pack: [j-bookmarks](skills/j-bookmarks/SKILL.md), a weekly triage of saved X posts into a ledger in the research vault, so every bookmark ends up researched, queued, or ignored with a link to the decision.

### The research loop

"Use j-research to find a way to build X" runs in two halves. First a landscape pass: what already exists, what practitioners use and regret, and whether you should build at all. j-scope then asks you the few decisions that set the MVP line. j-research then researches implementation inside that line only: official docs, reference code, GitHub issues, Stack Overflow, and practitioner threads and videos, in rounds until a round changes nothing.

Everything decisive is compiled into a research vault following [Karpathy's LLM wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f): immutable captured sources, agent-maintained wiki pages with review dates and volatility, an index, and a log. The next run starts from the vault and re-verifies only what has gone stale. Set the path with `J_RESEARCH_VAULT` or `research_vault` in `~/.config/jstack/config.json`; a starter vault is in [skills/j-research/assets/vault](skills/j-research/assets/vault/).

The social lane (Reddit, X, YouTube, Hacker News) depends on [last30days](https://github.com/mvanhorn/last30days-skill). See [the decision record](docs/decisions/0001-research-sources-and-vault.md) for why, and its safety notes.

**Status:** installer and structure are tested. The skills' effect on agent behaviour has not been measured yet; behavioural evals live in a separate jstack-evals repository.

## Install

Requires Python 3, Git, and an environment that supports directory symlinks. On Windows, symlink creation may require additional OS permissions. Clone this repository to a persistent location, then run from its root:

```sh
python3 scripts/install.py install --target ~/.claude/skills --dry-run
python3 scripts/install.py install --target ~/.claude/skills
```

Choose your agent's actual skills directory explicitly. The default core pack installs j-research, j-scope, and j-evidence. Use `--pack engineering` for j-review and j-deliver, `--pack maintainer` for j-skill-audit, `--pack personal` for j-bookmarks, or repeat `--skill NAME` to select individual skills. [targets.json](targets.json) lists candidate paths; it does not certify discovery support.

Existing entries are moved to timestamped backups under `~/.local/state/jstack/`. The installer prints a receipt path. Repeated installs leave matching links alone. It does not alter global rules, agent settings, plugins, or upstream installations.

```sh
python3 scripts/install.py rollback /path/to/receipt.json --dry-run
python3 scripts/install.py rollback /path/to/receipt.json
```

Rollback restores replaced entries and refuses to overwrite subsequent changes. Receipts are trusted local state, not files to accept from strangers. For agents without native discovery, [INDEX.md](INDEX.md) provides a small directory to reference from the agent's supported instructions mechanism.

## Other tools I use

| Collection | What I look to it for | Integration notes |
|---|---|---|
| [Matt Pocock's skills](https://github.com/mattpocock/skills) | Deliberate interviews, domain modeling, and handoffs | Current grill-me delegates to grilling; preserve dependencies and invocation policy. |
| [Garry Tan's gstack](https://github.com/garrytan/gstack) | Product framing, engineering planning, and QA | Use its supported host setup; isolated SKILL.md copies omit runtime dependencies. |
| [Poteto's pstack](https://github.com/cursor/plugins/tree/main/pstack) | Investigation, verification, and engineering discipline | Canonical source; the [standalone mirror](https://github.com/backnotprop/pstack) offers adaptations for other hosts. |

[upstreams.lock.json](upstreams.lock.json) records observed revisions and selected entrypoint hashes. It is a research registry, not a complete dependency lock or installer. These distributions are not bundled here. Choose one workflow owner per task instead of running several orchestration systems together.

## Development

```sh
python3 scripts/check.py
python3 -m unittest discover -s tests
```

When adding a skill, give it a specific outcome, keep conditional detail in linked references, add a realistic case to the separate jstack-evals repository, and regenerate INDEX.md with `python3 scripts/check.py --write-index`.

See [the current skill value audit](docs/skill-value-audit.md), [package decisions](docs/design.md), [migration audit](docs/audit.md), and [evaluation boundary](docs/evaluation.md). Behavioral test cases are proposals until results are recorded; a valid Markdown file does not prove a better agent workflow.
