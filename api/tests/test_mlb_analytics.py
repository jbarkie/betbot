from unittest.mock import MagicMock
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
    response = client.get(f"/analytics/mlb/game?id={game_id}")
    
    assert response.status_code == 200
    assert response.json() == {"id": game_id}