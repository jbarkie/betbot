from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import pytest

from api.src.login import get_current_user
from api.src.main import app


@pytest.fixture
def client():
    """
    Create a test client for the FastAPI app with dependency overrides.
    """
    mock_user = MagicMock()
    mock_user.username = "testuser"

    async def override_get_current_user():
        return mock_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    
    client = TestClient(app)

    yield client

    # Cleanup
    app.dependency_overrides.clear()

def test_get_mlb_game_analytics(client):
    """
    Test the /analytics/mlb/game?id={game_id} endpoint.
    """
    game_id = "12345"
    
    # Create mock analytics response
    from api.src.models.mlb_analytics import MlbAnalyticsResponse, TeamAnalytics
    
    mock_response = MlbAnalyticsResponse(
        id=game_id,
        home_team="Red Sox",
        away_team="Yankees",
        predicted_winner="Red Sox",
        win_probability=0.65,
        home_analytics=TeamAnalytics(
            name="Red Sox",
            winning_percentage=0.6,
            rolling_win_percentage=0.7,
            offensive_rating=0.75,
            defensive_rating=0.68,
            days_rest=2,
            momentum_score=0.71
        ),
        away_analytics=TeamAnalytics(
            name="Yankees",
            winning_percentage=0.5,
            rolling_win_percentage=0.4,
            offensive_rating=0.65,
            defensive_rating=0.72,
            days_rest=1,
            momentum_score=0.59
        ),
        key_factors={
            "season_record": "Red Sox has better season record",
            "momentum": "Red Sox has better recent form"
        },
        confidence_level="High"
    )

    # Mock the enhanced analytics service
    with patch("api.src.mlb_analytics.get_enhanced_mlb_game_analytics") as mock_analytics:
        mock_analytics.return_value = mock_response

        response = client.get(f"/analytics/mlb/game?id={game_id}")
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["id"] == game_id
        assert response_data["home_team"] == "Red Sox"
        assert response_data["away_team"] == "Yankees"
        assert response_data["predicted_winner"] == "Red Sox"
        assert response_data["win_probability"] == 0.65
        assert response_data["confidence_level"] == "High"
        assert "home_analytics" in response_data
        assert "away_analytics" in response_data
        assert "key_factors" in response_data
        
        # Verify the enhanced analytics service was called with the correct game_id
        mock_analytics.assert_called_once_with(game_id)


def test_get_mlb_model_info_with_loaded_model(client):
    """
    Test the /analytics/mlb/model-info endpoint with a loaded model.
    """
    from api.src.models.mlb_analytics import ModelInfoResponse

    mock_model_info = ModelInfoResponse(
        ml_model_name="RandomForest-v1.0",
        ml_model_type="RandomForestClassifier",
        version="1.0",
        trained_date="2025-01-15T10:30:00",
        is_loaded=True,
        is_available=True,
        metrics={
            "accuracy": 0.578,
            "precision": 0.562,
            "recall": 0.589,
            "f1": 0.575,
            "roc_auc": 0.612
        },
        features_count=26
    )

    # Mock the ML model service
    with patch("api.src.main.get_mlb_model_service") as mock_service:
        mock_service_instance = MagicMock()
        mock_service_instance.get_model_info.return_value = {
            "ml_model_name": "RandomForest-v1.0",
            "ml_model_type": "RandomForestClassifier",
            "version": "1.0",
            "trained_date": "2025-01-15T10:30:00",
            "is_loaded": True,
            "is_available": True,
            "metrics": {
                "accuracy": 0.578,
                "precision": 0.562,
                "recall": 0.589,
                "f1": 0.575,
                "roc_auc": 0.612
            },
            "features_count": 26
        }
        mock_service.return_value = mock_service_instance

        response = client.get("/analytics/mlb/model-info")
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["ml_model_name"] == "RandomForest-v1.0"
        assert response_data["ml_model_type"] == "RandomForestClassifier"
        assert response_data["version"] == "1.0"
        assert response_data["is_loaded"] is True
        assert response_data["is_available"] is True
        assert "metrics" in response_data
        assert response_data["metrics"]["accuracy"] == 0.578
        assert response_data["features_count"] == 26

        # Verify the service was called
        mock_service.assert_called_once()
        mock_service_instance.get_model_info.assert_called_once()


def test_get_mlb_model_info_without_model(client):
    """
    Test the /analytics/mlb/model-info endpoint when no model is available.
    """
    from api.src.models.mlb_analytics import ModelInfoResponse

    # Mock the ML model service
    with patch("api.src.main.get_mlb_model_service") as mock_service:
        mock_service_instance = MagicMock()
        mock_service_instance.get_model_info.return_value = {
            "ml_model_name": "none",
            "ml_model_type": "unknown",
            "version": "unknown",
            "trained_date": "unknown",
            "is_loaded": False,
            "is_available": False,
            "error": "Model not configured"
        }
        mock_service.return_value = mock_service_instance

        response = client.get("/analytics/mlb/model-info")
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["ml_model_name"] == "none"
        assert response_data["is_loaded"] is False
        assert response_data["is_available"] is False
        assert "error" in response_data


