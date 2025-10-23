"""
Direct MLB API Implementation

This module provides direct HTTP requests to the MLB Stats API, bypassing
the mlbstatsapi library to avoid compatibility issues.
"""

import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from ..models.mlb_models import MLBOffensiveStats, MLBDefensiveStats


class MLBDirectAPI:
    """Direct HTTP client for MLB Stats API."""
    
    BASE_URL = "https://statsapi.mlb.com/api/v1"
    
    def __init__(self, timeout: int = 30):
        """
        Initialize the direct API client.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MLB Data Collector/1.0'
        })
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict]:
        """
        Make a direct HTTP request to the MLB API.
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            
        Returns:
            JSON response data or None if request failed
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed for {url}: {e}")
            return None
    
    def get_team_hitting_stats(
        self, 
        team_id: int, 
        start_date: str, 
        end_date: str
    ) -> Optional[Dict]:
        """
        Get team hitting statistics directly from the API.
        
        Args:
            team_id: MLB team ID
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Hitting stats data or None if request failed
        """
        params = {
            'start_date': start_date,
            'end_date': end_date,
            'stats': 'season',
            'group': 'hitting'
        }
        
        return self._make_request(f"teams/{team_id}/stats", params)
    
    def get_team_pitching_stats(
        self, 
        team_id: int, 
        start_date: str, 
        end_date: str
    ) -> Optional[Dict]:
        """
        Get team pitching statistics directly from the API.
        
        Args:
            team_id: MLB team ID
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Pitching stats data or None if request failed
        """
        params = {
            'start_date': start_date,
            'end_date': end_date,
            'stats': 'season',
            'group': 'pitching'
        }
        
        return self._make_request(f"teams/{team_id}/stats", params)
    
    def extract_hitting_stats(self, api_data: Dict) -> Optional[Dict]:
        """
        Extract hitting statistics from API response.
        
        Args:
            api_data: Raw API response data
            
        Returns:
            Extracted hitting stats or None if not found
        """
        try:
            if 'stats' in api_data and api_data['stats']:
                for stat_group in api_data['stats']:
                    if (stat_group.get('group', {}).get('displayName') == 'hitting' and
                        stat_group.get('type', {}).get('displayName') == 'season' and
                        'splits' in stat_group and stat_group['splits']):
                        
                        return stat_group['splits'][0]['stat']
            return None
        except (KeyError, IndexError, TypeError) as e:
            logging.error(f"Failed to extract hitting stats: {e}")
            return None
    
    def extract_pitching_stats(self, api_data: Dict) -> Optional[Dict]:
        """
        Extract pitching statistics from API response.
        
        Args:
            api_data: Raw API response data
            
        Returns:
            Extracted pitching stats or None if not found
        """
        try:
            if 'stats' in api_data and api_data['stats']:
                for stat_group in api_data['stats']:
                    if (stat_group.get('group', {}).get('displayName') == 'pitching' and
                        stat_group.get('type', {}).get('displayName') == 'season' and
                        'splits' in stat_group and stat_group['splits']):
                        
                        return stat_group['splits'][0]['stat']
            return None
        except (KeyError, IndexError, TypeError) as e:
            logging.error(f"Failed to extract pitching stats: {e}")
            return None


