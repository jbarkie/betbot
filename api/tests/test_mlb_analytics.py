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