from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from api.src.main import app
from api.src.login import get_current_user

def get_test_client():
    mock_user = MagicMock()
    mock_user.username = "testuser"
    
    async def mock_get_current_user():
        return mock_user
    
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    return TestClient(app)

def test_update_settings_success():
    """Test the settings endpoint with valid data"""
    client = get_test_client()
    
    settings_data = {
        "username": "updated",
        "email": "new@example.com",
        "email_notifications_enabled": True
    }
    
    response = client.post("/settings", json=settings_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "username" in data
    assert data["username"] == "updated"
    assert "email" in data
    assert data["email"] == "new@example.com"
    assert "email_notifications_enabled" in data
    assert data["email_notifications_enabled"] is True

def test_update_settings_partial():
    """Test the settings endpoint with partial data"""
    client = get_test_client()
    
    # Test data with only email field
    settings_data = {
        "email": "partial@example.com"
    }
    
    response = client.post("/settings", json=settings_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "email" in data
    assert data["email"] == "partial@example.com"