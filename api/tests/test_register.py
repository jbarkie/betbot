from fastapi.testclient import TestClient
from api.src.main import app
from unittest.mock import patch, MagicMock
from api.src.register import register_user

client = TestClient(app)

def test_register_user_function():
    mock_session = MagicMock()
    mock_user = MagicMock()
    mock_users_constructor = MagicMock(return_value=mock_user)

    with patch('api.src.register.connect_to_db', return_value=mock_session), \
         patch('api.src.register.Users', mock_users_constructor), \
         patch('bcrypt.hashpw', return_value=b'hashed_password'):
        
        result = register_user(
            username="testuser",
            first_name="Test",
            last_name="User",
            email="testuser@example.com",
            password="password123"
        )

        mock_users_constructor.assert_called_once_with(
            username="testuser",
            first_name="Test",
            last_name="User",
            email="testuser@example.com",
            password=b'hashed_password'
        )

        mock_session.add.assert_called_once_with(mock_user)
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

        assert result == mock_user

def test_register_endpoint_integration():
    mock_session = MagicMock()
    mock_user = MagicMock()
    mock_users_constructor = MagicMock(return_value=mock_user)

    with patch('api.src.register.connect_to_db', return_value=mock_session), \
         patch('api.src.register.Users', mock_users_constructor), \
         patch('api.src.main.get_user_by_username', return_value=None), \
         patch('bcrypt.hashpw', return_value=b'hashed_password'):
        
        register_data = {
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "email": "newuser@example.com",
            "password": "password123"
        }
        response = client.post("/register", json=register_data)
        
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"

        mock_users_constructor.assert_called_once_with(
            username="newuser",
            first_name="New",
            last_name="User",
            email="newuser@example.com",
            password=b'hashed_password'
        )

        mock_session.add.assert_called_once_with(mock_user)
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

def test_register_endpoint_integration_user_exists():
    mock_session = MagicMock()
    mock_user = MagicMock()
    mock_users_constructor = MagicMock(return_value=mock_user)

    with patch('api.src.register.connect_to_db', return_value=mock_session), \
         patch('api.src.register.Users', mock_users_constructor), \
         patch('api.src.main.get_user_by_username', return_value=mock_user), \
         patch('bcrypt.hashpw', return_value=b'hashed_password'):
        
        register_data = {
            "username": "existinguser",
            "first_name": "Existing",
            "last_name": "User",
            "email": "newuser@example.com",
            "password": "password123"
        }
        response = client.post("/register", json=register_data)

        assert response.status_code == 403
        assert response.json() == {"detail": "User already exists"}