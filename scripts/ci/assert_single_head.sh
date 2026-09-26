#!/usr/bin/env bash
# Fail unless the Alembic migration history has exactly one head.
#
# Usage:
#   scripts/ci/assert_single_head.sh            # runs `alembic heads`
#   scripts/ci/assert_single_head.sh FILE       # reads captured output from FILE (tests)
#
# `alembic heads` only prints information; it exits 0 even with a forked
# history. This script turns that output into a pass/fail signal.
set -euo pipefail

if [ "${1:-}" != "" ]; then
    output="$(cat "$1")"
else
    # Capture both streams so a failing alembic explains itself instead of
    # dying silently under set -e with an opaque exit code.
    if ! output="$(alembic heads 2>&1)"; then
        echo "FAIL: 'alembic heads' exited non-zero" >&2
        printf '%s\n' "$output" >&2
        exit 1
    fi
fi

count="$(printf '%s\n' "$output" | grep -c '(head)' || true)"

if [ "$count" -eq 1 ]; then
    echo "OK: exactly one migration head"
    printf '%s\n' "$output"
    exit 0
fi

echo "FAIL: expected exactly one migration head, found $count" >&2
printf '%s\n' "$output" >&2
exit 1
