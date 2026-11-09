# Package decisions

## Primary host and model independence

Optimize for T3 Code across selected models. Keep provider-specific mechanics in the host integration reference and use current runtime instructions. Model agnostic describes the skill design; behavioral transfer must still be measured per provider/model in T3. Standalone agent CLIs are optional targets, not substitutes for T3 integration trials.

## Focused skills, selected packs

Skills are the discovery unit; packs are the installation unit. A pack does not inject all its instructions into a task. Keep independent capabilities discoverable by their own descriptions. Use modes only when they share an outcome and evidence contract, as review/confirm/fix do.

The package started with four task-facing skills and one maintainer skill; [INDEX.md](../INDEX.md) lists the current set. Research investigates questions and alternatives; evidence reconciliation determines what existing sources prove about a claim or status. Preserve existing installations during migration. Do not force a ten-group target or import all historical procedures unchanged.

## Owned core and independent upstreams

Maintain original adaptations here; record their origins. Keep upstream distributions separate at recorded revisions. Retain upstream namespaces and native setup when required. Links are recommendations, not a promise that one Markdown file supplies a working toolchain.

An external pack becomes installable through jstack only after its dependency closure, supported host integration, license, setup effects, and collisions are understood. Do not stack competing orchestrators on one task.

## Explicit installation and rollback

Install selected owned skills into one explicit directory per command. Before replacing an entry, move it to a timestamped backup and record a receipt. Repeat installs are no-ops. Rollback refuses destinations changed since installation. It removes only installer-created links and restores backups. Keep the checkout at its installed path or reinstall from its new location.

Do not overwrite global rules or agent settings. An agent without native skill discovery can be directed to INDEX.md through its own supported instructions mechanism. Candidate folders do not count as certified support. T3 is a host using providers, not a universal extra skills directory.

## Public package and local configuration

Public documentation explains useful behavior and requirements. Personal inventory and machine-specific configuration stay in ignored .local/. Do not export private transcripts. Keep account routing, secret provider details, project branch policy, and local resource limits in their owning environment.

## Evidence before migration

Structural validation establishes package integrity. Installer tests establish tested filesystem behavior. Behavioral cases establish skill usefulness only when actually run against realistic artifacts. Fresh-session discovery tests establish support per host and version.

Before replacing old installed skills: map existing callers, compare baseline and candidate behavior, test the selected host, then switch installation links. Preserve the old version until rollback is no longer needed.

## Next candidates

Evaluate decision records, session handoffs, resource-aware validation, and secure secret delivery next. Prefer existing upstream capabilities where they fit. A clipboard watcher is not the default when the host provides a secret-input mechanism. Defer generic ratchet installation, account routing, bulk branch cleanup, and fleet orchestration until their assumptions and audience are clear.
