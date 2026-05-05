#!/usr/bin/env python3
"""
MLB Model Training Script

This script trains machine learning models to predict MLB game outcomes using
historical data, team statistics, and engineered features.

Usage:
    python train_mlb_model.py [--model-type MODEL] [--start-date DATE] [--end-date DATE] [--verbose]

Options:
    --model-type            Type of model to train: random_forest, logistic_regression, xgboost (default: random_forest)
    --start-date            Start date for training data (YYYY-MM-DD format, default: 90 days ago)
    --end-date              End date for training data (YYYY-MM-DD format, default: today)
    --verbose               Enable verbose logging output
    --test-split            Fraction of data to use for testing (default: 0.2)
    --diagnostics           Print per-month accuracy, class balance, learning curve, and feature importances
    --temporal-weighting    Apply exponential decay sample weights (recent games weighted higher)
    --half-life             Half-life in days for temporal weighting (default: 365)
    --hyperparameter-search Run RandomizedSearchCV over XGBoost params (requires --model-type xgboost)
    --search-iter           Number of parameter settings sampled in search (default: 50)
"""

import sys
import argparse
import calendar
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
import warnings

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import required modules
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import TimeSeriesSplit, cross_val_score, RandomizedSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import joblib

from shared.database import connect_to_db
from machine_learning.data.models.mlb_models import MLBTeam, MLBOffensiveStats, MLBDefensiveStats, MLBSchedule
from machine_learning.data.processing.mlb_data_pipeline import MLBDataPipeline
from api.src.ml_config import MLB_MODELS_DIR, MLB_REQUIRED_FEATURES

# Suppress sklearn warnings for cleaner output
warnings.filterwarnings('ignore', category=UserWarning)


