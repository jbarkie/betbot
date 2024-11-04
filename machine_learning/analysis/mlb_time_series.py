"""
Time series analysis utilities for MLB game predictions.
"""
from datetime import datetime
from typing import Tuple, Dict
import pandas as pd
import numpy as np

class TeamTimeSeriesAnalyzer:
    """
    Handles time series analysis for MLB team performance metrics.
    """
    def __init__(self, window_size: int = 10):
        """
        Initialize the analyzer with a window size for rolling calculations.
        
        Args:
            window_size: Number of games to include in rolling calculations
        """
        self.window_size = window_size

    def calculate_rolling_stats(
        self,
        schedule_df: pd.DataFrame,
        teams_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate rolling statistics for each team.
        
        Args:
            schedule_df: DataFrame containing game schedule and results
            teams_df: DataFrame containing team information
            
        Returns:
            DataFrame containing rolling statistics for all teams
        """
        completed_games = schedule_df[schedule_df['status'] == 'Final'].copy()
        completed_games['date'] = pd.to_datetime(completed_games['date'])
        completed_games = completed_games.sort_values('date')
        
        rolling_stats = []
        
        for team_id in teams_df['id'].unique():
            team_stats = self._calculate_team_stats(completed_games, team_id)
            rolling_stats.append(team_stats)
        
        return pd.concat(rolling_stats).reset_index(drop=True)

    def _calculate_team_stats(
        self,
        completed_games: pd.DataFrame,
        team_id: int
    ) -> pd.DataFrame:
        """
        Calculate rolling statistics for a single team.
        
        Args:
            completed_games: DataFrame of completed games
            team_id: ID of the team to analyze
            
        Returns:
            DataFrame containing rolling statistics for the specified team
        """
        team_games = completed_games[
            (completed_games['home_team_id'] == team_id) |
            (completed_games['away_team_id'] == team_id)
        ].copy()

        if team_games.empty:
            return pd.DataFrame() # return empty DataFrame if no games found for given team
        
        team_games['is_win'] = np.where(
            team_games['home_team_id'] == team_id,
            team_games['home_score'] > team_games['away_score'],
            team_games['away_score'] > team_games['home_score']
        )
        
        team_games['runs_scored'] = np.where(
            team_games['home_team_id'] == team_id,
            team_games['home_score'],
            team_games['away_score']
        )
        
        team_games['runs_allowed'] = np.where(
            team_games['home_team_id'] == team_id,
            team_games['away_score'],
            team_games['home_score']
        )
        
        rolling_stats = pd.DataFrame({
            'team_id': team_id,
            'date': team_games['date'],
            'rolling_win_pct': round(team_games['is_win'].rolling(window=self.window_size).mean(), 3),
            'rolling_runs_scored': team_games['runs_scored'].rolling(window=self.window_size).mean(),
            'rolling_runs_allowed': team_games['runs_allowed'].rolling(window=self.window_size).mean(),
            'streak': team_games['is_win'].rolling(window=self.window_size).sum(),
            'last_game_date': team_games['date'].shift(1)
        })

        rolling_stats['days_rest'] = rolling_stats['date'].diff().dt.days

        if not rolling_stats.empty:
            last_game_date = rolling_stats['date'].iloc[-1].date()
            days_since_last_game = (datetime.now().date() - last_game_date).days
            rolling_stats.loc[rolling_stats.index[-1], 'days_rest'] = days_since_last_game
            
            rolling_stats['last_game_date'] = last_game_date
            rolling_stats['days_since_last_game'] = days_since_last_game

        return rolling_stats
        
class MomentumAnalyzer:
    """
    Analyzes team momentum and performance trends.
    """
    @staticmethod
    def identify_hot_cold_teams(
        rolling_stats: pd.DataFrame,
        teams_df: pd.DataFrame,
        n_teams: int = 5
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Identify current hot and cold teams based on recent performance.
        
        Args:
            rolling_stats: Rolling statistics calculated for all teams
            teams_df: DataFrame containing team information
            n_teams: Number of top/bottom teams to identify
            
        Returns:
            Tuple of DataFrames containing hot and cold teams
        """
        latest_stats = rolling_stats.sort_values('date').groupby('team_id').last().reset_index()
        latest_stats = pd.merge(
            latest_stats,
            teams_df[['id', 'name']],
            left_on='team_id',
            right_on='id'
        )
        
        hot_teams = latest_stats.nlargest(n_teams, 'rolling_win_pct')
        cold_teams = latest_stats.nsmallest(n_teams, 'rolling_win_pct')
        
        return hot_teams, cold_teams

class RestAnalyzer:
    """
    Analyzes the impact of rest days on team performance.
    """
    @staticmethod
    def calculate_rest_impact(
        rolling_stats: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Calculate the impact of rest days on team performance.
        
        Args:
            rolling_stats: Rolling statistics calculated for all teams
            
        Returns:
            Dictionary containing average win percentage by rest category
        """
        rolling_stats = rolling_stats.copy()
        rolling_stats['rest_category'] = pd.cut(
            rolling_stats['days_rest'],
            bins=[-np.inf, 0, 1, 2, np.inf],
            labels=['Back-to-back', '1 day', '2 days', '3+ days']
        )
        
        return rolling_stats.groupby('rest_category', observed=True)['rolling_win_pct'].mean().to_dict()