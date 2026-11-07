# Sources and tools

Only facts an agent would not already know. Each carries the date it was last checked; recheck prices and limits older than 90 days.

| Need | Tool | Notes (checked 2026-11-07) |
|---|---|---|
| Social and community sweep | [last30days](https://github.com/mvanhorn/last30days-skill) | Invoke it as a skill, not by calling its engine directly; when hosted by an agent it expects the agent to write the query plan. Reddit, Hacker News and GitHub need no keys; YouTube needs `yt-dlp`. Default window is 30 days (`--days` widens it). Expect off-topic clusters on niche technical topics: in one dogfood run, 2 of 8 were relevant. |
| X posts | last30days with browser cookies (`setup --allow-browser-cookies`) | Free. Reads your logged-in x.com session at search time, which carries account risk under X's terms; the owner of this stack has accepted that. On macOS the agent host app needs browser-data access (System Settings > Privacy & Security). Paid alternative without the account risk: `XAI_API_KEY` for xAI `x_search`, $5 per 1,000 posts fetched plus tokens (from 2026-09-21). |
| Paid multi-step research | Exa `agent_run`, Firecrawl agent, Tavily research | Billed per run. Check their citations like any other summary. |
| Video transcripts | `yt-dlp --write-auto-subs --skip-download` | Auto-captions mangle names and numbers; confirm anything decisive elsewhere. |
| Vault search | `rg`, or the Obsidian CLI (`obsidian search query=...`) | The official CLI needs Obsidian 1.12.7+ with the app running. Add a search index such as qmd only when `index.md` no longer fits in context. |

## last30days safety

The skills.sh security scan (2026-11-07) rates last30days as high risk, mainly because it runs a local engine with network access and can read browser cookies. It runs with full agent permissions. Grant cookie access only if you accept the account risk, and review changes before updating past the pinned revision (`71dc2a1`, 2026-11-07).
