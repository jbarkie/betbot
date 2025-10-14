#!/usr/bin/env python3
"""
MLB Data Update Script

This script updates the MLB database tables with fresh data from the 2025 season.
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
from datetime import datetime
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
from machine_learning.data.collection.mlb_direct_api import fetch_team_stats_direct
from shared.database import connect_to_db
from machine_learning.data.models.mlb_models import MLBTeam, MLBOffensiveStats, MLBDefensiveStats, MLBSchedule

# Load environment variables
load_dotenv(project_root / 'api' / '.env')


class MLBDataUpdater:
    """Handles updating MLB database tables with fresh data."""
    
    def __init__(self, verbose=False, dry_run=False, skip_stats=False):
        """
        Initialize the MLB data updater.
        
        Args:
            verbose: Enable verbose logging
            dry_run: Show what would be updated without making changes
            skip_stats: Skip team statistics update
        """
        self.verbose = verbose
        self.dry_run = dry_run
        self.skip_stats = skip_stats
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
        
        # Also configure the MLB stats API logger
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
            self.logger.info(f"Current season: {season_data.seasonid}")
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
            fetch_team_records(self.mlb, self.session, season_data.seasonid)
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
            start_date = season_data.regularseasonstartdate
            end_date = datetime.now().strftime('%Y-%m-%d')
            
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
            # Only update recent data (last 30 days) to avoid processing months of data
            from datetime import timedelta
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            self.logger.info(f"Fetching team stats from {start_date} to {end_date} (last 30 days only)")
            fetch_team_stats_direct(self.session, start_date, end_date)
            self.logger.info("Successfully updated team statistics")
        except Exception as e:
            self.logger.error(f"Failed to update team stats: {e}")
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
            else:
                self.logger.info("Skipping team statistics update as requested")
            
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
    
    args = parser.parse_args()
    
    try:
        updater = MLBDataUpdater(verbose=args.verbose, dry_run=args.dry_run, skip_stats=args.skip_stats)
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
