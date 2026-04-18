# MLB Data Update Scripts

This directory contains scripts for updating MLB database tables with fresh data from the 2025 season.

## Overview

The MLB analytics system requires up-to-date data in the following database tables:

- `mlb_teams` - Team information and current records
- `mlb_offensive_stats` - Team batting statistics
- `mlb_defensive_stats` - Team pitching statistics
- `mlb_schedule` - Game schedule and results

## Quick Start

### Manual Update

To update the data manually, run:

```bash
# From the project root directory
cd /path/to/betbot
source venv/bin/activate
python machine_learning/scripts/update_mlb_data.py
```

### Dry Run

To see what would be updated without making changes:

```bash
python machine_learning/scripts/update_mlb_data.py --dry-run
```

### Verbose Output

For detailed logging during the update:

```bash
python machine_learning/scripts/update_mlb_data.py --verbose
```

### Skip Team Statistics

To update only teams, records, and schedule (faster execution):

```bash
python machine_learning/scripts/update_mlb_data.py --skip-stats
```

## Direct API Implementation

The script now uses a **direct HTTP implementation** for team statistics, bypassing the `mlbstatsapi` library to avoid compatibility issues. This ensures reliable data collection without API parsing errors.

**Benefits:**

- ✅ No more API compatibility errors
- ✅ Faster and more reliable data collection
- ✅ Direct control over API requests and responses
- ✅ Better error handling and logging

## Scripts

### `update_mlb_data.py`

The main update script that fetches and stores MLB data.

**Features:**

- Updates all four MLB database tables
- Fetches 2025 season data only
- Includes error handling and progress logging
- Supports dry-run mode for testing
- Uses existing, tested data collection functions

**Command Line Options:**

- `--verbose` - Enable detailed logging output
- `--dry-run` - Show what would be updated without making changes

**Example Usage:**

```bash
# Normal update
python machine_learning/scripts/update_mlb_data.py

# Verbose dry run
python machine_learning/scripts/update_mlb_data.py --verbose --dry-run
```

### `schedule_updates.sh`

A bash script for automated scheduling via launchd (macOS).

**Features:**

- Starts Docker Desktop if not running, and stops it when done
- Starts only the `db` container (not adminer) and waits for Postgres to be ready
- Activates the virtual environment automatically
- Logs all output with timestamps
- Handles errors gracefully with full teardown on failure
- Can be run manually at any time

## Automated Scheduling

### Setting Up launchd (macOS)

The project uses **launchd** instead of cron. Unlike cron, launchd catches up missed runs after the machine wakes from sleep.

Install once after cloning:

```bash
cp com.betbot.mlb-update.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.betbot.mlb-update.plist
```

Verify the job is registered:

```bash
launchctl list | grep betbot
```

Run manually at any time (e.g., to catch up or test):

```bash
bash machine_learning/scripts/schedule_updates.sh
```

To unload (disable) the scheduler:

```bash
launchctl unload ~/Library/LaunchAgents/com.betbot.mlb-update.plist
```

### Log Files

Scheduled updates are logged to:

```
/path/to/betbot/logs/mlb_data_update.log
```

Check the logs to monitor update status:

```bash
tail -f /path/to/betbot/logs/mlb_data_update.log
```

## Expected Runtime

- **Teams and Records:** ~30 seconds
- **Schedule:** ~1-2 minutes
- **Team Statistics:** ~5-10 minutes (depends on number of games)
- **Total:** ~10-15 minutes for a full update

## Troubleshooting

### Common Issues

**1. Database Connection Error**

```
Failed to connect to database: ...
```

- Check that your `.env` file is properly configured
- Verify the database is running
- Ensure database credentials are correct

**2. MLB API Error**

```
Failed to initialize MLB Stats API: ...
```

- Check your internet connection
- Verify the `python-mlb-statsapi` package is installed
- The MLB API may be temporarily unavailable

**3. Permission Errors**

```
Permission denied: ...
```

- Make sure the script is executable: `chmod +x machine_learning/scripts/schedule_updates.sh`
- Check file permissions on the project directory

**4. Virtual Environment Issues**

```
Failed to activate virtual environment
```

- Verify the virtual environment exists at `venv/`
- Check that the path in the script is correct

### Debug Mode

For troubleshooting, run with verbose output:

```bash
python machine_learning/scripts/update_mlb_data.py --verbose
```

### Checking Data

After running the update, verify the data was updated:

```python
from shared.database import connect_to_db
from machine_learning.data.models.mlb_models import MLBTeam, MLBOffensiveStats, MLBDefensiveStats, MLBSchedule

session = connect_to_db()

# Check counts
print(f"Teams: {session.query(MLBTeam).count()}")
print(f"Offensive stats: {session.query(MLBOffensiveStats).count()}")
print(f"Defensive stats: {session.query(MLBDefensiveStats).count()}")
print(f"Schedule entries: {session.query(MLBSchedule).count()}")

session.close()
```

## Dependencies

The scripts require the following packages (already in `requirements.txt`):

- `python-mlb-statsapi` - MLB Stats API client
- `colorlog` - Colored logging output
- `sqlalchemy` - Database ORM
- `python-dotenv` - Environment variable loading
