# Sources and tools

Only facts an agent would not already know. Each carries the date it was last checked; recheck prices and limits older than 90 days.

| Need | Tool | Notes (checked 2026-11-07) |
|---|---|---|
| Social and community sweep | [last30days](https://github.com/mvanhorn/last30days-skill) | Invoke it as a skill, not by calling its engine directly; when hosted by an agent it expects the agent to write the query plan. Reddit, Hacker News and GitHub need no keys; YouTube needs `yt-dlp`. Default window is 30 days (`--days` widens it). Expect off-topic clusters on niche technical topics: in one dogfood run, 2 of 8 were relevant. |
| X posts | last30days with browser cookies (`setup --allow-browser-cookies`) | Free. Reads your logged-in x.com session at search time, which carries account risk under X's terms; the owner of this stack has accepted that. On macOS the agent host app needs browser-data access (System Settings > Privacy & Security), and Chrome's cookies also need Keychain access. A first setup can report "permission denied" even when access is granted; re-run it, and expect X results to be noisy in `--quick` mode. Paid alternative without the account risk: `XAI_API_KEY` for xAI `x_search`, $5 per 1,000 posts fetched plus tokens (from 2026-09-21). |
| Primary docs and pages ("the official page that explains X") | Exa `web_search_exa` (describe the ideal page, not keywords), then `web_fetch_exa` | Semantic. In a 2026-11-07 test it was the only one to return the official docs page. |
| Recent, dated breadth | Tavily `tavily_search` with `time_range` or `start_date`; `tavily_extract` for full text | Fast, filters by date, good snippets. |
| Code, GitHub issues and PRs | Firecrawl `firecrawl_search` with `categories: ["developer"]`; `firecrawl_scrape` for script-heavy pages | Its developer index returned GitHub issues and repos the other two missed. |
| Fallback | The host's own web search and fetch | Use when none of the three is connected, and say so in the coverage line. |
| Paid multi-step research | Exa `agent_run`, Firecrawl agent, Tavily research | Billed per run. Check their citations like any other summary. |
| Video transcripts | `yt-dlp --write-auto-subs --skip-download` | Auto-captions mangle names and numbers; confirm anything decisive elsewhere. |
| Vault search | `rg`, or the Obsidian CLI (`obsidian search query=...`) | The official CLI needs Obsidian 1.12.7+ with the app running. Add a search index such as qmd only when `index.md` no longer fits in context. |

In the docs and code lanes, query two of the three providers and merge results by URL: in the 2026-11-07 test the same question returned no overlapping results across them. Searches cost a credit or two each. Name the providers used in the report's coverage line.

## last30days safety

The skills.sh security scan (2026-11-07) rates last30days as high risk, mainly because it runs a local engine with network access and can read browser cookies. It runs with full agent permissions. Grant cookie access only if you accept the account risk, and review changes before updating past the pinned revision (`71dc2a1`, 2026-11-07).
