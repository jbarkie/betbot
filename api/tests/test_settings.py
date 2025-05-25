from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from api.src.main import app
from api.src.login import get_current_user
from api.src.models.tables import Users
import pytest

@pytest.fixture
def test_client():
    """Create a test client with mocked authentication"""
    mock_user = MagicMock()
    mock_user.username = "testuser"
    
    async def mock_get_current_user():
        return mock_user
    
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    client = TestClient(app)

    yield client

    # Cleanup
    app.dependency_overrides.clear()

@pytest.fixture
def mock_db(monkeypatch):
    """Create a mocked database session and user"""
    mock_session = MagicMock()
    mock_user = MagicMock(spec=Users)
    mock_user.username = "testuser"
    mock_user.email = "old@example.com"
    mock_user.email_notifications_enabled = False
    mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user
    monkeypatch.setattr("api.src.settings.connect_to_db", lambda: mock_session)
    return mock_session, mock_user


def test_update_settings_success(test_client, mock_db):
    """Test a successful update of user settings with valid data"""
    mock_session, mock_user = mock_db
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
    mock_session.commit.assert_called_once()
    assert mock_user.username == "updated"
    assert mock_user.email == "new@example.com"
    assert mock_user.email_notifications_enabled is True

def test_update_settings_partial(test_client, mock_db):
    """Test a successful update of user settings with a request that only changes one field"""
    mock_session, mock_user = mock_db
    settings_data = {
        "email": "partial@example.com"
    }
    response = test_client.post("/settings", json=settings_data)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["email"] == "partial@example.com"

def test_update_settings_user_not_found(test_client, monkeypatch):
    """Test failed update of settings when the user does not exist"""
    mock_session = MagicMock()
    mock_session.query.return_value.filter_by.return_value.first.return_value = None
    monkeypatch.setattr("api.src.settings.connect_to_db", lambda: mock_session)

    settings_data = {
        "username": "nonexistent",
        "email": "doesnotexist@example.com"
    }
    response = test_client.post("/settings", json=settings_data)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["message"] == "User not found"
    assert data["username"] == "nonexistent"
    assert data["email"] is None
    assert data["email_notifications_enabled"] is None

def test_update_settings_exception_handling(test_client, mock_db):
    """Test updating settings when an exception occurs"""
    mock_session, mock_user = mock_db
    mock_session.commit.side_effect = Exception("Database error")

    settings_data = {
        "username": "testuser",
        "email": "error@example.com",
        "email_notifications_enabled": True
    }
    response = test_client.post("/settings", json=settings_data)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "An error occurred: Database error" in data["message"]
    assert data["username"] == "testuser"
    assert data["email"] is None
    assert data["email_notifications_enabled"] is None

def test_get_settings_success(test_client, mock_db):
    """Test a successful retrieval of user settings"""
    mock_session, mock_user = mock_db
    response = test_client.get("/settings")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Settings retrieved successfully"
    assert data["username"] == "testuser"

def test_get_settings_user_not_found(test_client, monkeypatch):
    """Test failed retrieval of settings when the user does not exist"""
    mock_session = MagicMock()
    mock_session.query.return_value.filter_by.return_value.first.return_value = None
    monkeypatch.setattr("api.src.settings.connect_to_db", lambda: mock_session)

    response = test_client.get("/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["message"] == "User not found"
    assert data["username"] == "testuser"
    assert data["email"] is None
    assert data["email_notifications_enabled"] is None

def test_get_settings_exception_handling(test_client, mock_db):
    """Test retrieving settings when an exception occurs"""
    mock_session, mock_user = mock_db
    mock_session.query.side_effect = Exception("Database error")

    response = test_client.get("/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "An error occurred: Database error" in data["message"]
    assert data["username"] == "testuser"
    assert data["email"] is None
    assert data["email_notifications_enabled"] is None