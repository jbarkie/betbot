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
    # Mock Odds and MLBTeam objects
    mock_odds = MagicMock()
    mock_odds.id = game_id
    mock_odds.home_team = "Red Sox"
    mock_odds.away_team = "Yankees"
    
    mock_home_team = MagicMock()
    mock_home_team.name = "Red Sox"
    mock_home_team.winning_percentage = 0.6
    mock_away_team = MagicMock()
    mock_away_team.name = "Yankees"
    mock_away_team.winning_percentage = 0.5

    with patch("api.src.mlb_analytics.connect_to_db") as mock_connect_to_db, \
         patch("api.src.mlb_analytics.Odds") as mock_odds_model, \
         patch("api.src.mlb_analytics.MLBTeam") as mock_mlb_team_model:
        # Setup session mock
        mock_session = MagicMock()
        mock_connect_to_db.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            mock_odds,  # Odds lookup
            mock_home_team,  # Home team lookup
            mock_away_team   # Away team lookup
        ]

        response = client.get(f"/analytics/mlb/game?id={game_id}")
        assert response.status_code == 200
        assert response.json() == {
            "id": game_id,
            "home_team": "Red Sox",
            "away_team": "Yankees",
            "predicted_winner": "Red Sox",
            "win_probability": 0.55
        }