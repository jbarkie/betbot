"""
Data pipeline utilities for MLB data used to make predictions on game outcomes.
"""
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd
from machine_learning.analysis.mlb_feature_engineering import GameFeatureGenerator
from machine_learning.analysis.mlb_time_series import TeamTimeSeriesAnalyzer

# Starting pitcher feature columns produced when pitcher stats are supplied.
# Sourced from ml_config so the training pipeline and the serving contract cannot
# drift apart.
from api.src.ml_config import MLB_PITCHER_FEATURES as PITCHER_FEATURES


def build_pitcher_lookup(pitcher_stats_df: pd.DataFrame) -> Dict[Tuple[str, int], Dict]:
    """
    Index pitcher stat rows by (game_id, team_id) for constant-time lookup.

    Args:
        pitcher_stats_df: DataFrame with game_id, team_id, era, whip, k9

    Returns:
        Mapping of (game_id, team_id) to a dict of era/whip/k9
    """
    if pitcher_stats_df is None or pitcher_stats_df.empty:
        return {}

    # Read column-wise rather than with iterrows(). iterrows() builds a Series per
    # row, which upcasts a mixed int/float row to float64 — an integer game_id then
    # stringifies as "1.0" and silently fails to match the schedule's "1".
    columns = pitcher_stats_df.columns
    game_ids = pitcher_stats_df['game_id'].to_numpy()
    team_ids = pitcher_stats_df['team_id'].to_numpy()
    stats = {
        key: pitcher_stats_df[key].to_numpy() if key in columns else None
        for key in ('era', 'whip', 'k9')
    }

    lookup = {}
    for i in range(len(pitcher_stats_df)):
        game_id, team_id = game_ids[i], team_ids[i]
        if pd.isna(game_id) or pd.isna(team_id):
            continue
        lookup[(_normalize_game_id(game_id), int(team_id))] = {
            key: (None if values is None or pd.isna(values[i]) else values[i])
            for key, values in stats.items()
        }

    return lookup


def _normalize_game_id(value) -> str:
    """
    Render a game id as the string form used throughout the schedule.

    Numeric ids arrive as int, numpy integer, or float depending on how pandas
    typed the column, and a float would stringify with a trailing ".0".
    """
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if hasattr(value, 'item'):
        value = value.item()
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
    return str(value)


def compute_pitcher_medians(df: pd.DataFrame) -> Dict[str, float]:
    """
    Compute the median of each starting pitcher feature present in a DataFrame.

    Medians are used instead of means because ERA and WHIP are right-skewed: a
    handful of blowup outings would drag a mean well above the typical starter.

    Args:
        df: DataFrame that may contain the pitcher feature columns

    Returns:
        Mapping of column name to median, omitting columns that are absent or all-NaN
    """
    medians = {}
    for column in PITCHER_FEATURES:
        if column not in df.columns:
            continue
        median = df[column].median()
        if pd.notna(median):
            medians[column] = float(median)
    return medians


class MLBDataPipeline:
    """
    Prepares MLB game data for model training by combining features from multiple sources.
    """
    def __init__(
        self,
        rolling_window: int = 10,
        head_to_head_window: int = 5,
        min_games_threshold: int = 10
    ):
        """
        Initialize the data pipeline.

        Args:
            rolling_window: Number of games to include in rolling calculations
            head_to_head_window: Number of recent matchups to consider for head-to-head features
            min_games_threshold: Minimum prior games required for a team to be included in training
        """
        self.min_games_threshold = min_games_threshold
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
        features_to_exclude: Optional[List[str]] = None,
        pitcher_stats_df: Optional[pd.DataFrame] = None
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
            pitcher_stats_df: Optional DataFrame of cumulative pre-game starting pitcher
                stats; when supplied, six pitcher feature columns are added and any
                missing values are median-imputed

        Returns:
            DataFrame containing training data for the specified date range.
        """

        # Ensure date columns are pandas datetime for proper comparisons
        schedule_df = schedule_df.copy()
        schedule_df['date'] = pd.to_datetime(schedule_df['date'])
        offensive_stats_df = offensive_stats_df.copy()
        offensive_stats_df['date'] = pd.to_datetime(offensive_stats_df['date'])
        defensive_stats_df = defensive_stats_df.copy()
        defensive_stats_df['date'] = pd.to_datetime(defensive_stats_df['date'])

        pitcher_lookup = build_pitcher_lookup(pitcher_stats_df)

        rolling_stats = self.time_series_analyzer.calculate_rolling_stats(schedule_df, teams_df)

        training_games = schedule_df[
            (schedule_df['date'] >= pd.Timestamp(start_date)) &
            (schedule_df['date'] <= pd.Timestamp(end_date)) &
            (schedule_df['status'] == 'Final')
        ].copy()

        game_features = []
        for _, game in training_games.iterrows():
            home_team_id = game['home_team_id']
            away_team_id = game['away_team_id']
            game_date = game['date']  # Already a Timestamp after pd.to_datetime conversion
            game_id = game.get('game_id', None)

            latest_home_stats = self.feature_generator._get_recent_stats(home_team_id, game_date, rolling_stats)
            latest_away_stats = self.feature_generator._get_recent_stats(away_team_id, game_date, rolling_stats)

            if (latest_home_stats.get('games_played', 0) < self.min_games_threshold or
                    latest_away_stats.get('games_played', 0) < self.min_games_threshold):
                continue

            features = self.feature_generator.generate_game_features(
                home_team_id=home_team_id,
                away_team_id=away_team_id,
                game_date=game_date,
                rolling_stats=rolling_stats,
                offensive_stats=offensive_stats_df,
                defensive_stats=defensive_stats_df,
                schedule_df=schedule_df,
                home_pitcher=pitcher_lookup.get(
                    (_normalize_game_id(game_id), int(home_team_id))),
                away_pitcher=pitcher_lookup.get(
                    (_normalize_game_id(game_id), int(away_team_id)))
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

        # Median-impute pitcher features. This has to happen here rather than being
        # left to the model pipeline, because the trainer fills residual NaN with 0
        # and a 0.00 ERA would present a missing starter as an untouchable one.
        self.pitcher_medians = compute_pitcher_medians(training_data)
        self.pitcher_coverage = {
            column: float(training_data[column].notna().mean())
            for column in PITCHER_FEATURES if column in training_data.columns
        }
        for column, median in self.pitcher_medians.items():
            training_data[column] = training_data[column].fillna(median)

        if features_to_exclude:
            training_data = training_data.drop(columns=features_to_exclude)

        return training_data