def test_mlb_game_analytics_with_ml_prediction(client):
    """
    Test that the MLB analytics endpoint includes ML prediction fields.
    """
    game_id = "ml_game_123"

    from api.src.models.mlb_analytics import MlbAnalyticsResponse, TeamAnalytics

    mock_response = MlbAnalyticsResponse(
        id=game_id,
        home_team="Dodgers",
        away_team="Giants",
        predicted_winner="Dodgers",
        win_probability=0.68,
        home_analytics=TeamAnalytics(
            name="Dodgers",
            winning_percentage=0.65,
            rolling_win_percentage=0.70,
            offensive_rating=0.78,
            defensive_rating=0.72,
            days_rest=2,
            momentum_score=0.75
        ),
        away_analytics=TeamAnalytics(
            name="Giants",
            winning_percentage=0.55,
            rolling_win_percentage=0.50,
            offensive_rating=0.68,
            defensive_rating=0.70,
            days_rest=1,
            momentum_score=0.63
        ),
        key_factors={
            "season_record": "Dodgers has better season record",
            "momentum": "Dodgers has better recent form"
        },
        confidence_level="High",
        # ML-specific fields
        ml_model_name="RandomForest-v1.0",
        ml_confidence="High",
        home_win_probability=0.68,
        away_win_probability=0.32,
        prediction_method="machine_learning",
        feature_importance={
            "home_rolling_win_pct": 0.142,
            "home_era": 0.118,
            "away_rolling_runs_allowed": 0.095
        }
    )

    with patch("api.src.mlb_analytics.get_enhanced_mlb_game_analytics") as mock_analytics:
        mock_analytics.return_value = mock_response

        response = client.get(f"/analytics/mlb/game?id={game_id}")
        assert response.status_code == 200

        response_data = response.json()

        # Verify base prediction fields
        assert response_data["id"] == game_id
        assert response_data["predicted_winner"] == "Dodgers"
        assert response_data["win_probability"] == 0.68

        # Verify ML-specific fields
        assert response_data["prediction_method"] == "machine_learning"
        assert response_data["ml_model_name"] == "RandomForest-v1.0"
        assert response_data["ml_confidence"] == "High"
        assert response_data["home_win_probability"] == 0.68
        assert response_data["away_win_probability"] == 0.32
        assert "feature_importance" in response_data
        assert len(response_data["feature_importance"]) == 3


def test_mlb_game_analytics_with_rule_based_fallback(client):
    """
    Test that the MLB analytics endpoint falls back to rule-based when ML unavailable.
    """
    game_id = "rule_game_456"

    from api.src.models.mlb_analytics import MlbAnalyticsResponse, TeamAnalytics

    mock_response = MlbAnalyticsResponse(
        id=game_id,
        home_team="Mets",
        away_team="Braves",
        predicted_winner="Mets",
        win_probability=0.58,
        home_analytics=TeamAnalytics(
            name="Mets",
            winning_percentage=0.58,
            rolling_win_percentage=0.60,
            offensive_rating=0.70,
            defensive_rating=0.68,
            days_rest=1,
            momentum_score=0.66
        ),
        away_analytics=TeamAnalytics(
            name="Braves",
            winning_percentage=0.54,
            rolling_win_percentage=0.55,
            offensive_rating=0.68,
            defensive_rating=0.67,
            days_rest=2,
            momentum_score=0.63
        ),
        key_factors={
            "season_record": "Mets has better season record",
            "recent_form": "Mets has better rolling win percentage"
        },
        confidence_level="Medium",
        # ML fields should be None for rule-based
        prediction_method="rule_based",
        ml_model_name=None,
        ml_confidence=None,
        home_win_probability=None,
        away_win_probability=None,
        feature_importance=None
    )

    with patch("api.src.mlb_analytics.get_enhanced_mlb_game_analytics") as mock_analytics:
        mock_analytics.return_value = mock_response

        response = client.get(f"/analytics/mlb/game?id={game_id}")
        assert response.status_code == 200

        response_data = response.json()

        # Verify base prediction fields
        assert response_data["id"] == game_id
        assert response_data["predicted_winner"] == "Mets"
        assert response_data["win_probability"] == 0.58

        # Verify fallback to rule-based
        assert response_data["prediction_method"] == "rule_based"
        assert response_data["ml_model_name"] is None
        assert response_data["ml_confidence"] is None