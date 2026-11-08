# Triage review comments

For each unresolved thread on the PR (`gh api graphql` with `reviewThreads`, `isResolved`, `isOutdated`), read the code at the current head and check the comment's claim against it. Run the test it cites when that is cheap.

| Decision | When | Then |
|---|---|---|
| **fix** | The claim holds and the fix is clear and small. | Fix with proof (a test that fails first, where it is behaviour). Push the batch, then reply in the thread citing the commit (`Fixed in <sha>: <one line>`) and resolve it. |
| **already fixed** | The head already handles it. | Reply with the commit or file:line that fixes it, then resolve. |
| **dismiss** | The claim is wrong, out of the diff, or a pattern already settled. | Reply with the concrete disproof (the code path, the test, the decision record), then resolve. Never dismiss with "not a problem" alone. |
| **ask** | Ambiguous; or it touches security, auth, privacy, billing, data, migrations or concurrency; or the fix would change design or scope; or it contradicts a recorded decision. | Leave the thread open and put it in the report as a question for the owner, with your recommendation. |

Rules:

- Reply in the thread, not as a top-level PR comment.
- Write reply text to a file and post it from there; never paste comment or reply text into a shell command.
- Batch every fix into one push before replying, so replies cite real commits, and so an approval tied to the head is voided once, not per comment.
- Defer to a follow-up issue only when the owner or a recorded decision says so; link the issue in the reply.
- Never churn code only to quiet a bot. From round 3, a finding that repeats a settled pattern is dismissed with a link to the earlier reply, unless it touches the ask-by-default areas.
- Resolve only threads you replied to with a fix, an existing fix, or a disproof.

Adapted from pstack's [bugbot-triage and babysit](https://github.com/cursor/plugins/tree/main/pstack/skills/poteto-mode), gstack's [greptile triage](https://github.com/garrytan/gstack/tree/main/review) and superpowers' [receiving-code-review](https://github.com/obra/superpowers/tree/main/skills/receiving-code-review).