def fetch_team_stats_direct(
    session: Session,
    start_date: str,
    end_date: str,
    api_client: MLBDirectAPI = None
) -> None:
    """
    Fetch team statistics using direct API calls.

    Args:
        session: Database session
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        api_client: Optional API client instance
    """
    from ..models.mlb_models import MLBTeam, MLBSchedule

    if api_client is None:
        api_client = MLBDirectAPI()

    teams = session.query(MLBTeam).all()

    # Only process dates where games were actually played
    game_dates = session.query(MLBSchedule.date)\
        .filter(MLBSchedule.date.between(start_date, end_date))\
        .filter(MLBSchedule.status == 'Final')\
        .distinct()\
        .order_by(MLBSchedule.date)\
        .all()

    game_dates = [date[0] for date in game_dates]

    if not game_dates:
        logging.info(f'No completed games found between {start_date} and {end_date}')
        return

    # Query existing statistics upfront to avoid redundant API calls
    existing_offensive = set(
        session.query(MLBOffensiveStats.team_id, MLBOffensiveStats.date)
        .filter(MLBOffensiveStats.date.between(start_date, end_date))
        .all()
    )

    existing_defensive = set(
        session.query(MLBDefensiveStats.team_id, MLBDefensiveStats.date)
        .filter(MLBDefensiveStats.date.between(start_date, end_date))
        .all()
    )

    logging.info(f'Processing team stats for {len(game_dates)} game dates using direct API')
    logging.info(f'Found {len(existing_offensive)} existing offensive stat records')
    logging.info(f'Found {len(existing_defensive)} existing defensive stat records')

    stats_fetched = {'offensive': 0, 'defensive': 0}
    stats_skipped = {'offensive': 0, 'defensive': 0}

    for current_date in game_dates:
        logging.info(f'Processing team stats for {current_date}')

        for team in teams:
            # Check if offensive stats already exist before making API call
            if (team.id, current_date) in existing_offensive:
                logging.debug(f'Skipping offensive stats for team {team.id} on {current_date} - already exists')
                stats_skipped['offensive'] += 1
            else:
                # Fetch hitting stats
                hitting_data = api_client.get_team_hitting_stats(
                    team.id, start_date, current_date.strftime('%Y-%m-%d')
                )

                if hitting_data:
                    hitting_stats = api_client.extract_hitting_stats(hitting_data)
                    if hitting_stats:
                        try:
                            db_offensive_stats = MLBOffensiveStats(
                                team_id=team.id,
                                date=current_date,
                                team_batting_average=float(hitting_stats.get('avg', 0.0)),
                                runs_scored=int(hitting_stats.get('runs', 0)),
                                home_runs=int(hitting_stats.get('homeRuns', 0)),
                                on_base_percentage=float(hitting_stats.get('obp', 0.0)),
                                slugging_percentage=float(hitting_stats.get('slg', 0.0))
                            )
                            session.add(db_offensive_stats)
                            stats_fetched['offensive'] += 1
                            logging.debug(f'Added offensive stats for team {team.id} on {current_date}')
                        except (ValueError, TypeError) as e:
                            logging.warning(f'Failed to process offensive stats for team {team.id} on {current_date}: {e}')
                    else:
                        logging.warning(f'No hitting stats found for team {team.id} on {current_date}')
                else:
                    logging.warning(f'Failed to fetch hitting data for team {team.id} on {current_date}')

            # Check if defensive stats already exist before making API call
            if (team.id, current_date) in existing_defensive:
                logging.debug(f'Skipping defensive stats for team {team.id} on {current_date} - already exists')
                stats_skipped['defensive'] += 1
            else:
                # Fetch pitching stats
                pitching_data = api_client.get_team_pitching_stats(
                    team.id, start_date, current_date.strftime('%Y-%m-%d')
                )

                if pitching_data:
                    pitching_stats = api_client.extract_pitching_stats(pitching_data)
                    if pitching_stats:
                        try:
                            db_defensive_stats = MLBDefensiveStats(
                                team_id=team.id,
                                date=current_date,
                                team_era=float(pitching_stats.get('era', 0.0)),
                                runs_allowed=int(pitching_stats.get('runs', 0)),
                                whip=float(pitching_stats.get('whip', 0.0)),
                                strikeouts=int(pitching_stats.get('strikeOuts', 0)),
                                avg_against=float(pitching_stats.get('avg', 0.0))
                            )
                            session.add(db_defensive_stats)
                            stats_fetched['defensive'] += 1
                            logging.debug(f'Added defensive stats for team {team.id} on {current_date}')
                        except (ValueError, TypeError) as e:
                            logging.warning(f'Failed to process defensive stats for team {team.id} on {current_date}: {e}')
                    else:
                        logging.warning(f'No pitching stats found for team {team.id} on {current_date}')
                else:
                    logging.warning(f'Failed to fetch pitching data for team {team.id} on {current_date}')
        
        # Commit after each date to avoid large transactions
        session.commit()
        logging.info(f'Committed stats for {current_date}')

    # Log summary of stats processing
    logging.info(f'Stats fetching summary:')
    logging.info(f'  Offensive stats - Fetched: {stats_fetched["offensive"]}, Skipped: {stats_skipped["offensive"]}')
    logging.info(f'  Defensive stats - Fetched: {stats_fetched["defensive"]}, Skipped: {stats_skipped["defensive"]}')


def test_direct_api():
    """Test the direct API implementation."""
    api_client = MLBDirectAPI()
    
    # Test hitting stats
    hitting_data = api_client.get_team_hitting_stats(141, '2025-09-13', '2025-09-13')
    if hitting_data:
        hitting_stats = api_client.extract_hitting_stats(hitting_data)
        if hitting_stats:
            print("Hitting stats sample:")
            print(f"  Batting Average: {hitting_stats.get('avg')}")
            print(f"  Runs: {hitting_stats.get('runs')}")
            print(f"  Home Runs: {hitting_stats.get('homeRuns')}")
            print(f"  OBP: {hitting_stats.get('obp')}")
            print(f"  SLG: {hitting_stats.get('slg')}")
        else:
            print("No hitting stats found")
    else:
        print("Failed to fetch hitting data")
    
    # Test pitching stats
    pitching_data = api_client.get_team_pitching_stats(141, '2025-09-13', '2025-09-13')
    if pitching_data:
        pitching_stats = api_client.extract_pitching_stats(pitching_data)
        if pitching_stats:
            print("\nPitching stats sample:")
            print(f"  ERA: {pitching_stats.get('era')}")
            print(f"  Runs Allowed: {pitching_stats.get('runs')}")
            print(f"  WHIP: {pitching_stats.get('whip')}")
            print(f"  Strikeouts: {pitching_stats.get('strikeOuts')}")
            print(f"  Avg Against: {pitching_stats.get('avg')}")
        else:
            print("No pitching stats found")
    else:
        print("Failed to fetch pitching data")


if __name__ == '__main__':
    test_direct_api()
