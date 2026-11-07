#!/bin/bash
# Commit local vault changes, rebase onto the remote, and push.
# Safe to run on a schedule. Refuses to commit when iCloud has evicted files
# (they would look deleted) or when an unusual number of files disappear.
# Usage: vault_sync.sh VAULT [MAX_DELETIONS]
set -u
vault="${1:?usage: vault_sync.sh VAULT [MAX_DELETIONS]}"
max_deletions="${2:-5}"
log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }

cd "$vault" || { log "cannot enter $vault"; exit 1; }
git rev-parse --git-dir >/dev/null 2>&1 || { log "not a git work tree"; exit 1; }

if [ -n "$(git status --porcelain --untracked-files=no | grep '^.U\|^U' || true)" ] || [ -d "$(git rev-parse --git-dir)/rebase-merge" ] || [ -d "$(git rev-parse --git-dir)/rebase-apply" ]; then
  log "unresolved conflict or rebase in progress; resolve it by hand"; exit 1
fi

evicted=$(find . -path ./.git -prune -o -name '.*.icloud' -print | head -5)
if [ -n "$evicted" ]; then
  log "iCloud placeholders present, not syncing: $(echo "$evicted" | tr '\n' ' ')"; exit 0
fi

deleted=$(git ls-files --deleted | wc -l | tr -d ' ')
if [ "$deleted" -gt "$max_deletions" ]; then
  log "$deleted tracked files missing (limit $max_deletions), not syncing"; exit 1
fi

git add -A
if ! git diff --cached --quiet; then
  git commit -q -m "Sync from $(hostname -s) $(date -u +%Y-%m-%dT%H:%MZ)" || { log "commit failed"; exit 1; }
fi

if ! git pull -q --rebase origin main; then
  git rebase --abort 2>/dev/null
  log "pull conflicted; local commits kept, resolve by hand"; exit 1
fi
git push -q origin HEAD:main || { log "push failed"; exit 1; }
log "synced $(git rev-parse --short HEAD)"
