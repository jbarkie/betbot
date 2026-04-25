#!/bin/bash

# MLB Data Update Scheduler
# Requires native Homebrew PostgreSQL to be running (brew services start postgresql@14).
# If PostgreSQL is not accepting connections, logs a clear message and exits immediately.
# Managed by launchd — see com.betbot.mlb-update.plist in project root.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/mlb_data_update.log"
PG_ISREADY="/usr/local/opt/postgresql@14/bin/pg_isready"

mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

handle_error() {
    log "ERROR: $1"
    exit 1
}

# ── PostgreSQL ─────────────────────────────────────────────────────────────────

if ! "$PG_ISREADY" -h localhost -p 5432 -U user -d betbot > /dev/null 2>&1; then
    log "SKIP: PostgreSQL is not accepting connections — run 'brew services start postgresql@14'"
    exit 0
fi

log "PostgreSQL is ready"

# ── Prerequisites ─────────────────────────────────────────────────────────────

[ -d "$VENV_PATH" ] || handle_error "Virtual environment not found at $VENV_PATH"

UPDATE_SCRIPT="$SCRIPT_DIR/update_mlb_data.py"
[ -f "$UPDATE_SCRIPT" ] || handle_error "Update script not found at $UPDATE_SCRIPT"

# ── Run update ────────────────────────────────────────────────────────────────

log "Starting MLB data update"

source "$VENV_PATH/bin/activate" || handle_error "Failed to activate virtual environment"
cd "$PROJECT_ROOT" || handle_error "Failed to change to project root"

python "$UPDATE_SCRIPT" >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

deactivate

if [ $EXIT_CODE -eq 0 ]; then
    log "MLB data update completed successfully"
else
    handle_error "Update script failed with exit code $EXIT_CODE"
fi

log "Scheduled MLB data update finished"
