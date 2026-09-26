#!/bin/bash

# MLB Data Update Scheduler
# Requires native Homebrew PostgreSQL to be running (brew services start postgresql@14).
# Managed by launchd — see com.betbot.mlb-update.plist in project root.
#
# When PostgreSQL is not accepting connections the run is SKIPPED: the attempt is
# recorded in a marker file, a macOS notification is sent (best effort), and the
# script exits 0 because a skip is an expected outcome, not a crash. The next
# successful run logs a RESUMED line summarising the skipped attempts and clears
# the marker. RESUMED means updates resumed, not that every gap was recovered:
# the updater refetches the whole season schedule, but only the last 30 days of
# team stats, so a gap older than that prints the manual backfill command.
#
# Environment overrides (used by tests; none are needed in normal operation):
#   BETBOT_PG_ISREADY   path to pg_isready (default: brew --prefix postgresql@14)
#   BETBOT_LOG_DIR      where the log and skip marker live (default: <repo>/logs)
#   BETBOT_UPDATE_CMD   shell command to run instead of the venv update script
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

if [ -n "${BETBOT_PG_ISREADY:-}" ]; then
    PG_ISREADY="$BETBOT_PG_ISREADY"
else
    BREW_PREFIX="$(brew --prefix postgresql@14 2>/dev/null || true)"
    PG_ISREADY="${BREW_PREFIX:-/usr/local/opt/postgresql@14}/bin/pg_isready"
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
    elif command -v osascript > /dev/null 2>&1; then
        osascript -e "display notification \"$message\" with title \"BetBot MLB update\"" > /dev/null 2>&1 \
            || log "WARN: osascript notification failed (ignored)"
    fi
    return 0
}

days_between() {
    python3 -c "import sys, datetime as d; a, b = (d.date.fromisoformat(x) for x in sys.argv[1:]); print((b - a).days)" "$1" "$2"
}

report_resumed() {
    [ -s "$SKIP_MARKER" ] || return 0

    local attempts days first_day last_day today gap
    attempts="$(grep -c . "$SKIP_MARKER")"
    days="$(cut -c1-10 "$SKIP_MARKER" | sort -u | grep -c .)"
    first_day="$(head -n 1 "$SKIP_MARKER" | cut -c1-10)"
    last_day="$(tail -n 1 "$SKIP_MARKER" | cut -c1-10)"
    today="$(date '+%Y-%m-%d')"

    log "RESUMED: $attempts skipped attempt(s) across $days day(s), first skip $first_day, last skip $last_day"

    gap="$(days_between "$first_day" "$today" 2>/dev/null || echo 0)"
    if [ "$gap" -gt "$TEAM_STATS_WINDOW_DAYS" ]; then
        log "WARN: first skip was $gap days ago but team stats only refresh for the last $TEAM_STATS_WINDOW_DAYS days. Backfill with: python machine_learning/scripts/update_mlb_data.py --start-date $first_day --end-date $today"
    fi

    notify "MLB data update RESUMED after $attempts skipped attempt(s) since $first_day"
    rm -f "$SKIP_MARKER"
}

# ── PostgreSQL ─────────────────────────────────────────────────────────────────

if ! "$PG_ISREADY" -h localhost -p 5432 -U user -d betbot > /dev/null 2>&1; then
    date '+%Y-%m-%d %H:%M:%S' >> "$SKIP_MARKER"
    ATTEMPTS="$(grep -c . "$SKIP_MARKER")"
    log "SKIP: PostgreSQL is not accepting connections — run 'brew services start postgresql@14' ($ATTEMPTS skipped attempt(s) recorded in $SKIP_MARKER)"
    notify "MLB data update SKIPPED: PostgreSQL is not running ($ATTEMPTS skipped attempt(s) pending)"
    exit 0
fi

log "PostgreSQL is ready"

# ── Run update ────────────────────────────────────────────────────────────────

log "Starting MLB data update"

if [ -n "${BETBOT_UPDATE_CMD:-}" ]; then
    bash -c "$BETBOT_UPDATE_CMD" >> "$LOG_FILE" 2>&1
    EXIT_CODE=$?
else
    [ -d "$VENV_PATH" ] || handle_error "Virtual environment not found at $VENV_PATH"
    [ -f "$UPDATE_SCRIPT" ] || handle_error "Update script not found at $UPDATE_SCRIPT"

    source "$VENV_PATH/bin/activate" || handle_error "Failed to activate virtual environment"
    cd "$PROJECT_ROOT" || handle_error "Failed to change to project root"

    python "$UPDATE_SCRIPT" >> "$LOG_FILE" 2>&1
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
