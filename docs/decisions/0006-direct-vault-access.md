# 0006: Direct vault access when the vault server is unavailable

Date: 2026-11-26. Status: accepted.

## Context

On 2026-11-26 a build session needed the research vault to save evidence for a retro finding. The vault server's sign-in was refused, and a non-interactive session cannot sign in again. j-research fell back only to a local folder, which that host did not have configured, and j-launch's filing step said to file nothing without a connected vault. So the finding was reported and not filed, although the vault's git repository was reachable with `gh` the whole time.

The vault server is one route to that repository, not the vault itself. The vault's `AGENTS.md` already holds every rule the server enforces (layout, frontmatter, one index line per page, the log line, lint), and its `.gitattributes` merges `index.md` and `log.md` by union, so a push from a checkout does not clash with the server's appends. The server can be missing for three reasons: not configured on the host, sign-in refused, or up but failing (as in the error 1102 outage behind [0004](0004-vault-server-on-workers-paid.md)).

## Decision

When the vault server is not usable for any of those three reasons, the agent says so plainly and uses **direct access**: it reads and writes through a **vault checkout** and runs by hand what the server would do.

- **Trigger.** When a vault server is configured, one call to one of its tools by name first, since that reconnects a saved sign-in; on failure, direct access for the rest of the run, no retries.
- **Acknowledgement.** Before the first vault read or write: "The vault MCP server is not available (<reason>), so I am using the vault's git repository directly." Repeated in the report.
- **Checkout.** The configured local folder if set (pulled first when it is a git work tree), otherwise a fresh `gh repo clone` into a temporary directory, removed at the end of the run unless a push failed. The repository's name comes from `$J_RESEARCH_VAULT_REPO` or `research_vault_repo` in `~/.config/jstack/config.json`, never from tracked files.
- **Reads and writes both.** Search with `rg`; write pages and captures as files; add the index line and log line by hand; finish with `vault_lint.py` and `vault_sync.sh`. No new scripts.
- **j-launch.** A vault checkout counts as a reachable vault for filing retro evidence.

## Rejected

- Naming the vault's repository in skill text: jstack is public and the vault is private. A config key keeps the name on the owner's machine.
- Direct access for writes only: j-research searches the vault before the web, so a write-only fallback would leave that rule impossible to follow.
- A persistent clone in a cache directory: a stale copy is a second source of truth. A temporary clone is about 3 MB of Markdown and cheap to repeat.
- New helpers for the index and log lines: the edits are one line each, the vault's `AGENTS.md` defines their format, and lint catches a page missing from the index.

## Revisit when

- Direct pushes start conflicting with server writes on wiki pages (union merge covers only `index.md` and `log.md`).
- The vault grows enough that cloning per session is slow.
- The vault server gains a non-interactive credential, so refusals stop being the common trigger.
