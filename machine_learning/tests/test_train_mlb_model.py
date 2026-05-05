"""
Unit tests for MLBModelTrainer helper methods.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


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


def _make_training_data(n: int) -> pd.DataFrame:
    """Generate a minimal training DataFrame for hyperparameter search tests."""
    from api.src.ml_config import MLB_REQUIRED_FEATURES
    rng = np.random.default_rng(42)
    data = {feat: rng.standard_normal(n) for feat in MLB_REQUIRED_FEATURES}
    data['home_team_won'] = rng.integers(0, 2, n)
    data['game_date'] = _make_game_dates(n)
    return pd.DataFrame(data)


_MOCK_BEST_PARAMS = {
    'model__max_depth': 4,
    'model__learning_rate': 0.05,
    'model__n_estimators': 300,
    'model__subsample': 0.8,
    'model__colsample_bytree': 0.7,
    'model__min_child_weight': 3,
    'model__gamma': 0.1,
}
_MOCK_BEST_SCORE = 0.5421


class TestRunHyperparameterSearch:
    """Tests for MLBModelTrainer._run_hyperparameter_search()."""

    @pytest.fixture
    def xgb_trainer(self):
        from machine_learning.scripts.train_mlb_model import MLBModelTrainer
        return MLBModelTrainer(model_type='xgboost', verbose=False)

    @pytest.fixture
    def rf_trainer(self):
        from machine_learning.scripts.train_mlb_model import MLBModelTrainer
        return MLBModelTrainer(model_type='random_forest', verbose=False)

    @pytest.fixture
    def lr_trainer(self):
        from machine_learning.scripts.train_mlb_model import MLBModelTrainer
        return MLBModelTrainer(model_type='logistic_regression', verbose=False)

    @pytest.fixture
    def mock_search(self):
        """Pre-configured RandomizedSearchCV mock."""
        mock = MagicMock()
        mock.best_params_ = _MOCK_BEST_PARAMS
        mock.best_score_ = _MOCK_BEST_SCORE
        return mock

    def test_raises_value_error_for_random_forest(self, rf_trainer):
        """_run_hyperparameter_search must reject model_type != 'xgboost'."""
        with pytest.raises(ValueError, match="xgboost"):
            rf_trainer._run_hyperparameter_search(_make_training_data(200))

    def test_raises_value_error_for_logistic_regression(self, lr_trainer):
        """_run_hyperparameter_search must reject model_type 'logistic_regression'."""
        with pytest.raises(ValueError, match="xgboost"):
            lr_trainer._run_hyperparameter_search(_make_training_data(200))

    def test_uses_time_series_split_with_five_folds(self, xgb_trainer, mock_search):
        """Search must pass TimeSeriesSplit(n_splits=5) as the cv argument."""
        from sklearn.model_selection import TimeSeriesSplit

        with patch.object(xgb_trainer, 'create_model', return_value=MagicMock()), \
             patch(
                 'machine_learning.scripts.train_mlb_model.RandomizedSearchCV',
                 return_value=mock_search,
             ) as mock_rscv_cls:
            xgb_trainer._run_hyperparameter_search(_make_training_data(200), n_iter=2)

        _, call_kwargs = mock_rscv_cls.call_args
        cv_arg = call_kwargs['cv']
        assert isinstance(cv_arg, TimeSeriesSplit), "cv must be a TimeSeriesSplit instance"
        assert cv_arg.n_splits == 5

    def test_sets_override_params_after_search(self, xgb_trainer, mock_search):
        """After search, _xgboost_override_params must contain best params without 'model__' prefix."""
        expected = {k.replace('model__', ''): v for k, v in _MOCK_BEST_PARAMS.items()}

        with patch.object(xgb_trainer, 'create_model', return_value=MagicMock()), \
             patch('machine_learning.scripts.train_mlb_model.RandomizedSearchCV', return_value=mock_search):
            xgb_trainer._run_hyperparameter_search(_make_training_data(200), n_iter=2)

        assert xgb_trainer._xgboost_override_params == expected

    def test_return_value_structure(self, xgb_trainer, mock_search):
        """Return value must have 'params' dict and 'best_cv_score' float."""
        with patch.object(xgb_trainer, 'create_model', return_value=MagicMock()), \
             patch('machine_learning.scripts.train_mlb_model.RandomizedSearchCV', return_value=mock_search):
            result = xgb_trainer._run_hyperparameter_search(_make_training_data(200), n_iter=2)

        assert 'params' in result
        assert 'best_cv_score' in result
        assert isinstance(result['params'], dict)
        assert result['best_cv_score'] == pytest.approx(_MOCK_BEST_SCORE)

    def test_return_params_strip_model_prefix(self, xgb_trainer, mock_search):
        """Returned 'params' must not contain the 'model__' pipeline prefix."""
        with patch.object(xgb_trainer, 'create_model', return_value=MagicMock()), \
             patch('machine_learning.scripts.train_mlb_model.RandomizedSearchCV', return_value=mock_search):
            result = xgb_trainer._run_hyperparameter_search(_make_training_data(200), n_iter=2)

        for key in result['params']:
            assert not key.startswith('model__'), f"Key '{key}' still has 'model__' prefix"
