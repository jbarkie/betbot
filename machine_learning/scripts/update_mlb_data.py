#!/usr/bin/env python3
"""
MLB Data Update Script

Update current-season data, with optional recovery of missed historical dates.
It leverages the existing data collection functions from the machine_learning module.

Usage:
    python update_mlb_data.py [--verbose] [--dry-run]

Options:
    --verbose    Enable verbose logging output
    --dry-run    Show what would be updated without making changes
"""

import sys
import os
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import required modules
from dotenv import load_dotenv
from machine_learning.data.collection.mlb import (
    configure_logging as mlb_configure_logging,
    fetch_current_season,
    fetch_teams,
    fetch_team_records,
    fetch_schedule
)
from machine_learning.data.collection.mlb_direct_api import fetch_team_stats_direct, MLBDirectAPI
from machine_learning.data.collection.mlb_pitcher_stats import collect_pitcher_stats, MLBPitcherStatsCollector
from shared.database import connect_to_db
from machine_learning.data.models.mlb_models import MLBTeam, MLBOffensiveStats, MLBDefensiveStats, MLBSchedule

# Load environment variables
load_dotenv(project_root / 'api' / '.env')


def recovery_windows(start_date, end_date):
    """Yield inclusive recovery ranges split at season-year boundaries."""
    first = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()
    while first <= end:
        last = min(end, first.replace(month=12, day=31))
        yield first.isoformat(), last.isoformat()
        first = last + timedelta(days=1)


