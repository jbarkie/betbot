#!/usr/bin/env python3
"""
MLB Model Training Script

This script trains machine learning models to predict MLB game outcomes using
historical data, team statistics, and engineered features.

Usage:
    python train_mlb_model.py [--model-type MODEL] [--start-date DATE] [--end-date DATE] [--verbose]

Options:
    --model-type    Type of model to train: random_forest, logistic_regression, xgboost, ensemble (default: random_forest)
    --start-date    Start date for training data (YYYY-MM-DD format, default: season start)
    --end-date      End date for training data (YYYY-MM-DD format, default: today)
    --verbose       Enable verbose logging output
    --test-split    Fraction of data to use for testing (default: 0.2)
"""

import sys
import argparse
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
import warnings

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import required modules
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
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
            model_type: Type of model to train (random_forest, logistic_regression, xgboost, ensemble)
            verbose: Enable verbose logging
        """
        self.model_type = model_type
        self.verbose = verbose
        self.model = None
        self.pipeline = None
        self.feature_importances = {}
        self.metrics = {}

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
            DataFrame with engineered features ready for training
        """
        self.logger.info(f"Preparing training data from {start_date.date()} to {end_date.date()}...")

        pipeline = MLBDataPipeline(rolling_window=10, head_to_head_window=5)

        training_data = pipeline.prepare_training_data(
            schedule_df=schedule_df,
            teams_df=teams_df,
            offensive_stats_df=offensive_df,
            defensive_stats_df=defensive_df,
            start_date=start_date,
            end_date=end_date,
            features_to_exclude=['game_id', 'game_date', 'home_team_id', 'away_team_id', 'run_differential']
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
                n_jobs=-1
            )
        elif self.model_type == 'logistic_regression':
            model = LogisticRegression(
                max_iter=10000,
                random_state=42,
                n_jobs=-1
            )
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")

        # Create pipeline
        pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('model', model)
        ])

        return pipeline

    def train_and_evaluate(self, training_data: pd.DataFrame, test_split: float = 0.2):
        """
        Train and evaluate the model using time series cross-validation.

        Args:
            training_data: Prepared training data
            test_split: Fraction of data to use for final testing
        """
        self.logger.info("Starting model training and evaluation...")

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

        # Create and train model
        self.pipeline = self.create_model()

        # Perform time series cross-validation on training data
        self.logger.info("Performing time series cross-validation...")
        tscv = TimeSeriesSplit(n_splits=5)
        cv_scores = cross_val_score(
            self.pipeline, X_train, y_train,
            cv=tscv, scoring='accuracy', n_jobs=-1
        )

        self.logger.info(f"Cross-validation scores: {cv_scores}")
        self.logger.info(f"Mean CV accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")

        # Train on full training set
        self.logger.info("Training final model on full training set...")
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
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'train_size': len(X_train),
            'test_size': len(X_test)
        }

        self.logger.info("\nModel Performance:")
        self.logger.info(f"  Accuracy:  {self.metrics['accuracy']:.4f}")
        self.logger.info(f"  Precision: {self.metrics['precision']:.4f}")
        self.logger.info(f"  Recall:    {self.metrics['recall']:.4f}")
        self.logger.info(f"  F1 Score:  {self.metrics['f1']:.4f}")
        self.logger.info(f"  ROC AUC:   {self.metrics['roc_auc']:.4f}")

        # Get feature importances (for tree-based models)
        if self.model_type == 'random_forest':
            importances = self.pipeline.named_steps['model'].feature_importances_
            self.feature_importances = dict(zip(MLB_REQUIRED_FEATURES, importances))

            # Sort and display top features
            sorted_features = sorted(self.feature_importances.items(), key=lambda x: x[1], reverse=True)
            self.logger.info("\nTop 10 Most Important Features:")
            for feature, importance in sorted_features[:10]:
                self.logger.info(f"  {feature}: {importance:.4f}")

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

        # Save metadata
        metadata = {
            'model_type': self.model_type,
            'version': version,
            'trained_date': datetime.now().isoformat(),
            'features': MLB_REQUIRED_FEATURES,
            'metrics': self.metrics,
            'feature_importances': self.feature_importances if self.feature_importances else None,
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
    python train_mlb_model.py                                    # Train default RandomForest model
    python train_mlb_model.py --model-type logistic_regression   # Train Logistic Regression
    python train_mlb_model.py --verbose --test-split 0.25        # Verbose with 25% test split
    python train_mlb_model.py --start-date 2025-04-01            # Specify training start date
        """
    )

    parser.add_argument(
        '--model-type',
        choices=['random_forest', 'logistic_regression'],
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

        # Train and evaluate
        trainer.train_and_evaluate(training_data, test_split=args.test_split)

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
