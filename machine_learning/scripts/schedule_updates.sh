#!/bin/bash

# MLB Data Update Scheduler
# Requires Docker Desktop to already be running. If Docker is not running,
# logs a clear message and exits immediately — no hangs, no retries.
# Managed by launchd — see com.betbot.mlb-update.plist in project root.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/mlb_data_update.log"
COMPOSE_FILE="$PROJECT_ROOT/env/docker-compose.yml"

mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

handle_error() {
    log "ERROR: $1"
    exit 1
}

# ── Docker Desktop ────────────────────────────────────────────────────────────

if ! docker info > /dev/null 2>&1; then
    log "SKIP: Docker is not running — start Docker Desktop and the update will run on next wake"
    exit 0
fi

log "Docker is running"

# ── Database container ────────────────────────────────────────────────────────

DB_RUNNING=$(docker compose -f "$COMPOSE_FILE" ps --status running --services 2>/dev/null | grep -c "^db$")

if [ "$DB_RUNNING" -eq 0 ]; then
    log "Starting db container"
    docker compose -f "$COMPOSE_FILE" up -d db >> "$LOG_FILE" 2>&1 \
        || handle_error "Failed to start db container"

    WAIT=0
    until docker compose -f "$COMPOSE_FILE" exec -T db pg_isready -U user > /dev/null 2>&1; do
        sleep 2
        WAIT=$((WAIT + 2))
        if [ $WAIT -ge 60 ]; then
            handle_error "Timed out waiting for Postgres to accept connections"
        fi
    done
    log "Postgres ready (${WAIT}s)"
else
    log "db container already running"
fi

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