class MLBDataUpdater:
    """Handles updating MLB database tables with fresh data."""
    
    def __init__(
        self, verbose=False, dry_run=False, skip_stats=False, start_date=None,
        end_date=None, recover_from=None, require_complete=False,
    ):
        """
        Initialize the MLB data updater.
        
        Args:
            verbose: Enable verbose logging
            dry_run: Show what would be updated without making changes
            skip_stats: Skip team statistics update
        """
        if recover_from:
            recovery_date = datetime.strptime(recover_from, '%Y-%m-%d').date()
            if recovery_date > datetime.now().date():
                raise ValueError('Recovery start must not be in the future')
            if skip_stats or start_date or end_date:
                raise ValueError('--recover-from cannot be combined with --skip-stats or explicit dates')
            start_date = recovery_date.isoformat()
            end_date = datetime.now().date().isoformat()
        elif bool(start_date) != bool(end_date):
            raise ValueError('--start-date and --end-date must be supplied together')
        if start_date and end_date:
            if datetime.strptime(start_date, '%Y-%m-%d') > datetime.strptime(end_date, '%Y-%m-%d'):
                raise ValueError('Start date must not be after end date')
        self.require_complete = require_complete or bool(recover_from)
        self.recover_from = recover_from
        self.verbose = verbose
        self.dry_run = dry_run
        self.skip_stats = skip_stats
        self.start_date = start_date
        self.end_date = end_date
        self.session = None
        self.mlb = None
        
        # Configure logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Set up logging configuration."""
        log_level = logging.DEBUG if self.verbose else logging.INFO
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)-8s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        self.logger = logging.getLogger(__name__)

        if self.verbose:
            mlb_configure_logging()
        
    def _connect_to_database(self):
        """Connect to the database."""
        try:
            self.session = connect_to_db()
            self.logger.info("Successfully connected to database")
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}")
            raise
            
    def _initialize_mlb_api(self):
        """Initialize the MLB Stats API."""
        try:
            import mlbstatsapi
            self.mlb = mlbstatsapi.Mlb()
            self.logger.info("Successfully initialized MLB Stats API")
        except Exception as e:
            self.logger.error(f"Failed to initialize MLB Stats API: {e}")
            raise
            
    def _get_current_season_info(self):
        """Get current season information."""
        try:
            season_data = fetch_current_season(self.mlb)
            self.logger.info(f"Current season: {season_data.season_id}")
            return season_data
        except Exception as e:
            self.logger.error(f"Failed to get current season info: {e}")
            raise
            
    def _check_existing_data(self):
        """Check what data already exists in the database."""
        if not self.session:
            return
            
        # Count existing records
        team_count = self.session.query(MLBTeam).count()
        offensive_count = self.session.query(MLBOffensiveStats).count()
        defensive_count = self.session.query(MLBDefensiveStats).count()
        schedule_count = self.session.query(MLBSchedule).count()
        
        self.logger.info(f"Existing data counts:")
        self.logger.info(f"  Teams: {team_count}")
        self.logger.info(f"  Offensive stats: {offensive_count}")
        self.logger.info(f"  Defensive stats: {defensive_count}")
        self.logger.info(f"  Schedule entries: {schedule_count}")
        
    def update_teams(self, season_data):
        """Update team information."""
        self.logger.info("Updating team information...")
        
        if self.dry_run:
            self.logger.info("DRY RUN: Would fetch and store team information")
            return
            
        try:
            fetch_teams(self.mlb, self.session)
            self.logger.info("Successfully updated team information")
        except Exception as e:
            self.logger.error(f"Failed to update teams: {e}")
            raise
            
    def update_team_records(self, season_data):
        """Update team win/loss records."""
        self.logger.info("Updating team records...")
        
        if self.dry_run:
            self.logger.info("DRY RUN: Would fetch and store team records")
            return
            
        try:
            fetch_team_records(self.mlb, self.session, season_data.season_id)
            self.logger.info("Successfully updated team records")
        except Exception as e:
            self.logger.error(f"Failed to update team records: {e}")
            raise
            
    def update_schedule(self, season_data):
        """Update game schedule and results."""
        self.logger.info("Updating game schedule...")
        
        if self.dry_run:
            self.logger.info("DRY RUN: Would fetch and store game schedule")
            return
            
        try:
            start_date = season_data.regular_season_start_date
            end_date = datetime.now().strftime('%Y-%m-%d')
            if self.recover_from:
                start_date = min(str(start_date), self.recover_from)
            
            self.logger.info(f"Fetching schedule from {start_date} to {end_date}")
            fetch_schedule(self.mlb, self.session, start_date, end_date)
            self.logger.info("Successfully updated game schedule")
        except Exception as e:
            self.logger.error(f"Failed to update schedule: {e}")
            raise
            
    def update_team_stats(self, season_data):
        """Update team offensive and defensive statistics."""
        self.logger.info("Updating team statistics...")
        
        if self.dry_run:
            self.logger.info("DRY RUN: Would fetch and store team statistics")
            return
            
        try:
            if self.start_date and self.end_date:
                start_date = self.start_date
                end_date = self.end_date
                self.logger.info(f"Fetching team stats from {start_date} to {end_date}")
            else:
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                end_date = datetime.now().strftime('%Y-%m-%d')
                self.logger.info(f"Fetching team stats from {start_date} to {end_date} (last 30 days)")
            if self.recover_from:
                # Each request belongs to one season, even across an offseason.
                for first, last in recovery_windows(start_date, end_date):
                    fetch_team_stats_direct(self.session, first, last, require_complete=True)
            else:
                fetch_team_stats_direct(
                    self.session, start_date, end_date, require_complete=self.require_complete
                )
            self.logger.info("Successfully updated team statistics")
        except Exception as e:
            self.logger.error(f"Failed to update team stats: {e}")
            raise
            
    def update_pitcher_stats(self, season_data):
        """Update cumulative pre-game starting pitcher statistics."""
        self.logger.info("Updating starting pitcher statistics...")

        if self.dry_run:
            self.logger.info("DRY RUN: Would fetch and store starting pitcher statistics")
            return

        try:
            season = None
            if self.end_date:
                season = datetime.strptime(self.end_date, '%Y-%m-%d').year
            elif isinstance(season_data, dict):
                season = season_data.get('season') or season_data.get('seasonId')

            seasons = [int(season)] if season else None
            if self.recover_from:
                seasons = list(range(int(self.recover_from[:4]), int(self.end_date[:4]) + 1))
            if self.require_complete:
                # Empty valid game logs are normal (e.g. a reliever with no starts).
                # Transport failures must escape instead of masquerading as empty logs.
                collector = MLBPitcherStatsCollector(MLBDirectAPI(raise_on_error=True))
                counts = collect_pitcher_stats(self.session, seasons=seasons, collector=collector)
            else:
                counts = collect_pitcher_stats(self.session, seasons=seasons)
            self.logger.info(
                f"Successfully updated starting pitcher statistics — "
                f"inserted: {counts['inserted']}, skipped: {counts['skipped']}, "
                f"pitchers without a game log: {counts['failed_pitchers']}"
            )
        except Exception as e:
            self.logger.error(f"Failed to update pitcher stats: {e}")
            raise

    def run_update(self):
        """Run the complete data update process."""
        start_time = datetime.now()
        self.logger.info("Starting MLB data update process")
        
        if self.dry_run:
            self.logger.info("DRY RUN MODE: No changes will be made to the database")
        
        try:
            # Initialize connections
            self._connect_to_database()
            self._initialize_mlb_api()
            
            # Get season information
            season_data = self._get_current_season_info()
            
            # Check existing data
            self._check_existing_data()
            
            # Update data in sequence
            self.update_teams(season_data)
            self.update_team_records(season_data)
            self.update_schedule(season_data)
            
            if not self.skip_stats:
                self.update_team_stats(season_data)
                self.update_pitcher_stats(season_data)
            else:
                self.logger.info("Skipping team and pitcher statistics update as requested")
            
            # Calculate runtime
            end_time = datetime.now()
            runtime = end_time - start_time
            
            self.logger.info(f"MLB data update completed successfully in {runtime}")
            
        except Exception as e:
            self.logger.error(f"MLB data update failed: {e}")
            raise
        finally:
            if self.session:
                self.session.close()
                self.logger.info("Database connection closed")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Update MLB database tables with fresh data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python update_mlb_data.py                    # Normal update
    python update_mlb_data.py --verbose          # Verbose logging
    python update_mlb_data.py --dry-run          # Show what would be updated
    python update_mlb_data.py --skip-stats       # Skip team stats (faster)
    python update_mlb_data.py --verbose --dry-run # Verbose dry run
        """
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging output'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be updated without making changes'
    )
    
    parser.add_argument(
        '--skip-stats',
        action='store_true',
        help='Skip team statistics update (teams, records, and schedule only)'
    )

    parser.add_argument(
        '--start-date',
        type=str,
        default=None,
        metavar='YYYY-MM-DD',
        help='Start date for team stats fetch (default: 30 days ago). Use with --end-date for backfills.'
    )

    parser.add_argument(
        '--end-date',
        type=str,
        default=None,
        metavar='YYYY-MM-DD',
        help='End date for team stats fetch (default: today). Use with --start-date for backfills.'
    )

    parser.add_argument(
        '--recover-from', metavar='YYYY-MM-DD',
        help='Recover schedule and missing team/pitcher stats through today; fail on incomplete downloads'
    )

    parser.add_argument(
        '--require-complete', action='store_true',
        help='Fail on missing team stats or pitcher transport errors, preserving scheduler recovery state'
    )

    args = parser.parse_args()

    try:
        updater = MLBDataUpdater(
            verbose=args.verbose,
            dry_run=args.dry_run,
            skip_stats=args.skip_stats,
            start_date=args.start_date,
            end_date=args.end_date,
            recover_from=args.recover_from,
            require_complete=args.require_complete,
        )
        updater.run_update()
        
        if not args.dry_run:
            print("\n✅ MLB data update completed successfully!")
        else:
            print("\n🔍 Dry run completed - no changes were made")
            
    except KeyboardInterrupt:
        print("\n❌ Update cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Update failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