class MLBModelTrainer:
    """Handles training and evaluation of MLB prediction models."""

    def __init__(self, model_type: str = 'random_forest', verbose: bool = False):
        """
        Initialize the model trainer.

        Args:
            model_type: Type of model to train (random_forest, logistic_regression, xgboost)
            verbose: Enable verbose logging
        """
        self.model_type = model_type
        self.verbose = verbose
        self.model = None
        self.pipeline = None
        self.feature_importances = {}
        self.metrics = {}
        self._xgboost_override_params = {}

        # Set up logging
        self._setup_logging()

    def _setup_logging(self):
        """Set up logging configuration."""
        log_level = logging.DEBUG if self.verbose else logging.INFO

        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)-8s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        self.logger = logging.getLogger(__name__)

    def fetch_data_from_database(self) -> tuple:
        """
        Fetch all necessary data from the database.

        Returns:
            Tuple of (schedule_df, teams_df, offensive_stats_df, defensive_stats_df)
        """
        self.logger.info("Fetching data from database...")

        session = connect_to_db()

        try:
            # Fetch all data
            schedule_records = session.query(MLBSchedule).all()
            teams_records = session.query(MLBTeam).all()
            offensive_records = session.query(MLBOffensiveStats).all()
            defensive_records = session.query(MLBDefensiveStats).all()

            # Convert to DataFrames
            schedule_df = pd.DataFrame([{
                'game_id': r.game_id,
                'date': r.date,
                'home_team_id': r.home_team_id,
                'away_team_id': r.away_team_id,
                'home_score': r.home_score,
                'away_score': r.away_score,
                'status': r.status
            } for r in schedule_records])

            teams_df = pd.DataFrame([{
                'id': r.id,
                'name': r.name,
                'division': r.division,
                'games_played': r.games_played,
                'wins': r.wins,
                'losses': r.losses,
                'winning_percentage': r.winning_percentage
            } for r in teams_records])

            offensive_df = pd.DataFrame([{
                'id': r.id,
                'team_id': r.team_id,
                'date': r.date,
                'team_batting_average': r.team_batting_average,
                'runs_scored': r.runs_scored,
                'home_runs': r.home_runs,
                'on_base_percentage': r.on_base_percentage,
                'slugging_percentage': r.slugging_percentage
            } for r in offensive_records])

            defensive_df = pd.DataFrame([{
                'id': r.id,
                'team_id': r.team_id,
                'date': r.date,
                'team_era': r.team_era,
                'runs_allowed': r.runs_allowed,
                'whip': r.whip,
                'strikeouts': r.strikeouts,
                'avg_against': r.avg_against
            } for r in defensive_records])

            self.logger.info(f"Fetched {len(schedule_df)} games, {len(teams_df)} teams")
            self.logger.info(f"Fetched {len(offensive_df)} offensive stats, {len(defensive_df)} defensive stats")

            return schedule_df, teams_df, offensive_df, defensive_df

        finally:
            session.close()

    def prepare_training_data(
        self,
        schedule_df: pd.DataFrame,
        teams_df: pd.DataFrame,
        offensive_df: pd.DataFrame,
        defensive_df: pd.DataFrame,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """
        Prepare training data using the MLBDataPipeline.

        Args:
            schedule_df: Game schedule data
            teams_df: Team information
            offensive_df: Offensive statistics
            defensive_df: Defensive statistics
            start_date: Start date for training data
            end_date: End date for training data

        Returns:
            DataFrame with engineered features ready for training.
            Includes game_date column for temporal analysis; train_and_evaluate() handles exclusion.
        """
        self.logger.info(f"Preparing training data from {start_date.date()} to {end_date.date()}...")

        pipeline = MLBDataPipeline(rolling_window=10, head_to_head_window=5)

        # game_date is retained here so train_and_evaluate() can use it for temporal weighting
        # and per-month diagnostics. It is not included in MLB_REQUIRED_FEATURES so it will
        # not enter the feature matrix X.
        training_data = pipeline.prepare_training_data(
            schedule_df=schedule_df,
            teams_df=teams_df,
            offensive_stats_df=offensive_df,
            defensive_stats_df=defensive_df,
            start_date=start_date,
            end_date=end_date,
            features_to_exclude=['game_id', 'home_team_id', 'away_team_id', 'run_differential']
        )

        self.logger.info(f"Prepared {len(training_data)} games for training")

        return training_data

    def create_model(self) -> Pipeline:
        """
        Create a machine learning pipeline based on the specified model type.

        Returns:
            Sklearn pipeline with preprocessing and model
        """
        self.logger.info(f"Creating {self.model_type} model pipeline...")

        # Define preprocessing steps
        preprocessor = Pipeline([
            ('imputer', SimpleImputer(strategy='mean')),
            ('scaler', StandardScaler())
        ])

        # Define model based on type
        if self.model_type == 'random_forest':
            model = RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=10,
                min_samples_leaf=4,
                random_state=42,
                n_jobs=1
            )
        elif self.model_type == 'logistic_regression':
            model = LogisticRegression(
                max_iter=10000,
                random_state=42,
                n_jobs=1
            )
        elif self.model_type == 'xgboost':
            try:
                from xgboost import XGBClassifier
            except ImportError:
                raise ImportError(
                    "xgboost is not installed. Run: pip install xgboost"
                )
            xgb_params = dict(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                eval_metric='logloss',
                verbosity=0
            )
            xgb_params.update(self._xgboost_override_params)
            model = XGBClassifier(**xgb_params)
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")

        # Create pipeline
        pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('model', model)
        ])

        return pipeline

    def _compute_sample_weights(self, game_dates: pd.Series, half_life_days: int) -> np.ndarray:
        """
        Compute exponential decay sample weights so recent games have higher influence.

        Weight formula: w_i = exp(ln(2) / half_life * days_elapsed_i)
        The most recent game's weight is 2× a game played half_life_days earlier.

        Args:
            game_dates: Series of game dates (datetime or date-like)
            half_life_days: Number of days for weight to halve

        Returns:
            Array of weights, same length as game_dates, monotonically non-decreasing with date
        """
        dates = pd.to_datetime(game_dates)
        date_min = dates.min()
        days_elapsed = (dates - date_min).dt.days.values.astype(float)
        lam = np.log(2) / half_life_days
        weights = np.exp(lam * days_elapsed)
        return weights

    def _compute_per_month_accuracy(
        self,
        y_test: pd.Series,
        y_pred: np.ndarray,
        test_dates: pd.Series
    ) -> dict:
        """
        Break down test-set accuracy by calendar month.

        Args:
            y_test: True labels (test set)
            y_pred: Predicted labels (test set)
            test_dates: Game dates corresponding to the test set

        Returns:
            Dict mapping month number → {'accuracy': float, 'game_count': int}
        """
        results = {}
        dates = pd.to_datetime(test_dates).reset_index(drop=True)
        y_test_arr = np.array(y_test)
        y_pred_arr = np.array(y_pred)

        for month in sorted(dates.dt.month.unique()):
            mask = (dates.dt.month == month).values
            if mask.sum() == 0:
                continue
            acc = accuracy_score(y_test_arr[mask], y_pred_arr[mask])
            results[int(month)] = {'accuracy': float(acc), 'game_count': int(mask.sum())}

        return results

    def _compute_learning_curve(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        sample_weights: np.ndarray = None
    ) -> list:
        """
        Compute test accuracy at 20/40/60/80/100% of chronological training data.

        Args:
            X_train: Training features
            y_train: Training labels
            X_test: Test features (fixed)
            y_test: Test labels (fixed)
            sample_weights: Optional array of weights for the training set (same length as X_train)

        Returns:
            List of dicts with keys 'fraction', 'train_size', 'test_accuracy'
        """
        fractions = [0.2, 0.4, 0.6, 0.8, 1.0]
        results = []

        for frac in fractions:
            n = max(10, int(len(X_train) * frac))
            X_sub = X_train.iloc[:n]
            y_sub = y_train.iloc[:n]
            w_sub = sample_weights[:n] if sample_weights is not None else None

            sub_pipeline = self.create_model()
            if w_sub is not None:
                sub_pipeline.fit(X_sub, y_sub, model__sample_weight=w_sub)
            else:
                sub_pipeline.fit(X_sub, y_sub)

            y_pred = sub_pipeline.predict(X_test)
            acc = accuracy_score(y_test, y_pred)
            results.append({
                'fraction': frac,
                'train_size': n,
                'test_accuracy': round(float(acc), 4)
            })

        return results

    def _run_hyperparameter_search(
        self,
        training_data: pd.DataFrame,
        test_split: float = 0.2,
        n_iter: int = 50
    ) -> dict:
        """
        Run RandomizedSearchCV over XGBoost hyperparameters using TimeSeriesSplit.

        Sets self._xgboost_override_params to the best-found params so that a
        subsequent call to create_model() (and therefore train_and_evaluate()) uses
        them automatically.  Only valid when model_type == 'xgboost'.

        Args:
            training_data: Prepared training data (same format as train_and_evaluate expects)
            test_split: Fraction held out as test set — search runs only on the training portion
            n_iter: Number of parameter settings sampled by RandomizedSearchCV

        Returns:
            dict with keys 'params' (best param dict, 'model__' prefix stripped) and
            'best_cv_score' (mean CV accuracy of the best candidate)
        """
        if self.model_type != 'xgboost':
            raise ValueError(
                f"--hyperparameter-search is only supported for model_type 'xgboost', "
                f"got '{self.model_type}'"
            )

        self.logger.info(
            f"Running randomized hyperparameter search "
            f"(n_iter={n_iter}, cv=TimeSeriesSplit(n_splits=5))..."
        )
        self.logger.info("This may take several minutes.")

        X = training_data[MLB_REQUIRED_FEATURES].copy().fillna(0)
        y = training_data['home_team_won'].astype(int)
        split_idx = int(len(X) * (1 - test_split))
        X_train = X.iloc[:split_idx]
        y_train = y.iloc[:split_idx]

        param_distributions = {
            'model__max_depth': [3, 4, 5, 6, 7, 8],
            'model__learning_rate': [0.01, 0.05, 0.08, 0.1, 0.15, 0.2],
            'model__n_estimators': [100, 200, 300, 500],
            'model__subsample': [0.6, 0.7, 0.8, 0.9, 1.0],
            'model__colsample_bytree': [0.6, 0.7, 0.8, 0.9, 1.0],
            'model__min_child_weight': [1, 3, 5, 7],
            'model__gamma': [0, 0.1, 0.2, 0.5],
        }

        tscv = TimeSeriesSplit(n_splits=5)
        search = RandomizedSearchCV(
            estimator=self.create_model(),
            param_distributions=param_distributions,
            n_iter=n_iter,
            cv=tscv,
            scoring='accuracy',
            n_jobs=1,
            random_state=42,
            verbose=2 if self.verbose else 0,
        )

        search.fit(X_train, y_train)

        best_params = {
            k.replace('model__', ''): v
            for k, v in search.best_params_.items()
        }

        self.logger.info(f"\nSearch complete.")
        self.logger.info(f"Best CV accuracy: {search.best_score_:.4f}")
        self.logger.info(f"Best params:\n{json.dumps(best_params, indent=2)}")

        self._xgboost_override_params = best_params

        return {
            'params': best_params,
            'best_cv_score': float(search.best_score_),
        }

    def train_and_evaluate(
        self,
        training_data: pd.DataFrame,
        test_split: float = 0.2,
        diagnostics: bool = False,
        sample_weights: np.ndarray = None
    ):
        """
        Train and evaluate the model using time series cross-validation.

        Args:
            training_data: Prepared training data (must include home_team_won; game_date if available)
            test_split: Fraction of data to use for final testing
            diagnostics: If True, print per-month accuracy, learning curve, and full feature importance
            sample_weights: Optional array of sample weights (same length as training_data rows)
        """
        self.logger.info("Starting model training and evaluation...")

        # Class balance (always reported)
        home_win_rate = training_data['home_team_won'].astype(int).mean()
        self.logger.info(
            f"Class balance — home win rate: {home_win_rate:.2%}  |  "
            f"away win rate: {1 - home_win_rate:.2%}"
        )

        # Retain game_date series for diagnostics and temporal weighting
        game_dates = training_data['game_date'].copy() if 'game_date' in training_data.columns else None

        # Separate features and target
        X = training_data[MLB_REQUIRED_FEATURES].copy()
        y = training_data['home_team_won'].astype(int)

        # Handle any remaining missing values
        X = X.fillna(0)

        # Split data chronologically (important for time series)
        split_idx = int(len(X) * (1 - test_split))
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        self.logger.info(f"Training set: {len(X_train)} games")
        self.logger.info(f"Test set: {len(X_test)} games")

        # Slice sample weights to training portion
        weights_train = None
        if sample_weights is not None:
            weights_train = sample_weights[:split_idx]
            w_min, w_max = weights_train.min(), weights_train.max()
            self.logger.info(
                f"Temporal weights — min: {w_min:.4f}, max: {w_max:.4f}, ratio: {w_max / w_min:.2f}"
            )

        # Create pipeline
        self.pipeline = self.create_model()

        # Time series cross-validation
        self.logger.info("Performing time series cross-validation...")
        tscv = TimeSeriesSplit(n_splits=5)

        if weights_train is not None:
            # Manual CV to propagate sample weights
            cv_scores_list = []
            for train_idx, val_idx in tscv.split(X_train):
                X_cv_tr, X_cv_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
                y_cv_tr, y_cv_val = y_train.iloc[train_idx], y_train.iloc[val_idx]
                w_cv_tr = weights_train[train_idx]
                cv_pipe = self.create_model()
                cv_pipe.fit(X_cv_tr, y_cv_tr, model__sample_weight=w_cv_tr)
                cv_scores_list.append(accuracy_score(y_cv_val, cv_pipe.predict(X_cv_val)))
            cv_scores = np.array(cv_scores_list)
        else:
            cv_scores = cross_val_score(
                self.pipeline, X_train, y_train,
                cv=tscv, scoring='accuracy', n_jobs=1
            )

        self.logger.info(f"Cross-validation scores: {cv_scores}")
        self.logger.info(f"Mean CV accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")

        # Train on full training set
        self.logger.info("Training final model on full training set...")
        if weights_train is not None:
            self.pipeline.fit(X_train, y_train, model__sample_weight=weights_train)
        else:
            self.pipeline.fit(X_train, y_train)

        # Evaluate on test set
        self.logger.info("Evaluating on test set...")
        y_pred = self.pipeline.predict(X_test)
        y_pred_proba = self.pipeline.predict_proba(X_test)[:, 1]

        # Calculate metrics
        self.metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, zero_division=0),
            'recall': recall_score(y_test, y_pred, zero_division=0),
            'f1': f1_score(y_test, y_pred, zero_division=0),
            'roc_auc': roc_auc_score(y_test, y_pred_proba),
            'cv_mean': float(cv_scores.mean()),
            'cv_std': float(cv_scores.std()),
            'train_size': len(X_train),
            'test_size': len(X_test)
        }

        self.logger.info("\nModel Performance:")
        self.logger.info(f"  Accuracy:  {self.metrics['accuracy']:.4f}")
        self.logger.info(f"  Precision: {self.metrics['precision']:.4f}")
        self.logger.info(f"  Recall:    {self.metrics['recall']:.4f}")
        self.logger.info(f"  F1 Score:  {self.metrics['f1']:.4f}")
        self.logger.info(f"  ROC AUC:   {self.metrics['roc_auc']:.4f}")

        # Feature importances for tree-based models (always shown)
        if self.model_type in ('random_forest', 'xgboost'):
            importances = self.pipeline.named_steps['model'].feature_importances_
            self.feature_importances = dict(zip(MLB_REQUIRED_FEATURES, importances))
            sorted_features = sorted(self.feature_importances.items(), key=lambda x: x[1], reverse=True)

            if diagnostics:
                self.logger.info("\nFeature Importance Ranking (all 26):")
                for i, (feature, importance) in enumerate(sorted_features, 1):
                    self.logger.info(f"  {i:2d}. {feature:<35} {importance:.4f}")
            else:
                self.logger.info("\nTop 10 Most Important Features:")
                for feature, importance in sorted_features[:10]:
                    self.logger.info(f"  {feature}: {importance:.4f}")

        # Diagnostics block
        if diagnostics:
            self.logger.info("\n" + "=" * 50)
            self.logger.info("DIAGNOSTICS")
            self.logger.info("=" * 50)

            # Per-month accuracy breakdown
            if game_dates is not None:
                test_dates = game_dates.iloc[split_idx:].reset_index(drop=True)
                month_accuracy = self._compute_per_month_accuracy(y_test, y_pred, test_dates)
                self.logger.info("\nPer-Month Accuracy (test set):")
                self.logger.info(f"  {'Month':<10} {'Games':>6} {'Accuracy':>10}")
                self.logger.info(f"  {'-'*28}")
                for month, data in month_accuracy.items():
                    month_name = calendar.month_abbr[month]
                    self.logger.info(
                        f"  {month_name:<10} {data['game_count']:>6} {data['accuracy']:>10.4f}"
                    )
            else:
                self.logger.warning("game_date not available — skipping per-month breakdown")

            # Learning curve
            self.logger.info("\nLearning Curve (chronological training subsets → fixed test set):")
            self.logger.info(f"  {'Fraction':<10} {'Train Size':>12} {'Test Accuracy':>14}")
            self.logger.info(f"  {'-'*38}")
            lc_results = self._compute_learning_curve(X_train, y_train, X_test, y_test, weights_train)
            for point in lc_results:
                self.logger.info(
                    f"  {point['fraction']:<10.0%} {point['train_size']:>12} {point['test_accuracy']:>14.4f}"
                )

    def save_model(self, version: str = "1.0"):
        """
        Save the trained model and metadata to disk.

        Args:
            version: Version string for the model
        """
        self.logger.info(f"Saving model version {version}...")

        # Ensure models directory exists
        MLB_MODELS_DIR.mkdir(parents=True, exist_ok=True)

        # Define file paths
        model_filename = f"mlb_predictor_v{version}.joblib"
        metadata_filename = f"mlb_predictor_v{version}_metadata.json"

        model_path = MLB_MODELS_DIR / model_filename
        metadata_path = MLB_MODELS_DIR / metadata_filename

        # Save model
        joblib.dump(self.pipeline, model_path)
        self.logger.info(f"Model saved to: {model_path}")

        # Save metadata — coerce numpy scalar types to Python float for JSON compatibility
        # (XGBoost feature_importances_ returns float32; json.dump rejects non-native types)
        safe_importances = (
            {k: float(v) for k, v in self.feature_importances.items()}
            if self.feature_importances else None
        )
        metadata = {
            'model_type': self.model_type,
            'version': version,
            'trained_date': datetime.now().isoformat(),
            'features': MLB_REQUIRED_FEATURES,
            'metrics': self.metrics,
            'feature_importances': safe_importances,
            'model_filename': model_filename,
            'sklearn_version': __import__('sklearn').__version__
        }

        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        self.logger.info(f"Metadata saved to: {metadata_path}")

        return model_path, metadata_path


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Train MLB game prediction models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python train_mlb_model.py                                                        # Train default RandomForest
    python train_mlb_model.py --model-type logistic_regression                       # Train Logistic Regression
    python train_mlb_model.py --model-type xgboost --version 3.0-xgb               # Train XGBoost (defaults)
    python train_mlb_model.py --model-type xgboost --hyperparameter-search          # Search + train best XGBoost
    python train_mlb_model.py --model-type xgboost --hyperparameter-search --search-iter 100  # Wider search
    python train_mlb_model.py --verbose --test-split 0.25                           # Verbose with 25% test split
    python train_mlb_model.py --diagnostics                                         # Full diagnostic output
    python train_mlb_model.py --temporal-weighting --half-life 365                  # Exponential decay weights
        """
    )

    parser.add_argument(
        '--model-type',
        choices=['random_forest', 'logistic_regression', 'xgboost'],
        default='random_forest',
        help='Type of model to train (default: random_forest)'
    )

    parser.add_argument(
        '--start-date',
        type=str,
        help='Start date for training data (YYYY-MM-DD format, default: 90 days ago)'
    )

    parser.add_argument(
        '--end-date',
        type=str,
        help='End date for training data (YYYY-MM-DD format, default: today)'
    )

    parser.add_argument(
        '--test-split',
        type=float,
        default=0.2,
        help='Fraction of data to use for testing (default: 0.2)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging output'
    )

    parser.add_argument(
        '--version',
        type=str,
        default='1.0',
        help='Version string for the saved model (default: 1.0)'
    )

    parser.add_argument(
        '--diagnostics',
        action='store_true',
        help='Print per-month accuracy breakdown, learning curve, class balance, and full feature importances'
    )

    parser.add_argument(
        '--temporal-weighting',
        action='store_true',
        help='Apply exponential decay sample weights so recent games influence training more'
    )

    parser.add_argument(
        '--half-life',
        type=int,
        default=365,
        help='Half-life in days for temporal weighting decay (default: 365)'
    )

    parser.add_argument(
        '--hyperparameter-search',
        action='store_true',
        help='Run RandomizedSearchCV over XGBoost hyperparameters (requires --model-type xgboost)'
    )

    parser.add_argument(
        '--search-iter',
        type=int,
        default=50,
        help='Number of parameter settings sampled in hyperparameter search (default: 50)'
    )

    args = parser.parse_args()

    # Parse dates
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d') if args.end_date else datetime.now()
    start_date = datetime.strptime(args.start_date, '%Y-%m-%d') if args.start_date else (end_date - timedelta(days=90))

    try:
        # Initialize trainer
        trainer = MLBModelTrainer(model_type=args.model_type, verbose=args.verbose)

        # Fetch data
        schedule_df, teams_df, offensive_df, defensive_df = trainer.fetch_data_from_database()

        # Prepare training data
        training_data = trainer.prepare_training_data(
            schedule_df, teams_df, offensive_df, defensive_df,
            start_date, end_date
        )

        if len(training_data) < 100:
            print(f"\n❌ Insufficient training data ({len(training_data)} games)")
            print("   Need at least 100 completed games to train a model.")
            print("   Run the data update script first: python machine_learning/scripts/update_mlb_data.py")
            sys.exit(1)

        # Hyperparameter search (XGBoost only)
        if args.hyperparameter_search:
            if args.model_type != 'xgboost':
                print(f"\n❌ --hyperparameter-search requires --model-type xgboost (got '{args.model_type}')")
                sys.exit(1)
            search_result = trainer._run_hyperparameter_search(
                training_data,
                test_split=args.test_split,
                n_iter=args.search_iter,
            )
            print(f"\n{'='*55}")
            print("HYPERPARAMETER SEARCH RESULTS")
            print(f"{'='*55}")
            print(f"  Best CV accuracy:              {search_result['best_cv_score']:.4f}")
            print(f"  Sprint 5 baseline (defaults):  0.5146")
            print(f"  Best params (JSON):")
            print(json.dumps(search_result['params'], indent=4))
            print(f"{'='*55}")
            print(f"\nContinuing to train final model with best params...")

        # Compute temporal sample weights if requested
        sample_weights = None
        if args.temporal_weighting:
            if 'game_date' not in training_data.columns:
                print("\nERROR: game_date column not available for temporal weighting")
                sys.exit(1)
            null_count = training_data['game_date'].isna().sum()
            if null_count > 0:
                print(f"\nERROR: game_date has {null_count} null values — cannot compute temporal weights")
                sys.exit(1)
            sample_weights = trainer._compute_sample_weights(training_data['game_date'], args.half_life)
            print(f"   Temporal weighting enabled (half-life: {args.half_life} days)")

        # Train and evaluate
        trainer.train_and_evaluate(
            training_data,
            test_split=args.test_split,
            diagnostics=args.diagnostics,
            sample_weights=sample_weights
        )

        # Save model
        model_path, metadata_path = trainer.save_model(version=args.version)

        print(f"\n✅ Model training completed successfully!")
        print(f"   Model: {model_path}")
        print(f"   Metadata: {metadata_path}")
        print(f"   Accuracy: {trainer.metrics['accuracy']:.4f}")
        print(f"\nTo use this model in the API, update api/src/ml_config.py:")
        print(f"   model_file: mlb_predictor_v{args.version}.joblib")
        print(f"   metadata_file: mlb_predictor_v{args.version}_metadata.json")

    except KeyboardInterrupt:
        print("\n❌ Training cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
