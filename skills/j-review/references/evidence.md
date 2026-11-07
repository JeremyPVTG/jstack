# Evidence for review

A useful finding connects a reachable trigger to an observable consequence. Cite code paths and caller assumptions; use a focused reproduction when inference is uncertain. A failing check must belong to the reviewed revision. Label environment failures separately.

Review evidence expires when the relevant code changes. A new unrelated commit need not invalidate every observation, but project rules may require approval of the complete current head.

Do not run a full suite just to strengthen wording. State missing runtime coverage plainly. A reviewer may recommend a fix without applying it. Never resolve external review threads merely because a local verdict says fixed.
