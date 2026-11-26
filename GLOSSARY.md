# jstack

A collection of agent skills, plus the tooling that installs them and the loop that improves them from evidence of real use.

## Improvement loop

**Retrospective**:
The bounded review a launched thread performs at its end, comparing the skills it was told to use with what it actually loaded, used and reworked.
_Avoid_: Retro report, postmortem

**Retro finding**:
A sanitized public issue recording one concrete failure, repeated friction, missed check or workflow conflict seen in a retrospective, naming the skill that owns the fix.
_Avoid_: Candidate, improvement, ticket

**Owning skill**:
The skill whose text would change to fix a retro finding; not necessarily the skill that launched the work.

**Filed**:
The first state of a retro finding: recorded and awaiting triage.
_Avoid_: Candidate (as a state), New

**Eval author**:
The agent that writes and freezes the eval cases for a retro finding before any skill text changes. Never the implementer.

**Implementer**:
The agent that makes one bounded change to an owning skill in response to a retro finding.

**Target case**:
The frozen eval case that reproduces a retro finding's failure.

**Soft holdout**:
A reworded sibling of the target case, kept out of the implementer's workspace until the gate runs but not isolated from its credentials.
_Avoid_: Holdout, hidden test, sealed set

**Incumbent**:
The owning skill's text as it stands on the base branch, used as the baseline condition.
_Avoid_: Baseline skill, old skill

**Candidate**:
A skill revision under test against the incumbent. Never a queue item.

**Gate**:
The predeclared comparison of candidate against incumbent that decides whether a draft pull request opens.

**Outcome**:
The recorded result of one gate: accepted, rejected or inconclusive.

## Research vault

**Vault server**:
The MCP server that reads and writes the research vault on an agent's behalf and enforces its rules.

**Vault checkout**:
A git working copy of the research vault's repository: the owner's configured local folder or a temporary clone.
_Avoid_: Local vault (when it means a clone)

**Direct access**:
Reading and writing the research vault through a vault checkout, doing by hand what the vault server would do, when the vault server is unavailable.
_Avoid_: Fallback mode, offline mode
