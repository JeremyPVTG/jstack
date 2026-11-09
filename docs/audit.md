# Initial audit — 2026-11-07

Snapshot of 2026-11-07. The owned set has since grown from four skills to the ones in [INDEX.md](../INDEX.md), and j-review and j-deliver were rebuilt; see [the skill value audit](skill-value-audit.md).

Scope: inventory of top-level personal Codex skills and targeted content inspection of PR, build, research, design-council, machine-limit, and T3 skills. This is not an audit of every system, plugin, AWS, or project skill. Inventory hashes preserve the inspected local snapshot without copying private history into this package.

## Consolidation decisions

| Existing skills | Proposed disposition | Reason |
|---|---|---|
| pr-review-verdict, pr-review-and-fix | j-review modes | Shared revision/evidence contract; preserve read-only versus fix authority |
| pr-ci-failure-fix, pr-test-and-publish, pr-merge-readiness | j-deliver modes | Shared release evidence; repository defines actual gates |
| pr-stale-review-threads | Keep specialized pending caller audit | External thread mutation is a distinct outcome; not silently replaced by a local verdict |
| staged-build-workflow | Split project policy from reusable workflow; retire duplicate coordinator after migration | Mixes HerdSense branches, product constraints, old PR facts, provider restrictions, tool assumptions, and general process |
| t3-coordinator-pipeline | Rewrite as a host adapter, outside core | Reuses review threads where current host requires fresh delegates; launches top-level threads for child work; fixes model/account routing and stage counts |
| t3-browser-tab-limit | Host troubleshooting reference | Automatic headless fallback conflicts with current shared-browser fallback rules; too broad a trigger |
| t3-usage-check | Deterministic script plus thin skill, future work | Repeated extraction should not require agent reasoning; preserve stale/unavailable distinction |
| t3-reroute-blocked-threads | Keep optional adapter; update authorization and live capability checks | Historical account choices must not authorize switching providers today |
| heavy-work-guard | Keep optional machine policy; narrow trigger | Local machine constraints matter; static 4GB heuristic is not a general capability standard |
| deep-research-vault | Project adapter | Already correctly delegates to the repository; not a generic research engine |
| clean-room-design-council | Keep optional, rework budget and methodology | Mandatory three families twice each is costly; fixed score stability does not establish statistical validity |
| blind-judge-diff | Keep optional, evaluate independently | Blinded comparison differs from ordinary review; avoid merging away the experimental protocol |
| customer-research, first-customer-finder, product-marketing | Keep as a founder pack; inspect before promotion | Different outcomes, despite shared customer context |
| Cloudflare, AWS, document, and design collections | Link selected upstream capabilities | Do not fork maintained vendor guidance without a demonstrated gap |

These dispositions are recommendations. Installed copies have not been removed or edited. The four owned skills are staged replacements, not aliases already wired into callers.

## Concrete corrections in staged skills

- Regression tests depend on meaningful behavior, rather than requiring a new test for every old or already-fixed finding.
- Existing authorization remains valid within scope; arbitrary repeat approval is removed.
- Readiness follows the actual repository rules, rather than universally requiring no unresolved comments, an updated base branch, or a special risk approval.
- Historical hostnames, branches, workflow names, incidents, model preferences, and account identifiers are absent from reusable entrypoints.
- Reviews, fixes, publishing, and merging have explicit authority boundaries without imposing additional approval rounds.
- No subagents, top-level threads, or multi-model panels launch automatically from the core.

## Design evaluation rework

Keep comparable captures, neutral labels where achievable, a fixed task-relevant rubric, independent observations, and image-capability checks. Blinding is partial when branding identifies a page; disclose that limitation. Score variance is evidence, not a reason to discard inconvenient ratings. Retain observations and investigate disagreements. Start with a budget suited to the decision; repeat or add independent judges when uncertainty justifies the cost. Stop when the acceptance criterion is met, evidence saturates, or the authorized budget ends. Avoid optimizing indefinitely to judge scores.

## Upstream inspection findings

- Matt's grill-me entrypoint delegates to grilling. Install their dependency pair using an appropriate host mapping. Its handoff skill writes to an OS temporary directory and links existing artifacts.
- gstack's office-hours entrypoint refers to shared preambles and executable helpers; a standalone Markdown link does not make it operational. Its README provides host-specific setup; Codex support is described as experimental at the recorded revision.
- Canonical pstack is cursor/plugins/pstack. backnotprop/pstack is a standalone mirror with intentional adaptations. The canonical automate-me depends on Cursor tools and workspace-scoped transcript discovery; its history-mining method must not be assumed portable. show-me-your-work uses supporting templates and a log helper.
- Full runtime dependency closure and installation side effects have not been certified. Candidate links do not mean those capabilities are ready in this session.

## Release standard

Promote a candidate only after it routes correctly, improves task outcomes on representative artifacts, preserves user intent and authorization, handles missing tools, and has an acceptable context/cost footprint. Record the model, host, revision, task, result, and limitations. The word frontier is an ambition, not an evaluation result.
