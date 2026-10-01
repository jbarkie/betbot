#!/bin/bash
# Launch the bundled helper through LaunchServices, then inspect its result.
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP="$PROJECT_ROOT/.local/BetBot Notifier.app"
[ -d "$APP" ] || { echo "Run setup_notifications.sh first" >&2; exit 1; }
RESULT="$(mktemp "${TMPDIR:-/tmp}/betbot-notification.XXXXXX")"
trap 'rm -f "$RESULT"' EXIT
if [ "${1:-}" = --authorize ] || [ "${1:-}" = --status ]; then
    ARGS=("$1")
else
    ARGS=(--message "${1:?notification message required}")
fi
/usr/bin/open -g -n -W "$APP" --args "${ARGS[@]}" --result "$RESULT"
cat "$RESULT"
[[ "$(cat "$RESULT")" == '0: '* ]]
