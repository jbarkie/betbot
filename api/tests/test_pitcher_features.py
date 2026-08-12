"""
Tests for starting pitcher feature engineering: the join from mlb_pitcher_stats
into the feature matrix, and the median imputation that covers missing starters.
"""

import numpy as np
import pandas as pd
import pytest
from datetime import datetime, timedelta

from machine_learning.data.processing.mlb_data_pipeline import (
    MLBDataPipeline,
    PITCHER_FEATURES,
    build_pitcher_lookup,
    compute_pitcher_medians,
)
from machine_learning.analysis.mlb_feature_engineering import GameFeatureGenerator
from api.src.ml_config import (
    MLB_BASE_FEATURES,
    MLB_PITCHER_FEATURES,
    MLB_REQUIRED_FEATURES,
)


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


def _make_pitcher_stats(rows) -> pd.DataFrame:
    return pd.DataFrame(
        rows, columns=['game_id', 'team_id', 'era', 'whip', 'k9']
    )


START = datetime(2024, 4, 1)
END = datetime(2024, 12, 31)


class TestFeatureContract:
    """The serving contract must describe exactly what the model was fit on."""

    def test_thirty_two_features_total(self):
        assert len(MLB_REQUIRED_FEATURES) == 32

    def test_split_is_twenty_six_plus_six(self):
        assert len(MLB_BASE_FEATURES) == 26
        assert len(MLB_PITCHER_FEATURES) == 6

    def test_pitcher_features_named_as_specified(self):
        assert MLB_PITCHER_FEATURES == [
            'home_starter_era', 'home_starter_whip', 'home_starter_k9',
            'away_starter_era', 'away_starter_whip', 'away_starter_k9',
        ]

    def test_required_features_are_base_then_pitcher(self):
        """Column order is part of the contract — the model is fit positionally."""
        assert MLB_REQUIRED_FEATURES == MLB_BASE_FEATURES + MLB_PITCHER_FEATURES

    def test_no_duplicate_feature_names(self):
        assert len(set(MLB_REQUIRED_FEATURES)) == len(MLB_REQUIRED_FEATURES)

    def test_pipeline_constant_matches_config(self):
        """Guards against the pipeline and the API drifting apart."""
        assert list(PITCHER_FEATURES) == list(MLB_PITCHER_FEATURES)


class TestBuildPitcherLookup:
    """Indexing pitcher rows for join."""

    def test_indexes_by_game_and_team(self):
        df = _make_pitcher_stats([
            ('1', 1, 3.00, 1.10, 9.0),
            ('1', 2, 4.50, 1.40, 7.0),
        ])
        lookup = build_pitcher_lookup(df)
        assert lookup[('1', 1)]['era'] == 3.00
        assert lookup[('1', 2)]['whip'] == 1.40

    def test_game_id_coerced_to_string(self):
        """Schedule game_id may arrive as int; the lookup key must still match."""
        df = _make_pitcher_stats([(1, 1, 3.00, 1.10, 9.0)])
        assert ('1', 1) in build_pitcher_lookup(df)

    def test_empty_or_none_yields_empty_lookup(self):
        assert build_pitcher_lookup(pd.DataFrame()) == {}
        assert build_pitcher_lookup(None) == {}


class TestGeneratorPitcherColumns:
    """generate_game_features must distinguish unknown from genuinely zero."""

    @pytest.fixture
    def generator(self):
        return GameFeatureGenerator()

    @pytest.fixture
    def rolling_stats(self):
        from machine_learning.analysis.mlb_time_series import TeamTimeSeriesAnalyzer
        schedule = _make_schedule(12)
        return TeamTimeSeriesAnalyzer(window_size=10).calculate_rolling_stats(
            schedule, _make_teams()
        )

    def _call(self, generator, rolling_stats, home_pitcher=None, away_pitcher=None):
        return generator.generate_game_features(
            home_team_id=1, away_team_id=2, game_date=pd.Timestamp('2024-05-01'),
            rolling_stats=rolling_stats,
            offensive_stats=_empty_stats(), defensive_stats=_empty_stats(),
            schedule_df=_make_schedule(12),
            home_pitcher=home_pitcher, away_pitcher=away_pitcher,
        )

    def test_emits_all_six_pitcher_columns(self, generator, rolling_stats):
        features = self._call(generator, rolling_stats)
        for column in MLB_PITCHER_FEATURES:
            assert column in features

    def test_missing_pitcher_is_nan_not_zero(self, generator, rolling_stats):
        """Zero ERA would read as a flawless pitcher rather than an unknown one."""
        features = self._call(generator, rolling_stats)
        for column in MLB_PITCHER_FEATURES:
            assert np.isnan(features[column]), f"{column} should be NaN when unknown"

    def test_supplied_pitcher_values_pass_through(self, generator, rolling_stats):
        features = self._call(
            generator, rolling_stats,
            home_pitcher={'era': 2.50, 'whip': 0.95, 'k9': 11.2},
            away_pitcher={'era': 5.10, 'whip': 1.55, 'k9': 6.4},
        )
        assert features['home_starter_era'] == pytest.approx(2.50)
        assert features['home_starter_k9'] == pytest.approx(11.2)
        assert features['away_starter_whip'] == pytest.approx(1.55)

    def test_null_stat_within_record_is_nan(self, generator, rolling_stats):
        """A season debut stored as NULL must not become 0.0."""
        features = self._call(generator, rolling_stats, home_pitcher={'era': None, 'whip': None, 'k9': None})
        assert np.isnan(features['home_starter_era'])

    def test_one_sided_pitcher_data(self, generator, rolling_stats):
        features = self._call(generator, rolling_stats, home_pitcher={'era': 3.0, 'whip': 1.1, 'k9': 9.0})
        assert features['home_starter_era'] == pytest.approx(3.0)
        assert np.isnan(features['away_starter_era'])


