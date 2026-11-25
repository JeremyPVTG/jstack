# Routing

Usual pairings for a launched thread. These are starting points, not exemptions from the three-collection selection gate in SKILL.md. Confirm every name in the session's skill catalog before using it; collections rename and retire skills. The project's instruction file overrides this table.

| Work | Owner | Helpers | Ships with |
|---|---|---|---|
| A decision map too big for one session: chart it, or work its next ticket | mattpocock `wayfinder` (user-only) | `grilling` and `domain-modeling` for grilling tickets, `research` for research tickets, `prototype` for prototype tickets, plus any skill the map's Notes names | mattpocock `pr` for the body, jstack `j-deliver` to merge |
| A bug fix or feature in a repository | jstack `j-build`, or the workflow the project names (pstack `poteto-mode` where the project routes large or ambiguous work to it) | mattpocock `diagnosing-bugs` or `tdd`, jstack `j-review`, the project's verify skill | jstack `j-deliver` |
| An open question: what exists, how to build it, which tool | jstack `j-research` | jstack `j-scope` for the MVP line | none |
| Reviewing a change, or triaging review comments | jstack `j-review` | none | jstack `j-deliver` |
| A PR stuck on CI, conflicts or review threads | jstack `j-deliver` | jstack `j-review` in triage mode | none |
| Writing or reworking a skill or agent instructions | mattpocock `writing-for-agents` | jstack `j-skill-audit` | jstack `j-deliver` |
| Checking whether work is complete or a claim holds | jstack `j-evidence` | jstack `j-research` for open points | none |
