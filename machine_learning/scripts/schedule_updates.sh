#!/bin/bash

# MLB Data Update Scheduler
# Managed by launchd — see com.betbot.mlb-update.plist in project root.
# Starts Docker Desktop and the db container if they are not already running,
# runs the MLB data update, then tears down what it started.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/mlb_data_update.log"
COMPOSE_FILE="$PROJECT_ROOT/env/docker-compose.yml"

DOCKER_STARTED=false
CONTAINER_STARTED=false

mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

handle_error() {
    log "ERROR: $1"
    teardown
    exit 1
}

teardown() {
    if [ "$CONTAINER_STARTED" = true ]; then
        log "Stopping Docker containers"
        docker compose -f "$COMPOSE_FILE" down >> "$LOG_FILE" 2>&1
    fi

    if [ "$DOCKER_STARTED" = true ]; then
        log "Quitting Docker Desktop"
        osascript -e 'quit app "Docker"' >> "$LOG_FILE" 2>&1
    fi
}

# ── Docker Desktop ────────────────────────────────────────────────────────────

if ! docker info > /dev/null 2>&1; then
    log "Docker Desktop not running — starting it"
    open -a Docker

    DOCKER_STARTED=true
    WAIT=0
    until docker info > /dev/null 2>&1; do
        sleep 3
        WAIT=$((WAIT + 3))
        if [ $WAIT -ge 120 ]; then
            handle_error "Timed out waiting for Docker Desktop to become ready"
        fi
    done
    log "Docker Desktop ready (${WAIT}s)"
else
    log "Docker Desktop already running"
fi

# ── Database container ────────────────────────────────────────────────────────

DB_RUNNING=$(docker compose -f "$COMPOSE_FILE" ps --status running --services 2>/dev/null | grep -c "^db$")

if [ "$DB_RUNNING" -eq 0 ]; then
    log "Starting db container"
    docker compose -f "$COMPOSE_FILE" up -d db >> "$LOG_FILE" 2>&1 \
        || handle_error "Failed to start db container"

    CONTAINER_STARTED=true
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

python "$UPDATE_SCRIPT" --verbose >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

deactivate

if [ $EXIT_CODE -eq 0 ]; then
    log "MLB data update completed successfully"
else
    handle_error "Update script failed with exit code $EXIT_CODE"
fi

# ── Cleanup ───────────────────────────────────────────────────────────────────

teardown
log "Scheduled MLB data update finished"
