# T3 Code upstream changes

Dated transitions of the pinned reference in [the source lock](t3-source.lock.json). Each entry is source evidence only; it does not show runtime compatibility with an installed build.

## 2026-11-07: 25bf84a to 09a54f0

- Old: `25bf84ab07f53f141c20239c63e383823a9d5ea0`. New: `09a54f01bc0ae83865347a965ced50f8c8ec2953` (main, 18 commits ahead).
- Changed watched path: `packages/provider-core/src/server/orchestrationInstructions.ts` (sha256 `556cddc9...` to `726fb93e...`). The visuals guidance now tells agents to pass `html_preview` either a path to an HTML file or inline HTML, instead of passing a file's HTML contents (upstream d6c2b09c5, "html tools take a file path"). Discovery, capabilities, delegation and tool lifecycle text are unchanged; the L1-L34 anchor still covers the instruction sections.
- Unchanged and still valid at the new commit: the two orchestration-v2 docs, ClaudeSkills.ts, the Cursor skills scanner, providerSkills.ts, and the mcp-tool-use README and orchestration cases.
- Test implications: none of jstack's skills call `html_preview`, so no jstack host case is affected. Upstream added `evals/mcp-tool-use/cases/visual-preview.ndjson` (not watched). Installed build match is not verified; compatibility tests were not run.
