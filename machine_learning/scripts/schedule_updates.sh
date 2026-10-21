#!/bin/bash

# MLB Data Update Scheduler
# Requires native Homebrew PostgreSQL to be running (brew services start postgresql@14).
# Managed by launchd — see com.betbot.mlb-update.plist in project root.
#
# When PostgreSQL is not accepting connections the run is SKIPPED: the attempt is
# recorded in a marker file, a macOS notification is sent (best effort), and the
# script exits 0 because a skip is an expected outcome, not a crash. The next
# successful run logs a RESUMED line summarising the skipped attempts and clears
# the marker. Gaps beyond the 30-day refresh window trigger strict recovery
# through today; incomplete downloads keep the marker for the next attempt.
# RESUMED is not a general audit of historical database completeness.
#
# Environment overrides (used by tests; none are needed in normal operation):
#   BETBOT_PG_ISREADY   path to pg_isready (default: discovered, see below)
#   BETBOT_BREW_CANDIDATES  colon-separated brew binaries to try (tests only)
#   BETBOT_HOMEBREW_ROOTS   colon-separated Homebrew roots to try (tests only)
#   BETBOT_LOG_DIR      where the log and skip marker live (default: <repo>/logs)
#   BETBOT_UPDATE_CMD   shell command instead of the updater; receives its CLI arguments
#   BETBOT_NOTIFY_CMD   command given the message as $1 instead of osascript
#   BETBOT_VENV_PATH    virtualenv location (default: <repo>/venv)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_PATH="${BETBOT_VENV_PATH:-$PROJECT_ROOT/venv}"
LOG_DIR="${BETBOT_LOG_DIR:-$PROJECT_ROOT/logs}"
LOG_FILE="$LOG_DIR/mlb_data_update.log"
SKIP_MARKER="$LOG_DIR/mlb_update_skips.log"
UPDATE_SCRIPT="$SCRIPT_DIR/update_mlb_data.py"
TEAM_STATS_WINDOW_DAYS=30

# pg_isready discovery. launchd runs this with a minimal PATH that usually
# contains neither Homebrew location, so `brew` by name cannot be trusted:
# Apple Silicon installs live under /opt/homebrew, Intel (and Rosetta) installs
# under /usr/local. Try absolute brew binaries for both first, then any brew on
# PATH, then the two standard roots directly, then the historical path.
LEGACY_PG_ISREADY="/usr/local/opt/postgresql@14/bin/pg_isready"
BREW_CANDIDATES="${BETBOT_BREW_CANDIDATES:-/opt/homebrew/bin/brew:/usr/local/bin/brew}"
HOMEBREW_ROOTS="${BETBOT_HOMEBREW_ROOTS:-/opt/homebrew:/usr/local}"

discover_pg_isready() {
    local brew prefix root candidate
    local IFS=':'

    for brew in $BREW_CANDIDATES $(command -v brew 2>/dev/null); do
        [ -x "$brew" ] || continue
        prefix="$("$brew" --prefix postgresql@14 2>/dev/null)" || continue
        candidate="$prefix/bin/pg_isready"
        if [ -n "$prefix" ] && [ -x "$candidate" ]; then
            echo "$candidate"
            return 0
        fi
    done

    for root in $HOMEBREW_ROOTS; do
        candidate="$root/opt/postgresql@14/bin/pg_isready"
        if [ -x "$candidate" ]; then
            echo "$candidate"
            return 0
        fi
    done

    echo "$LEGACY_PG_ISREADY"
}

if [ -n "${BETBOT_PG_ISREADY:-}" ]; then
    PG_ISREADY="$BETBOT_PG_ISREADY"
else
    PG_ISREADY="$(discover_pg_isready)"
fi

mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

handle_error() {
    log "ERROR: $1"
    exit 1
}

# Best effort: a missing or failing notifier never changes the marker or the
# exit code. The marker file is the durable record; the notification is a nudge.
notify() {
    local message="$1"
    if [ -n "${BETBOT_NOTIFY_CMD:-}" ]; then
        "$BETBOT_NOTIFY_CMD" "$message" > /dev/null 2>&1 \
            || log "WARN: notifier '$BETBOT_NOTIFY_CMD' failed (ignored)"
    elif [ -d "$PROJECT_ROOT/.local/BetBot Notifier.app" ]; then
        local result
        if ! result="$(bash "$SCRIPT_DIR/notify_macos.sh" "$message" 2>&1)"; then
            log "WARN: BetBot notifier failed (ignored): $result"
        fi
    elif command -v osascript > /dev/null 2>&1; then
        local diagnostic
        if ! diagnostic="$(osascript - "$message" 2>&1 <<'APPLESCRIPT'
on run argv
    display notification (item 1 of argv) with title "BetBot MLB update" sound name "Glass"
end run
APPLESCRIPT
        )"; then
            log "WARN: osascript notification failed (ignored): $diagnostic"
        fi
    else
        log "WARN: osascript unavailable; skip marker and logs remain the source of truth"
    fi
    return 0
}

