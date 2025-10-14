#!/bin/bash

# MLB Data Update Scheduler
# This script can be used with cron to automatically update MLB data
# 
# Usage with cron:
#   # Update daily at 6 AM
#   0 6 * * * /path/to/betbot/machine_learning/scripts/schedule_updates.sh
#
#   # Update twice daily (6 AM and 6 PM)
#   0 6,18 * * * /path/to/betbot/machine_learning/scripts/schedule_updates.sh

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"
LOG_DIR="$PROJECT_ROOT/logs"
LOG_FILE="$LOG_DIR/mlb_data_update.log"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to handle errors
handle_error() {
    log "ERROR: $1"
    log "MLB data update failed at $(date)"
    exit 1
}

# Start logging
log "Starting scheduled MLB data update"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    handle_error "Virtual environment not found at $VENV_PATH"
fi

# Check if the update script exists
UPDATE_SCRIPT="$SCRIPT_DIR/update_mlb_data.py"
if [ ! -f "$UPDATE_SCRIPT" ]; then
    handle_error "Update script not found at $UPDATE_SCRIPT"
fi

# Activate virtual environment
log "Activating virtual environment"
source "$VENV_PATH/bin/activate" || handle_error "Failed to activate virtual environment"

# Change to project root directory
cd "$PROJECT_ROOT" || handle_error "Failed to change to project root directory"

# Run the update script
log "Running MLB data update script"
python "$UPDATE_SCRIPT" --verbose >> "$LOG_FILE" 2>&1

# Check if the update was successful
if [ $? -eq 0 ]; then
    log "MLB data update completed successfully"
else
    handle_error "MLB data update script failed with exit code $?"
fi

# Deactivate virtual environment
deactivate

log "Scheduled MLB data update finished"
