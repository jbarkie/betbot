"""
Data pipeline utilities for MLB data used to make predictions on game outcomes.
"""
from datetime import datetime
from typing import List, Optional
import pandas as pd
from machine_learning.analysis.mlb_feature_engineering import GameFeatureGenerator
from machine_learning.analysis.mlb_time_series import TeamTimeSeriesAnalyzer


class MLBDataPipeline:
    """
    Prepares MLB game data for model training by combining features from multiple sources.
    """
    def __init__(
        self,
        rolling_window: int = 10,
        head_to_head_window: int = 5
    ):
        """
        Initialize the data pipeline.

        Args:
            rolling_window: Number of games to include in rolling calculations
            head_to_head_window: Number of recent matchups to consider for head-to-head features
        """
        self.time_series_analyzer = TeamTimeSeriesAnalyzer(window_size=rolling_window)
        self.feature_generator = GameFeatureGenerator(
            rolling_window=rolling_window,
            head_to_head_window=head_to_head_window
        )

    def prepare_training_data(
        self,
        schedule_df: pd.DataFrame,
        teams_df: pd.DataFrame,
        offensive_stats_df: pd.DataFrame,
        defensive_stats_df: pd.DataFrame,
        start_date: datetime,
        end_date: datetime,
        features_to_exclude: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """"
        Prepare training data for all completed games within the specified date range.

        Args:
            schedule_df: DataFrame containing game schedule and results
            teams_df: DataFrame containing team information
            offensive_stats_df: DataFrame containing offensive statistics for all teams
            defensive_stats_df: DataFrame containing defensive statistics for all teams
            start_date: Start date for the training data
            end_date: End date for the training data
            features_to_exclude: Optional list of feature names to exclude from the training data
        
        Returns:
            DataFrame containing training data for the specified date range.
        """

        rolling_stats = self.time_series_analyzer.calculate_rolling_stats(schedule_df, teams_df)

        training_games = schedule_df[
            (schedule_df['date'] >= start_date) & 
            (schedule_df['date'] <= end_date) &
            (schedule_df['status'] == 'Final')
        ].copy()

        game_features = []
        for _, game in training_games.iterrows():
            home_team_id = game['home_team_id']
            away_team_id = game['away_team_id']
            game_date = game['date']
            game_id = game.get('game_id', None)

            features = self.feature_generator.generate_game_features(
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                game_date=game_date,
                rolling_stats=rolling_stats,
                offensive_stats=offensive_stats_df,
                defensive_stats=defensive_stats_df,
                schedule_df=schedule_df
            )
            # Add game identifiers and target variables
            features.update({
                'game_id': game_id,
                'game_date': game_date,
                'home_team_id': home_team_id,
                'away_team_id': away_team_id,
                'home_team_won': game['home_score'] > game['away_score'],    
                'run_differential': game['home_score'] - game['away_score']
            })
            game_features.append(features)

        training_data = pd.DataFrame(game_features)

        if features_to_exclude:
            training_data = training_data.drop(columns=features_to_exclude)

        return training_data