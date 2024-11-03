"""
Feature enginering utilities for MLB game predictions.
"""
from datetime import datetime
from typing import Dict, Tuple
import pandas as pd

class GameFeatureGenerator:
    """
    Generates features for a given MLB game using current season data.
    """
    def __init__(
        self,
        rolling_window: int = 10,
        head_to_head_window: int = 5
    ):
        """
        Initialize the feature generator.
        
        Args:
            rolling_window: Number of games to include in rolling calculations
            head_to_head_window: Number of recent matchups to consider for head-to-head features
        """
        self.rolling_window = rolling_window
        self.head_to_head_window = head_to_head_window

    def generate_game_features(
        self,
        home_team_id: int,
        away_team_id: int,
        game_date: datetime,
        rolling_stats: pd.DataFrame,
        offensive_stats: pd.DataFrame,
        defensive_stats: pd.DataFrame,
        schedule_df: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Generate features for a single game.
        
        Args:
            home_team_id: ID of the home team
            away_team_id: ID of the away team
            game_date: Date of the game
            rolling_stats: DataFrame containing rolling statistics calculated for all teams
            offensive_stats: DataFrame containing offensive statistics for all teams
            defensive_stats: DataFrame containing defensive statistics for all teams
            schedule_df: DataFrame containing game schedule and results
            
        Returns:
            Dictionary containing engineered features for the game
        """
    
        latest_home_stats = self._get_recent_stats(
            home_team_id, game_date, rolling_stats
        )
        latest_away_stats = self._get_recent_stats(
            away_team_id, game_date, rolling_stats
        )

        h2h_features = self._get_head_to_head_features(
            home_team_id,
            away_team_id,
            game_date,
            schedule_df
        )

        features = {
            'home_rolling_win_pct': latest_home_stats.get('rolling_win_pct', 0.0),
            'away_rolling_win_pct': latest_away_stats.get('rolling_win_pct', 0.0),
            'home_rolling_runs_scored': latest_home_stats.get('rolling_runs_scored', 0.0),
            'away_rolling_runs_scored': latest_away_stats.get('rolling_runs_scored', 0.0),
            'home_rolling_runs_allowed': latest_home_stats.get('rolling_runs_allowed', 0.0),
            'away_rolling_runs_allowed': latest_away_stats.get('rolling_runs_allowed', 0.0),
            'home_days_rest': latest_home_stats.get('days_rest', 0.0),
            'away_days_rest': latest_away_stats.get('days_rest', 0.0),
            'h2h_home_win_pct': h2h_features.get('home_win_pct', 0.0),
            'h2h_away_win_pct': h2h_features.get('away_win_pct', 0.0),
            'h2h_games_played': h2h_features.get('games_played', 0)
        }

        return features
    
    def _get_recent_stats(
        self,
        team_id: int,
        game_date: datetime,
        rolling_stats: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Get the most recent rolling statistics for a team prior to a given date.
        
        Args:
            team_id: ID of the team 
            game_date: Date to get statstics before
            rolling_stats: DataFrame containing rolling statistics for all teams
            
        Returns:
            Dictionary containing recent statistics for given team
        """
        team_stats = rolling_stats[
            (rolling_stats['team_id'] == team_id) &
            (rolling_stats['date'] < game_date)
        ].sort_values('date').last()
        
        return team_stats.to_dict() if not team_stats.empty else {}
    
    def _get_head_to_head_features(
        self,
        home_team_id: int,
        away_team_id: int,
        game_date: datetime,
        schedule_df: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Calculate head-to-head statistics between two teams.

        Args:
            home_team_id: ID of home team
            away_team_id: ID of away team
            game_date: Date of the game to get statistics before
            schedule_df: DataFrame containing game schedule and results

        Returns:
            Dictionary containing head-to-head statistics
        """
        df_home_team_col = schedule_df['home_team_id']
        df_away_team_col = schedule_df['away_team_id']
        h2h_games = schedule_df[
            (
                (df_home_team_col == home_team_id & df_away_team_col == away_team_id) |
                (df_home_team_col == away_team_id & df_away_team_col == home_team_id)
            ) &
            (schedule_df['date'] < game_date) &
            (schedule_df['status'] == 'Final')
        ].sort_values('date').tail(self.head_to_head_window)

        if h2h_games.empty:
            return {
                'home_win_pct': 0.0,
                'away_win_pct': 0.0,
                'games_played': 0
            }

        home_wins = self._calculate_wins(home_team_id, h2h_games)
        away_wins = self._calculate_wins(away_team_id, h2h_games)

        games_played = len(h2h_games)

        return {
            'home_win_pct': home_wins / games_played,
            'away_win_pct': away_wins / games_played,
            'games_played': games_played
        }
    
    def _calculate_wins(self, team_id: int, h2h_games: pd.DataFrame) -> int:
        """
        Calculates head-to-head wins for a given team.

        Args:
            team_id: ID of the team
            h2h_games: DataFrame containing head-to-head matchups

        Returns:
            Total number of wins for the team in the head-to-head matchups
        """
        return sum(
            (h2h_games['home_team_id'] == team_id) & (h2h_games['home_score'] > h2h_games['away_score']) |
            (h2h_games['away_team_id'] == team_id) & (h2h_games['away_score'] > h2h_games['home_score'])
        )
    