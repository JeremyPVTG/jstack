# What a repository's build file holds

j-build reads one file in the repository before it changes anything, usually `docs/agents/build.md`, linked from AGENTS.md. It holds what is true for that repository, so the skill can stay generic. Keep it short and factual: a rule that cannot bend belongs in a hook or a CI check, not in prose.

## Sections

- **Base and branches:** the branch to start from and open PRs against; branch naming; whether a delivery plan or tracker assigns branch names.
- **Delivery plan:** where planned work lives (for example `configs/delivery/*.json`), which fields are binding (`scope`, `depends_on`, `acceptance`, `gate`).
- **Checks:** the exact commands the push hook and CI run, how to scope them to changed files, and any budgets they enforce (file sizes, bundle sizes, error ratchets). Setup a fresh worktree needs (installs, hooks).
- **Where heavy work runs:** memory limits on the laptop, remote runners, which suites never run locally.
- **Approvals and gates:** what needs a person and who (risk tiers, governed files, release managers), what agents may approve or comment, and what proves an approval (a review, a comment on an exact head).
- **Stops beyond the universal ones:** spend limits, hosts, data the repo must never keep, claims it must never make.
- **Research sources:** the trackers, chat and meeting tools to search during diagnosis, and which search providers to use.
- **Review rules:** what the rules lens checks (the repo's principles, copy rules, policy), and anything a reviewer must never flag.
- **Shell and tooling notes:** known traps in this repo's environment.
