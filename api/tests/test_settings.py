from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from api.src.main import app
from api.src.login import get_current_user
from api.src.models.tables import Users
import pytest

@pytest.fixture
def test_client():
    mock_user = MagicMock()
    mock_user.username = "testuser"
    
    async def mock_get_current_user():
        return mock_user
    
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    client = TestClient(app)

    yield client

    # Cleanup
    app.dependency_overrides.clear()

@patch("api.src.settings.connect_to_db")
def test_update_settings_success(mock_connect_to_db, test_client):
    """Test a successful update of user settings with valid data"""

    mock_session = MagicMock()
    mock_user = MagicMock(spec=Users)
    mock_user.username = "testuser"
    mock_user.email = "old@example.com"
    mock_user.email_notifications_enabled = False

    mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user
    mock_connect_to_db.return_value = mock_session
    
    settings_data = {
        "username": "updated",
        "email": "new@example.com",
        "email_notifications_enabled": True
    }

    response = test_client.post("/settings", json=settings_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["message"] == "Settings updated successfully"
    assert data["username"] == "updated"
    assert data["email"] == "new@example.com"
    assert data["email_notifications_enabled"] is True

    mock_connect_to_db.assert_called_once()
    mock_session.commit.assert_called_once()

    assert mock_user.username == "updated"
    assert mock_user.email == "new@example.com"
    assert mock_user.email_notifications_enabled is True

@patch("api.src.settings.connect_to_db")
def test_update_settings_partial(mock_connect_to_db, test_client):
    """Test the settings endpoint with partial data"""

    mock_session = MagicMock()
    mock_user = MagicMock(spec=Users)
    mock_user.username = "testuser"
    mock_user.email = "old@example.com"
    mock_user.email_notifications_enabled = False


    mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user
    mock_connect_to_db.return_value = mock_session
    
    # Test data with only email field
    settings_data = {
        "email": "partial@example.com"
    }
    
    response = test_client.post("/settings", json=settings_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "email" in data
    assert data["email"] == "partial@example.com"