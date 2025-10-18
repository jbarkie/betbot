"""
Tests for the ML Model Service.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from api.src.ml_model_service import MLModelService, get_mlb_model_service
from api.src.ml_config import MLB_REQUIRED_FEATURES


class TestMLModelService:
    """Test cases for the MLModelService class."""

    @pytest.fixture
    def temp_model_dir(self):
        """Create a temporary directory for test models."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def mock_model_config(self, temp_model_dir):
        """Create a mock model configuration."""
        return {
            'model_name': 'test_predictor',
            'version': '1.0',
            'model_file': 'test_predictor_v1.0.joblib',
            'metadata_file': 'test_predictor_v1.0_metadata.json',
            'model_type': 'RandomForestClassifier',
            'model_dir': temp_model_dir
        }

    @pytest.fixture
    def sample_trained_model(self):
        """Create a simple trained model for testing."""
        # Create a simple pipeline with RandomForest
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('model', model)
        ])

        # Train on dummy data
        X = np.random.rand(100, len(MLB_REQUIRED_FEATURES))
        y = np.random.randint(0, 2, 100)
        pipeline.fit(X, y)

        return pipeline

    @pytest.fixture
    def sample_metadata(self):
        """Create sample model metadata."""
        return {
            'model_type': 'RandomForestClassifier',
            'version': '1.0',
            'trained_date': '2025-01-15T10:30:00',
            'features': MLB_REQUIRED_FEATURES,
            'metrics': {
                'accuracy': 0.578,
                'precision': 0.562,
                'recall': 0.589,
                'f1': 0.575,
                'roc_auc': 0.612
            },
            'sklearn_version': '1.3.0'
        }

    @pytest.fixture
    def ml_service_with_model(self, temp_model_dir, mock_model_config, sample_trained_model, sample_metadata):
        """Create an ML service with a pre-loaded model."""
        # Save model and metadata to temp directory
        model_path = temp_model_dir / mock_model_config['model_file']
        metadata_path = temp_model_dir / mock_model_config['metadata_file']

        joblib.dump(sample_trained_model, model_path)
        with open(metadata_path, 'w') as f:
            json.dump(sample_metadata, f)

        # Patch get_model_path and get_metadata_path
        with patch('api.src.ml_model_service.get_model_path', return_value=model_path):
            with patch('api.src.ml_model_service.get_metadata_path', return_value=metadata_path):
                with patch('api.src.ml_model_service.model_exists', return_value=True):
                    service = MLModelService(model_config=mock_model_config)
                    yield service

    def test_initialization(self, mock_model_config):
        """Test ML service initialization."""
        service = MLModelService(model_config=mock_model_config)

        assert service.model_config == mock_model_config
        assert service._model is None
        assert service._metadata is None
        assert service._is_loaded is False
        assert service._load_error is None

    def test_is_available_no_model(self, mock_model_config):
        """Test is_available when model doesn't exist."""
        with patch('api.src.ml_model_service.model_exists', return_value=False):
            service = MLModelService(model_config=mock_model_config)
            assert service.is_available is False

    def test_is_available_with_model(self, mock_model_config):
        """Test is_available when model exists."""
        with patch('api.src.ml_model_service.model_exists', return_value=True):
            service = MLModelService(model_config=mock_model_config)
            assert service.is_available is True

    def test_load_model_success(self, temp_model_dir, mock_model_config, sample_trained_model, sample_metadata):
        """Test successful model loading."""
        # Save model and metadata
        model_path = temp_model_dir / mock_model_config['model_file']
        metadata_path = temp_model_dir / mock_model_config['metadata_file']

        joblib.dump(sample_trained_model, model_path)
        with open(metadata_path, 'w') as f:
            json.dump(sample_metadata, f)

        # Create service and load model
        with patch('api.src.ml_model_service.get_model_path', return_value=model_path):
            with patch('api.src.ml_model_service.get_metadata_path', return_value=metadata_path):
                service = MLModelService(model_config=mock_model_config)
                result = service._load_model()

        assert result is True
        assert service.is_loaded is True
        assert service._model is not None
        assert service._metadata == sample_metadata
        assert service._load_error is None

    def test_load_model_file_not_found(self, temp_model_dir, mock_model_config):
        """Test model loading when file doesn't exist."""
        model_path = temp_model_dir / 'nonexistent_model.joblib'

        with patch('api.src.ml_model_service.get_model_path', return_value=model_path):
            service = MLModelService(model_config=mock_model_config)
            result = service._load_model()

        assert result is False
        assert service.is_loaded is False
        assert service._model is None
        assert 'not found' in service._load_error.lower()

    def test_load_model_without_metadata(self, temp_model_dir, mock_model_config, sample_trained_model):
        """Test model loading when metadata file is missing."""
        # Save only the model
        model_path = temp_model_dir / mock_model_config['model_file']
        metadata_path = temp_model_dir / 'nonexistent_metadata.json'

        joblib.dump(sample_trained_model, model_path)

        with patch('api.src.ml_model_service.get_model_path', return_value=model_path):
            with patch('api.src.ml_model_service.get_metadata_path', return_value=metadata_path):
                service = MLModelService(model_config=mock_model_config)
                result = service._load_model()

        assert result is True
        assert service.is_loaded is True
        assert service._metadata is not None
        assert service._metadata['model_type'] == 'RandomForestClassifier'
        assert service._metadata['version'] == '1.0'

    def test_predict_success(self, ml_service_with_model):
        """Test successful prediction."""
        # Create valid feature dictionary
        features = {feature: 0.5 for feature in MLB_REQUIRED_FEATURES}

        result = ml_service_with_model.predict(features)

        assert result is not None
        predicted_winner, win_probability, metadata = result

        assert predicted_winner in ['home', 'away']
        assert 0 <= win_probability <= 1
        assert 'ml_model_name' in metadata
        assert 'model_confidence' in metadata
        assert 'home_win_probability' in metadata
        assert 'away_win_probability' in metadata
        assert metadata['confidence_margin'] >= 0

    def test_predict_missing_features(self, ml_service_with_model):
        """Test prediction with missing required features."""
        # Create incomplete feature dictionary
        features = {'home_rolling_win_pct': 0.6}  # Missing most features

        result = ml_service_with_model.predict(features)

        assert result is None  # Should fail due to missing features

    def test_predict_handles_nan_values(self, ml_service_with_model):
        """Test prediction handles NaN values gracefully."""
        # Create features with NaN values
        features = {feature: 0.5 for feature in MLB_REQUIRED_FEATURES}
        features['home_rolling_win_pct'] = float('nan')

        result = ml_service_with_model.predict(features)

        # Should handle NaN by filling with 0
        assert result is not None

    def test_predict_confidence_levels(self, ml_service_with_model):
        """Test confidence level categorization."""
        features = {feature: 0.5 for feature in MLB_REQUIRED_FEATURES}

        result = ml_service_with_model.predict(features)

        assert result is not None
        _, _, metadata = result

        assert metadata['model_confidence'] in ['High', 'Medium', 'Low']

    def test_predict_feature_importance(self, ml_service_with_model):
        """Test feature importance is included in metadata."""
        features = {feature: 0.5 for feature in MLB_REQUIRED_FEATURES}

        result = ml_service_with_model.predict(features)

        assert result is not None
        _, _, metadata = result

        # RandomForest should have feature importance
        if metadata['feature_importance']:
            assert isinstance(metadata['feature_importance'], dict)
            assert len(metadata['feature_importance']) <= 5  # Top 5 features

    def test_predict_without_loaded_model(self, mock_model_config):
        """Test prediction when model isn't loaded."""
        with patch('api.src.ml_model_service.model_exists', return_value=False):
            service = MLModelService(model_config=mock_model_config)
            features = {feature: 0.5 for feature in MLB_REQUIRED_FEATURES}

            result = service.predict(features)

            assert result is None

    def test_get_model_info_with_loaded_model(self, ml_service_with_model):
        """Test get_model_info with a loaded model."""
        # Force load the model
        ml_service_with_model._load_model()

        info = ml_service_with_model.get_model_info()

        assert info['ml_model_type'] == 'RandomForestClassifier'
        assert info['version'] == '1.0'
        assert info['is_loaded'] is True
        assert info['is_available'] is True
        assert 'metrics' in info
        assert info['features_count'] == len(MLB_REQUIRED_FEATURES)

    def test_get_model_info_without_model(self, mock_model_config):
        """Test get_model_info when no model exists."""
        with patch('api.src.ml_model_service.model_exists', return_value=False):
            service = MLModelService(model_config=mock_model_config)

            info = service.get_model_info()

            assert info['ml_model_name'] == 'none'
            assert info['is_loaded'] is False
            assert info['is_available'] is False
            assert 'error' in info

    def test_reload_model(self, temp_model_dir, mock_model_config, sample_trained_model, sample_metadata):
        """Test model reloading."""
        # Save model
        model_path = temp_model_dir / mock_model_config['model_file']
        metadata_path = temp_model_dir / mock_model_config['metadata_file']

        joblib.dump(sample_trained_model, model_path)
        with open(metadata_path, 'w') as f:
            json.dump(sample_metadata, f)

        with patch('api.src.ml_model_service.get_model_path', return_value=model_path):
            with patch('api.src.ml_model_service.get_metadata_path', return_value=metadata_path):
                service = MLModelService(model_config=mock_model_config)

                # Load initially
                service._load_model()
                assert service.is_loaded is True

                # Reload
                result = service.reload_model()

                assert result is True
                assert service.is_loaded is True

    def test_singleton_pattern(self):
        """Test that get_mlb_model_service returns singleton instance."""
        service1 = get_mlb_model_service()
        service2 = get_mlb_model_service()

        assert service1 is service2  # Same instance

    def test_lazy_loading(self, ml_service_with_model):
        """Test that model is lazy-loaded on first prediction."""
        # Service should not be loaded initially
        service = MLModelService(model_config=ml_service_with_model.model_config)
        assert service.is_loaded is False

        # First prediction should trigger load
        with patch.object(service, '_load_model', wraps=service._load_model) as mock_load:
            features = {feature: 0.5 for feature in MLB_REQUIRED_FEATURES}
            service.predict(features)

            mock_load.assert_called_once()


