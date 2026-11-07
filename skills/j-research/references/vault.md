# Vault access

Use the first that is available.

1. **Vault MCP server** (tools named `guide`, `search`, `read`, `write_page`, `capture_source`, `append_log`, `lint`; see [vault-server](../../../vault-server/)). Call `guide` once for the rules and index. Use `search` and `read` to find pages, `capture_source` for raw sources, `write_page` (with the `sha` from `read`) for wiki pages and the index, then `append_log` and `lint`. Works from any device.
2. **Local folder**: `$J_RESEARCH_VAULT`, else `research_vault` in `~/.config/jstack/config.json`. Read its `AGENTS.md` before writing, and finish with `python3 scripts/vault_lint.py <vault>` from the skill's directory.
3. **Neither**: research without a vault and offer once to create one from [the template](../assets/vault/).
