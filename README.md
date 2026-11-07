# jstack

Skills and workflows I use with coding agents. Includes original skills, adaptations, and a short list of tools I recommend.

## Start here

| Skill | Use it for | Example |
|---|---|---|
| [j-review](skills/j-review/SKILL.md) | Reviewing a change, confirming findings, or fixing supplied findings | “Review this branch for reachable bugs. Leave the code unchanged.” |
| [j-deliver](skills/j-deliver/SKILL.md) | CI repair, validation, publishing, and release readiness | “Check whether this PR is ready using this repo's release rules.” |
| [j-research](skills/j-research/SKILL.md) | Investigating questions and comparing options with traceable sources | “Compare these approaches using current primary sources; explain what would change your recommendation.” |
| [j-evidence](skills/j-evidence/SKILL.md) | Checking completion or public claims against source evidence | “Which of these tasks can we actually mark complete?” |
| [j-skill-audit](skills/j-skill-audit/SKILL.md) | Pruning, packaging, and evaluating skills | “Find overlap in these skills and propose the smallest useful set.” |

These skills keep review findings, release state, and completion evidence distinct. They use the target project's rules instead of hardcoding a branch, runner, provider, or approval process.

Early version: structure and installer behavior are tested. Skill behavior and discovery in fresh agent sessions are not yet benchmarked. The core adapts my earlier PR review, CI repair, publishing, and readiness skills; provenance and migration findings are in [the audit](docs/audit.md).

## Install

Requires Python 3, Git, and an environment that supports directory symlinks. On Windows, symlink creation may require additional OS permissions. Clone this repository to a persistent location, then run from its root:

```sh
python3 scripts/install.py install --target ~/.claude/skills --dry-run
python3 scripts/install.py install --target ~/.claude/skills
```

Choose your agent's actual skills directory explicitly. The default core pack installs j-review, j-deliver, j-evidence, and j-research. Use `--pack maintainer` for j-skill-audit, or repeat `--skill NAME` to select individual skills. [targets.json](targets.json) lists candidate paths; it does not certify discovery support.

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

See [package decisions](docs/design.md), [migration audit](docs/audit.md), and [evaluation boundary](docs/evaluation.md). Behavioral test cases are proposals until results are recorded; a valid Markdown file does not prove a better agent workflow.
