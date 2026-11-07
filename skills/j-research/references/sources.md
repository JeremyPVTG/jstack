# Sources and tools

Use whatever the host actually provides; these are the tools j-research knows how to use well. Facts here carry the date they were last checked. Recheck anything older than 90 days before relying on a price or limit.

| Need | Tool | Notes (checked 2026-11-07) |
|---|---|---|
| Social and community sweep | [last30days](https://github.com/mvanhorn/last30days-skill) | Reddit, X, YouTube transcripts, Hacker News, GitHub, Polymarket and more, scored by engagement. MIT. Requires Python 3.12+. Reddit, HN and GitHub work without keys; YouTube needs `yt-dlp` on PATH. Window is the last 30 days by default, so treat it as "what people do now", not the full history. |
| X posts | last30days with `XAI_API_KEY` | Uses xAI's `x_search`: $5 per 1,000 posts fetched plus tokens (xAI pricing from 2026-09-21). Decline the browser-cookie route; it reads your logged-in X session. |
| General web search | Exa, Tavily, Firecrawl, or host web search | Describe the page you want rather than keywords. Use `site:` filters (`site:stackoverflow.com`, `site:github.com`) for targeted lanes. |
| Read a page | Exa fetch, Firecrawl scrape, `defuddle` | Fetch the primary page rather than trusting a search snippet. |
| Multi-step research | Exa `agent_run`, Firecrawl agent, Tavily research | Paid per run. Useful for list-building and enrichment; check its citations like any other summary. |
| Stack Overflow | Web search with `site:stackoverflow.com`, or the Stack Exchange API | Compare answer date and version with the version you are using. |
| GitHub | `gh search repos`, `gh api`, `gh search issues` | Check last push, release cadence, open issues, and licence before recommending adoption. |
| Video | `yt-dlp --write-auto-subs --skip-download` | Transcripts only; cite the timestamp. |
| Papers | Firecrawl research tools, PubMed, arXiv | For scientific claims, read the paper, not the abstract alone. |
| Vault search | `rg` in the vault, or the Obsidian CLI (`obsidian search query=...`, Obsidian 1.12.7+, app must be running) | Start with `index.md`. Add a search index such as qmd only when `index.md` no longer fits in context. |

## last30days safety

The skills.sh security scan (2026-11-07) rates last30days highly risky, mainly because it runs a local engine with network access and can read browser cookies. It runs with full agent permissions. Keep its first-run choices to keyless sources plus API keys, refuse cookie access, and pin the version you reviewed (`71dc2a1` on 2026-11-07).