# Diagnostic only: no readiness check, marker writes, or data refresh.
if [ "${1:-}" = "--check-notification" ]; then
    notify "Notification check: if you can see this, BetBot alerts are visible."
    log "Notification check attempted; confirm the banner or Notification Center entry yourself. Command success does not prove visibility."
    exit 0
fi

recovery_start() {
    local python_bin="$VENV_PATH/bin/python"
    [ -x "$python_bin" ] || python_bin="python3"
    "$python_bin" - "$SKIP_MARKER" "$TEAM_STATS_WINDOW_DAYS" <<'PYTHON'
import datetime as d
import pathlib
import sys

lines = pathlib.Path(sys.argv[1]).read_text().splitlines()
dates = [d.datetime.strptime(line, '%Y-%m-%d %H:%M:%S').date() for line in lines if line.strip()]
if not dates:
    raise ValueError('Skip marker contains no timestamps')
today = d.date.today()
if any(day > today for day in dates):
    raise ValueError('Skip marker contains a future timestamp')
# The missed morning update would also have collected the previous day's games.
first = min(dates) - d.timedelta(days=1)
if (today - first).days > int(sys.argv[2]):
    print(first.isoformat())
PYTHON
}

report_resumed() {
    [ -s "$SKIP_MARKER" ] || return 0

    local attempts days first_day last_day
    attempts="$(grep -c . "$SKIP_MARKER")"
    days="$(cut -c1-10 "$SKIP_MARKER" | sort -u | grep -c .)"
    first_day="$(head -n 1 "$SKIP_MARKER" | cut -c1-10)"
    last_day="$(tail -n 1 "$SKIP_MARKER" | cut -c1-10)"

    log "RESUMED: $attempts skipped attempt(s) across $days day(s), first skip $first_day, last skip $last_day"

    notify "MLB data update RESUMED after $attempts skipped attempt(s) since $first_day"
    rm -f "$SKIP_MARKER"
}

# ── PostgreSQL ─────────────────────────────────────────────────────────────────

log "Using pg_isready at $PG_ISREADY"
if [ ! -x "$PG_ISREADY" ]; then
    log "WARN: $PG_ISREADY is not executable; PostgreSQL will be reported as unavailable"
fi

if ! "$PG_ISREADY" -h localhost -p 5432 -U user -d betbot > /dev/null 2>&1; then
    date '+%Y-%m-%d %H:%M:%S' >> "$SKIP_MARKER"
    ATTEMPTS="$(grep -c . "$SKIP_MARKER")"
    log "SKIP: PostgreSQL is not accepting connections — run 'brew services start postgresql@14' ($ATTEMPTS skipped attempt(s) recorded in $SKIP_MARKER)"
    notify "MLB data update SKIPPED: PostgreSQL is not running ($ATTEMPTS skipped attempt(s) pending)"
    exit 0
fi

log "PostgreSQL is ready"

# ── Run update ────────────────────────────────────────────────────────────────

UPDATE_ARGS=()
if [ -s "$SKIP_MARKER" ]; then
    UPDATE_ARGS=(--require-complete)
    RECOVERY_START="$(recovery_start)" || handle_error "Cannot parse skip marker; preserving it for inspection"
    if [ -n "$RECOVERY_START" ]; then
        UPDATE_ARGS=(--recover-from "$RECOVERY_START")
        log "RECOVERY: refreshing missed data from $RECOVERY_START through today; incomplete downloads retain the marker"
    fi
fi

log "Starting MLB data update"

if [ -n "${BETBOT_UPDATE_CMD:-}" ]; then
    bash -c "$BETBOT_UPDATE_CMD \"\$@\"" -- "${UPDATE_ARGS[@]}" >> "$LOG_FILE" 2>&1
    EXIT_CODE=$?
else
    [ -d "$VENV_PATH" ] || handle_error "Virtual environment not found at $VENV_PATH"
    [ -f "$UPDATE_SCRIPT" ] || handle_error "Update script not found at $UPDATE_SCRIPT"

    source "$VENV_PATH/bin/activate" || handle_error "Failed to activate virtual environment"
    cd "$PROJECT_ROOT" || handle_error "Failed to change to project root"

    python "$UPDATE_SCRIPT" "${UPDATE_ARGS[@]}" >> "$LOG_FILE" 2>&1
    EXIT_CODE=$?

    deactivate
fi

if [ $EXIT_CODE -eq 0 ]; then
    log "MLB data update completed successfully"
    report_resumed
else
    # The marker is deliberately left in place: nothing has been recovered yet.
    handle_error "Update script failed with exit code $EXIT_CODE"
fi

log "Scheduled MLB data update finished"