class TestComputePitcherMedians:
    """Median, not mean — ERA is right-skewed by blowup outings."""

    def test_median_resists_outliers(self):
        df = pd.DataFrame({'home_starter_era': [3.0, 3.5, 4.0, 81.0]})
        medians = compute_pitcher_medians(df)
        assert medians['home_starter_era'] == pytest.approx(3.75)
        assert medians['home_starter_era'] != pytest.approx(df['home_starter_era'].mean())

    def test_ignores_nan_when_computing(self):
        df = pd.DataFrame({'home_starter_whip': [1.0, np.nan, 2.0]})
        assert compute_pitcher_medians(df)['home_starter_whip'] == pytest.approx(1.5)

    def test_absent_and_all_nan_columns_omitted(self):
        df = pd.DataFrame({'home_starter_era': [np.nan, np.nan]})
        assert compute_pitcher_medians(df) == {}


class TestPipelineJoinAndImputation:
    """End-to-end: pitcher stats joined into training data, gaps median-filled."""

    def _run(self, pitcher_stats_df):
        pipeline = MLBDataPipeline(rolling_window=10, min_games_threshold=10)
        return pipeline, pipeline.prepare_training_data(
            schedule_df=_make_schedule(15),
            teams_df=_make_teams(),
            offensive_stats_df=_empty_stats(),
            defensive_stats_df=_empty_stats(),
            start_date=START,
            end_date=END,
            pitcher_stats_df=pitcher_stats_df,
        )

    def test_pitcher_columns_present_when_stats_supplied(self):
        stats = _make_pitcher_stats([
            (str(g), t, 3.0, 1.2, 8.0) for g in range(11, 16) for t in (1, 2)
        ])
        _, result = self._run(stats)
        for column in MLB_PITCHER_FEATURES:
            assert column in result.columns

    def test_joined_values_land_on_the_right_game_and_team(self):
        """Home and away must not be transposed."""
        stats = _make_pitcher_stats(
            [(str(g), 1, 2.00, 1.00, 10.0) for g in range(11, 16)]
            + [(str(g), 2, 6.00, 1.60, 5.0) for g in range(11, 16)]
        )
        _, result = self._run(stats)
        schedule = _make_schedule(15).set_index('game_id')

        for _, row in result.iterrows():
            # Game 11 is index 10, which is even, so team1 is home; alternates after.
            expected_home = 2.00 if row['home_team_id'] == 1 else 6.00
            assert row['home_starter_era'] == pytest.approx(expected_home)

    def test_missing_games_are_median_imputed_not_nan_or_zero(self):
        # Supply stats for only some of the eligible games (11-15).
        stats = _make_pitcher_stats([
            ('11', 1, 2.0, 1.0, 10.0), ('11', 2, 4.0, 1.4, 6.0),
            ('12', 1, 3.0, 1.2, 8.0), ('12', 2, 5.0, 1.5, 7.0),
        ])
        _, result = self._run(stats)

        for column in MLB_PITCHER_FEATURES:
            assert result[column].notna().all(), f"{column} still has NaN"
            assert (result[column] != 0).all(), f"{column} was zero-filled"

    def test_imputed_value_equals_the_column_median(self):
        stats = _make_pitcher_stats([
            ('11', 1, 2.0, 1.0, 10.0),
            ('12', 1, 4.0, 1.0, 10.0),
            ('13', 1, 9.0, 1.0, 10.0),
        ])
        pipeline, result = self._run(stats)
        # Rows without supplied stats must carry the median of those that had them.
        assert pipeline.pitcher_medians['home_starter_era'] == pytest.approx(
            result['home_starter_era'].median()
        )

    def test_coverage_recorded_before_imputation(self):
        """Coverage must reflect real data, not the post-imputation state."""
        stats = _make_pitcher_stats([('11', 1, 2.0, 1.0, 10.0)])
        pipeline, result = self._run(stats)
        assert 0.0 < pipeline.pitcher_coverage['home_starter_era'] < 1.0
        assert result['home_starter_era'].notna().all()

    def test_omitting_pitcher_stats_leaves_columns_all_nan(self):
        """The 26-feature path stays available and does not invent pitcher values."""
        _, result = self._run(None)
        for column in MLB_PITCHER_FEATURES:
            assert result[column].isna().all()

    def test_row_count_unchanged_by_pitcher_join(self):
        """Imputation must not drop games — that would confound the A/B comparison."""
        _, without = self._run(None)
        _, with_stats = self._run(_make_pitcher_stats([('11', 1, 2.0, 1.0, 10.0)]))
        assert len(without) == len(with_stats)
