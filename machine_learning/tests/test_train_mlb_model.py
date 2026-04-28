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


class TestComputePerMonthAccuracy:
    """Tests for MLBModelTrainer._compute_per_month_accuracy()."""

    @pytest.fixture
    def trainer(self):
        from machine_learning.scripts.train_mlb_model import MLBModelTrainer
        return MLBModelTrainer(model_type='random_forest', verbose=False)

    def test_returns_dict_with_correct_month_keys(self, trainer):
        """Output keys must be the integer month numbers present in test_dates."""
        dates = pd.Series([datetime(2025, 7, 1), datetime(2025, 8, 1), datetime(2025, 9, 1)])
        y_test = pd.Series([1, 0, 1])
        y_pred = np.array([1, 0, 1])
        result = trainer._compute_per_month_accuracy(y_test, y_pred, dates)
        assert set(result.keys()) == {7, 8, 9}

    def test_game_count_per_month(self, trainer):
        """game_count must equal the number of test games that fall in each month."""
        dates = pd.Series(
            [datetime(2025, 7, d) for d in range(1, 11)] +
            [datetime(2025, 8, d) for d in range(1, 6)]
        )
        y_test = pd.Series([1] * 15)
        y_pred = np.array([1] * 15)
        result = trainer._compute_per_month_accuracy(y_test, y_pred, dates)
        assert result[7]['game_count'] == 10
        assert result[8]['game_count'] == 5

    def test_perfect_predictions_give_accuracy_one(self, trainer):
        """Accuracy must be 1.0 when every prediction matches the true label."""
        dates = pd.Series([datetime(2025, 7, i + 1) for i in range(10)])
        y_test = pd.Series([1, 0, 1, 1, 0, 0, 1, 0, 1, 0])
        y_pred = np.array([1, 0, 1, 1, 0, 0, 1, 0, 1, 0])
        result = trainer._compute_per_month_accuracy(y_test, y_pred, dates)
        assert result[7]['accuracy'] == pytest.approx(1.0)

    def test_all_wrong_predictions_give_accuracy_zero(self, trainer):
        """Accuracy must be 0.0 when every prediction is wrong."""
        dates = pd.Series([datetime(2025, 8, i + 1) for i in range(5)])
        y_test = pd.Series([1, 1, 0, 0, 1])
        y_pred = np.array([0, 0, 1, 1, 0])
        result = trainer._compute_per_month_accuracy(y_test, y_pred, dates)
        assert result[8]['accuracy'] == pytest.approx(0.0)

    def test_accuracy_in_valid_range(self, trainer):
        """Accuracy values must lie in [0.0, 1.0] for all months."""
        rng = np.random.default_rng(0)
        dates = pd.Series([datetime(2025, 7, i + 1) for i in range(20)])
        y_test = pd.Series(rng.integers(0, 2, 20))
        y_pred = rng.integers(0, 2, 20)
        result = trainer._compute_per_month_accuracy(y_test, y_pred, dates)
        for data in result.values():
            assert 0.0 <= data['accuracy'] <= 1.0


class TestComputeLearningCurve:
    """Tests for MLBModelTrainer._compute_learning_curve()."""

    @pytest.fixture
    def trainer(self):
        from machine_learning.scripts.train_mlb_model import MLBModelTrainer
        return MLBModelTrainer(model_type='random_forest', verbose=False)

    @pytest.fixture
    def small_dataset(self):
        """Minimal labelled arrays for fast sklearn training."""
        from api.src.ml_config import MLB_REQUIRED_FEATURES
        rng = np.random.default_rng(42)
        n_train, n_test = 100, 30
        X_train = pd.DataFrame(
            rng.random((n_train, len(MLB_REQUIRED_FEATURES))),
            columns=MLB_REQUIRED_FEATURES
        )
        y_train = pd.Series(rng.integers(0, 2, n_train))
        X_test = pd.DataFrame(
            rng.random((n_test, len(MLB_REQUIRED_FEATURES))),
            columns=MLB_REQUIRED_FEATURES
        )
        y_test = pd.Series(rng.integers(0, 2, n_test))
        return X_train, y_train, X_test, y_test

    def test_returns_five_points(self, trainer, small_dataset):
        """Curve must contain exactly five data points (20/40/60/80/100%)."""
        X_train, y_train, X_test, y_test = small_dataset
        result = trainer._compute_learning_curve(X_train, y_train, X_test, y_test)
        assert len(result) == 5

    def test_output_keys(self, trainer, small_dataset):
        """Each entry must have 'fraction', 'train_size', and 'test_accuracy' keys."""
        X_train, y_train, X_test, y_test = small_dataset
        result = trainer._compute_learning_curve(X_train, y_train, X_test, y_test)
        for point in result:
            assert {'fraction', 'train_size', 'test_accuracy'} <= point.keys()

    def test_fractions_match_expected(self, trainer, small_dataset):
        """Fraction values must be exactly [0.2, 0.4, 0.6, 0.8, 1.0]."""
        X_train, y_train, X_test, y_test = small_dataset
        result = trainer._compute_learning_curve(X_train, y_train, X_test, y_test)
        assert [p['fraction'] for p in result] == [0.2, 0.4, 0.6, 0.8, 1.0]

    def test_train_sizes_monotonically_increasing(self, trainer, small_dataset):
        """Each successive point must use at least as much training data as the previous."""
        X_train, y_train, X_test, y_test = small_dataset
        result = trainer._compute_learning_curve(X_train, y_train, X_test, y_test)
        sizes = [p['train_size'] for p in result]
        assert sizes == sorted(sizes)

    def test_test_accuracy_in_valid_range(self, trainer, small_dataset):
        """test_accuracy must be in [0.0, 1.0] for every data point."""
        X_train, y_train, X_test, y_test = small_dataset
        result = trainer._compute_learning_curve(X_train, y_train, X_test, y_test)
        for point in result:
            assert 0.0 <= point['test_accuracy'] <= 1.0

    def test_weighted_curve_same_structure(self, trainer, small_dataset):
        """Passing uniform sample weights must produce the same structure as no weights."""
        X_train, y_train, X_test, y_test = small_dataset
        weights = np.ones(len(X_train))
        result = trainer._compute_learning_curve(X_train, y_train, X_test, y_test, sample_weights=weights)
        assert len(result) == 5
        for point in result:
            assert 0.0 <= point['test_accuracy'] <= 1.0
