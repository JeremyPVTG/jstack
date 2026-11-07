#!/bin/sh
# Weekly X bookmark sweep for launchd. Reads bookmarks with bird (browser
# cookies, so it runs on the Mac that is logged in to x.com), classifies new
# ones with a model that has no tools, records them in the vault ledger, and
# shows a notification. Never changes anything on X.
set -eu
PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
export PATH
summary=$(python3 "$(dirname "$0")/x_bookmarks.py" sweep 2>&1) || status=$?
echo "$(date '+%Y-%m-%d %H:%M') ${summary}"
osascript -e "display notification \"$(printf '%s' "$summary" | tr -d '"\\' | tail -c 200)\" with title \"X bookmarks\"" >/dev/null 2>&1 || true
exit "${status:-0}"
