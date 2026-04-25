"""
Unit tests for MLBModelTrainer helper methods.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def _make_game_dates(n: int, start: datetime = None) -> pd.Series:
    """Generate a chronological series of n game dates."""
    start = start or datetime(2024, 4, 1)
    return pd.Series([start + timedelta(days=i) for i in range(n)])


class TestComputeSampleWeights:
    """Tests for MLBModelTrainer._compute_sample_weights()."""

    @pytest.fixture
    def trainer(self):
        """Create a trainer instance without DB access."""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from machine_learning.scripts.train_mlb_model import MLBModelTrainer
        return MLBModelTrainer(model_type='random_forest', verbose=False)

    def test_output_length_matches_input(self, trainer):
        """Weights array must have the same length as the input dates."""
        dates = _make_game_dates(50)
        weights = trainer._compute_sample_weights(dates, half_life_days=365)
        assert len(weights) == len(dates)

    def test_all_weights_positive(self, trainer):
        """Every weight must be strictly greater than zero."""
        dates = _make_game_dates(100)
        weights = trainer._compute_sample_weights(dates, half_life_days=365)
        assert np.all(weights > 0)

    def test_weights_monotonically_nondecreasing(self, trainer):
        """Later games must have weight ≥ earlier games (chronological order)."""
        dates = _make_game_dates(200)
        weights = trainer._compute_sample_weights(dates, half_life_days=365)
        assert np.all(np.diff(weights) >= 0)

    def test_first_weight_is_one(self, trainer):
        """The oldest game (day 0) should have weight exactly 1.0."""
        dates = _make_game_dates(10)
        weights = trainer._compute_sample_weights(dates, half_life_days=365)
        assert weights[0] == pytest.approx(1.0, abs=1e-9)

    def test_half_life_ratio(self, trainer):
        """A game exactly half_life_days later should have weight ≈ 2× the oldest."""
        half_life = 180
        # Two dates: day 0 and day half_life
        dates = pd.Series([datetime(2024, 1, 1), datetime(2024, 1, 1) + timedelta(days=half_life)])
        weights = trainer._compute_sample_weights(dates, half_life_days=half_life)
        assert weights[1] / weights[0] == pytest.approx(2.0, rel=1e-6)

    def test_different_half_lives_produce_different_spreads(self, trainer):
        """Shorter half-life should produce a larger max/min ratio."""
        dates = _make_game_dates(365)
        weights_short = trainer._compute_sample_weights(dates, half_life_days=90)
        weights_long = trainer._compute_sample_weights(dates, half_life_days=365)

        ratio_short = weights_short[-1] / weights_short[0]
        ratio_long = weights_long[-1] / weights_long[0]
        assert ratio_short > ratio_long

    def test_single_date_returns_weight_one(self, trainer):
        """A single date should return weight 1.0 (no decay possible)."""
        dates = pd.Series([datetime(2024, 6, 1)])
        weights = trainer._compute_sample_weights(dates, half_life_days=365)
        assert len(weights) == 1
        assert weights[0] == pytest.approx(1.0, abs=1e-9)

    def test_accepts_pandas_datetime_series(self, trainer):
        """Method must accept a pd.Series of datetime objects."""
        dates = pd.Series(pd.date_range(start='2024-04-01', periods=30, freq='D'))
        weights = trainer._compute_sample_weights(dates, half_life_days=365)
        assert len(weights) == 30
        assert np.all(weights > 0)
