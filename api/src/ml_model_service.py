"""
ML Model Service

This module provides a service for loading, caching, and serving predictions
from trained machine learning models.
"""
import json
import logging
from typing import Dict, Optional, Tuple
import joblib

from api.src.ml_config import (
    get_model_path,
    get_metadata_path,
    model_exists,
    get_model_version_string,
    MLB_MODEL_CONFIG,
    MLB_REQUIRED_FEATURES,
    MIN_CONFIDENCE_THRESHOLD
)

logger = logging.getLogger(__name__)


class MLModelService:
    """
    Service for loading and serving ML model predictions.

    This class handles:
    - Lazy loading of models (loaded on first use)
    - Model caching (kept in memory after first load)
    - Graceful fallback when models are unavailable
    - Metadata management
    """

    def __init__(self, model_config: Optional[Dict] = None):
        """
        Initialize the ML model service.

        Args:
            model_config: Optional model configuration dict. Uses MLB_MODEL_CONFIG if not provided.
        """
        self.model_config = model_config or MLB_MODEL_CONFIG
        self._model = None
        self._metadata = None
        self._is_loaded = False
        self._load_error = None

    @property
    def is_available(self) -> bool:
        """
        Check if a trained model is available.

        Returns:
            True if model file exists, False otherwise
        """
        return model_exists(self.model_config)

    @property
    def is_loaded(self) -> bool:
        """
        Check if the model is currently loaded in memory.

        Returns:
            True if model is loaded, False otherwise
        """
        return self._is_loaded

    def _load_model(self) -> bool:
        """
        Load the model and metadata from disk.

        Returns:
            True if loading successful, False otherwise
        """
        if self._is_loaded:
            return True

        try:
            model_path = get_model_path(self.model_config)
            metadata_path = get_metadata_path(self.model_config)

            if not model_path.exists():
                self._load_error = f"Model file not found: {model_path}"
                logger.warning(self._load_error)
                return False

            # Load model
            logger.info(f"Loading ML model from: {model_path}")
            self._model = joblib.load(model_path)

            # Load metadata if available
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    self._metadata = json.load(f)
                logger.info(f"Loaded model metadata: {self._metadata.get('model_type')} v{self._metadata.get('version')}")
            else:
                logger.warning(f"Metadata file not found: {metadata_path}")
                self._metadata = {
                    'model_type': self.model_config['model_type'],
                    'version': self.model_config['version'],
                    'trained_date': 'unknown'
                }

            self._is_loaded = True
            self._load_error = None
            logger.info("Model loaded successfully")
            return True

        except Exception as e:
            self._load_error = f"Failed to load model: {str(e)}"
            logger.error(self._load_error, exc_info=True)
            return False

    def predict(self, features: Dict[str, float]) -> Optional[Tuple[str, float, Dict]]:
        """
        Make a prediction using the loaded model.

        Args:
            features: Dictionary of feature names to values

        Returns:
            Tuple of (predicted_winner, win_probability, metadata) or None if prediction fails
            - predicted_winner: 'home' or 'away'
            - win_probability: float between 0 and 1
            - metadata: dict with additional info (confidence, model_name, feature_importance, etc.)
        """
        # Try to load model if not already loaded
        if not self._is_loaded:
            if not self._load_model():
                logger.warning("Cannot make prediction: model not loaded")
                return None

        try:
            # Validate features
            missing_features = set(MLB_REQUIRED_FEATURES) - set(features.keys())
            if missing_features:
                logger.warning(f"Missing required features: {missing_features}")
                return None

            # Prepare feature vector in correct order
            import pandas as pd
            feature_vector = pd.DataFrame([features])[MLB_REQUIRED_FEATURES]

            # Handle any NaN values
            feature_vector = feature_vector.fillna(0)

            # Make prediction
            prediction_proba = self._model.predict_proba(feature_vector)[0]
            prediction = self._model.predict(feature_vector)[0]

            # Extract probabilities
            away_win_prob = prediction_proba[0]  # Class 0 = away team wins
            home_win_prob = prediction_proba[1]  # Class 1 = home team wins

            # Determine winner and probability
            if prediction == 1:  # Home team wins
                predicted_winner = 'home'
                win_probability = home_win_prob
            else:  # Away team wins
                predicted_winner = 'away'
                win_probability = away_win_prob

            # Determine confidence level
            confidence_margin = abs(home_win_prob - away_win_prob)
            if confidence_margin > 0.3:
                confidence_level = "High"
            elif confidence_margin > 0.15:
                confidence_level = "Medium"
            else:
                confidence_level = "Low"

            # Get feature importances if available
            feature_importance = None
            if hasattr(self._model.named_steps['model'], 'feature_importances_'):
                importances = self._model.named_steps['model'].feature_importances_
                # Get top 5 most important features for this prediction
                importance_dict = dict(zip(MLB_REQUIRED_FEATURES, importances))
                sorted_features = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)[:5]
                feature_importance = dict(sorted_features)

            # Prepare metadata
            metadata = {
                'ml_model_name': get_model_version_string(self.model_config),
                'model_confidence': confidence_level,
                'home_win_probability': round(home_win_prob, 3),
                'away_win_probability': round(away_win_prob, 3),
                'confidence_margin': round(confidence_margin, 3),
                'feature_importance': feature_importance,
                'use_ml_prediction': win_probability >= MIN_CONFIDENCE_THRESHOLD
            }

            return predicted_winner, round(win_probability, 3), metadata

        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}", exc_info=True)
            return None

    def get_model_info(self) -> Dict:
        """
        Get information about the current model.

        Returns:
            Dictionary containing model metadata
        """
        if not self._is_loaded:
            self._load_model()

        if self._metadata:
            return {
                'ml_model_name': get_model_version_string(self.model_config),
                'ml_model_type': self._metadata.get('model_type', 'unknown'),
                'version': self._metadata.get('version', 'unknown'),
                'trained_date': self._metadata.get('trained_date', 'unknown'),
                'metrics': self._metadata.get('metrics', {}),
                'features_count': len(self._metadata.get('features', [])),
                'is_loaded': self._is_loaded,
                'is_available': self.is_available
            }
        else:
            return {
                'ml_model_name': 'none',
                'ml_model_type': 'unknown',
                'version': 'unknown',
                'trained_date': 'unknown',
                'is_loaded': False,
                'is_available': False,
                'error': self._load_error or 'Model not configured'
            }

    def reload_model(self) -> bool:
        """
        Force reload the model from disk.

        Useful for updating to a new model version without restarting the service.

        Returns:
            True if reload successful, False otherwise
        """
        logger.info("Forcing model reload...")
        self._model = None
        self._metadata = None
        self._is_loaded = False
        self._load_error = None

        return self._load_model()


# Global singleton instance for the MLB model service
_mlb_model_service: Optional[MLModelService] = None


def get_mlb_model_service() -> MLModelService:
    """
    Get the global MLB model service instance.

    This function implements a singleton pattern to ensure only one instance
    of the model service exists, which keeps the model cached in memory.

    Returns:
        MLModelService instance
    """
    global _mlb_model_service

    if _mlb_model_service is None:
        _mlb_model_service = MLModelService()
        logger.info("Initialized MLB model service")

    return _mlb_model_service