class TestMLModelServiceIntegration:
    """Integration tests for ML Model Service with real sklearn models."""

    def test_end_to_end_prediction_flow(self, tmp_path):
        """Test complete prediction flow from model creation to prediction."""
        # Create and train a simple model
        X_train = np.random.rand(100, len(MLB_REQUIRED_FEATURES))
        y_train = np.random.randint(0, 2, 100)

        model = RandomForestClassifier(n_estimators=10, random_state=42)
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('model', model)
        ])
        pipeline.fit(X_train, y_train)

        # Save model
        model_path = tmp_path / 'test_model.joblib'
        metadata_path = tmp_path / 'test_metadata.json'

        joblib.dump(pipeline, model_path)

        metadata = {
            'model_type': 'RandomForestClassifier',
            'version': '1.0',
            'trained_date': '2025-01-15T10:30:00',
            'features': MLB_REQUIRED_FEATURES,
            'metrics': {'accuracy': 0.6}
        }

        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)

        # Create service and make prediction
        config = {
            'model_name': 'test',
            'version': '1.0',
            'model_file': 'test_model.joblib',
            'metadata_file': 'test_metadata.json',
            'model_type': 'RandomForestClassifier'
        }

        with patch('api.src.ml_model_service.get_model_path', return_value=model_path):
            with patch('api.src.ml_model_service.get_metadata_path', return_value=metadata_path):
                with patch('api.src.ml_model_service.model_exists', return_value=True):
                    service = MLModelService(model_config=config)

                    # Make prediction
                    features = {feature: np.random.rand() for feature in MLB_REQUIRED_FEATURES}
                    result = service.predict(features)

                    assert result is not None
                    winner, probability, meta = result

                    assert winner in ['home', 'away']
                    assert 0 <= probability <= 1
                    assert meta['ml_model_name'] is not None
                    assert 0 <= meta['home_win_probability'] <= 1
                    assert 0 <= meta['away_win_probability'] <= 1
                    # Probabilities should sum to 1
                    assert abs(meta['home_win_probability'] + meta['away_win_probability'] - 1.0) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
