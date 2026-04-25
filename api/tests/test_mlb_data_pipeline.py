import pandas as pd
from datetime import datetime, timedelta

from machine_learning.data.processing.mlb_data_pipeline import MLBDataPipeline


def _make_schedule(n_games: int, team1: int = 1, team2: int = 2) -> pd.DataFrame:
    base_date = datetime(2024, 4, 1)
    return pd.DataFrame([
        {
            'game_id': i + 1,
            'date': base_date + timedelta(days=i),
            'home_team_id': team1 if i % 2 == 0 else team2,
            'away_team_id': team2 if i % 2 == 0 else team1,
            'home_score': 3,
            'away_score': 2,
            'status': 'Final',
        }
        for i in range(n_games)
    ])


def _make_teams(team1: int = 1, team2: int = 2) -> pd.DataFrame:
    return pd.DataFrame([
        {'id': team1, 'name': 'Team A', 'division': 'AL East',
         'games_played': 20, 'wins': 10, 'losses': 10, 'winning_percentage': 0.5},
        {'id': team2, 'name': 'Team B', 'division': 'AL East',
         'games_played': 20, 'wins': 10, 'losses': 10, 'winning_percentage': 0.5},
    ])


def _empty_stats() -> pd.DataFrame:
    return pd.DataFrame(columns=['id', 'team_id', 'date'])


START = datetime(2024, 4, 1)
END = datetime(2024, 12, 31)


class TestMLBDataPipelineMinGamesThreshold:
    def test_default_threshold_excludes_early_season_games(self):
        # With threshold=10 and 15 games, games 1-10 are excluded (0-9 prior games each).
        # Games 11-15 have both teams at 10 prior games and are included.
        schedule = _make_schedule(15)
        pipeline = MLBDataPipeline(rolling_window=10, min_games_threshold=10)

        result = pipeline.prepare_training_data(
            schedule_df=schedule,
            teams_df=_make_teams(),
            offensive_stats_df=_empty_stats(),
            defensive_stats_df=_empty_stats(),
            start_date=START,
            end_date=END,
        )

        assert len(result) == 5

    def test_custom_threshold_excludes_correct_games(self):
        # With threshold=3 and 10 games, games 1-3 are excluded (0-2 prior games each).
        # Games 4-10 have both teams at 3+ prior games and are included.
        schedule = _make_schedule(10)
        pipeline = MLBDataPipeline(rolling_window=10, min_games_threshold=3)

        result = pipeline.prepare_training_data(
            schedule_df=schedule,
            teams_df=_make_teams(),
            offensive_stats_df=_empty_stats(),
            defensive_stats_df=_empty_stats(),
            start_date=START,
            end_date=END,
        )

        assert len(result) == 7

    def test_zero_threshold_excludes_nothing(self):
        # With threshold=0 every game is eligible regardless of prior game count.
        schedule = _make_schedule(5)
        pipeline = MLBDataPipeline(rolling_window=10, min_games_threshold=0)

        result = pipeline.prepare_training_data(
            schedule_df=schedule,
            teams_df=_make_teams(),
            offensive_stats_df=_empty_stats(),
            defensive_stats_df=_empty_stats(),
            start_date=START,
            end_date=END,
        )

        assert len(result) == 5
