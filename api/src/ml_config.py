"""
ML Model Configuration

This module defines paths, settings, and metadata for machine learning models
used in the BetBot API.
"""
import os
from pathlib import Path
from typing import Dict, Optional

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Model storage paths
MLB_MODELS_DIR = PROJECT_ROOT / "machine_learning" / "models" / "mlb"

# Current production model configurations
MLB_MODEL_CONFIG = {
    "model_name": "mlb_predictor",
    "version": "3.3",
    "model_file": "mlb_predictor_v3.3.joblib",
    "metadata_file": "mlb_predictor_v3.3_metadata.json",
    "model_type": "RandomForestClassifier",  # also supported: "LogisticRegression", "XGBoostClassifier"
}

# Model feature configuration.
#
# MLB_BASE_FEATURES are the 26 team-level features present since v2.0.
# MLB_PITCHER_FEATURES are the 6 starting pitcher features added in v3.3.
# MLB_REQUIRED_FEATURES is the serving contract: the exact column set, in order,
# that the current production model was fit on. Keep the two halves separate so a
# model can still be trained without pitcher features for comparison.
MLB_BASE_FEATURES = [
    'home_rolling_win_pct',
    'away_rolling_win_pct',
    'home_rolling_runs_scored',
    'away_rolling_runs_scored',
    'home_rolling_runs_allowed',
    'away_rolling_runs_allowed',
    'home_days_rest',
    'away_days_rest',
    'home_batting_avg',
    'away_batting_avg',
    'home_obp',
    'away_obp',
    'home_slg',
    'away_slg',
    'home_era',
    'away_era',
    'home_whip',
    'away_whip',
    'home_strikeouts',
    'away_strikeouts',
    'h2h_home_win_pct',
    'h2h_away_win_pct',
    'h2h_games_played',
    'month',
    'day_of_week',
    'is_weekend'
]

MLB_PITCHER_FEATURES = [
    'home_starter_era',
    'home_starter_whip',
    'home_starter_k9',
    'away_starter_era',
    'away_starter_whip',
    'away_starter_k9'
]

MLB_REQUIRED_FEATURES = MLB_BASE_FEATURES + MLB_PITCHER_FEATURES

# Model performance thresholds
MIN_CONFIDENCE_THRESHOLD = 0.55  # Minimum confidence to use ML prediction
FALLBACK_TO_RULES_THRESHOLD = 0.52  # If confidence below this, use rule-based system


def get_model_path(model_config: Optional[Dict] = None) -> Path:
    """
    Get the full path to the current production model file.

    Args:
        model_config: Optional model configuration dict. Uses MLB_MODEL_CONFIG if not provided.

    Returns:
        Path to the model file
    """
    if model_config is None:
        model_config = MLB_MODEL_CONFIG

    return MLB_MODELS_DIR / model_config["model_file"]


def get_metadata_path(model_config: Optional[Dict] = None) -> Path:
    """
    Get the full path to the model metadata file.

    Args:
        model_config: Optional model configuration dict. Uses MLB_MODEL_CONFIG if not provided.

    Returns:
        Path to the metadata file
    """
    if model_config is None:
        model_config = MLB_MODEL_CONFIG

    return MLB_MODELS_DIR / model_config["metadata_file"]


def model_exists(model_config: Optional[Dict] = None) -> bool:
    """
    Check if the configured model file exists.

    Args:
        model_config: Optional model configuration dict. Uses MLB_MODEL_CONFIG if not provided.

    Returns:
        True if model file exists, False otherwise
    """
    model_path = get_model_path(model_config)
    return model_path.exists()


def get_model_version_string(model_config: Optional[Dict] = None) -> str:
    """
    Get a formatted version string for the model.

    Args:
        model_config: Optional model configuration dict. Uses MLB_MODEL_CONFIG if not provided.

    Returns:
        Formatted version string (e.g., "RandomForest-v1.0")
    """
    if model_config is None:
        model_config = MLB_MODEL_CONFIG

    return f"{model_config['model_type']}-v{model_config['version']}"
