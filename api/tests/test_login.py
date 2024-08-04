from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import pytest
from api.src.config import ALGORITHM, SECRET_KEY
from api.src.login import get_user_by_username
from api.src.main import app
from api.src.models.auth import AuthenticatedUser
from api.src.models.tables import Users
import bcrypt
import jwt

client = TestClient(app)

def test_get_user_by_username():
    mock_session = MagicMock()
    mock_user = MagicMock(spec=Users)
    mock_user.username = "testuser"
    mock_user.first_name = "Test"
    mock_user.last_name = "User"
    mock_user.email = "testuser@example.com"
    mock_user.password = "hashedpassword123"

    mock_session.query.return_value.filter_by.return_value.first.return_value = mock_user

    with patch('api.src.login.connect_to_db', return_value=mock_session):
        result = get_user_by_username("testuser")

        assert mock_session.query.called
        mock_session.query.assert_called_once_with(Users)
        mock_session.query.return_value.filter_by.assert_called_once_with(username="testuser")
        mock_session.query.return_value.filter_by.return_value.first.assert_called_once()

        assert isinstance(result, AuthenticatedUser)
        assert result.username == "testuser"
        assert result.first_name == "Test"
        assert result.last_name == "User"
        assert result.email == "testuser@example.com"
        assert result.hashed_password == "hashedpassword123"

def test_get_user_by_username_not_found():
    mock_session = MagicMock()
    mock_session.query.return_value.filter_by.return_value.first.return_value = None

    with patch('api.src.login.connect_to_db', return_value=mock_session):
        result = get_user_by_username("nonexistentuser")

        assert mock_session.query.called
        mock_session.query.assert_called_once_with(Users)
        mock_session.query.return_value.filter_by.assert_called_once_with(username="nonexistentuser")
        mock_session.query.return_value.filter_by.return_value.first.assert_called_once()

        assert result is None

@pytest.fixture
def mock_user():
    user = MagicMock()
    user.username = "testuser"
    user.first_name = "Test"
    user.last_name = "User"
    user.email = "test@testing.com"
    user.hashed_password = bcrypt.hashpw("correctpassword".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    return user

def test_login_successful(mock_user):
    with patch('api.src.login.authenticate_user', return_value=mock_user), \
         patch('api.src.login.get_user_by_username', return_value=mock_user), \
         patch('bcrypt.checkpw', return_value=True):
        response = client.post("/login", data={"username": "testuser", "password": "correctpassword"})
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"

def test_login_incorrect_password(mock_user):
    with patch('api.src.login.get_user_by_username', return_value=mock_user):
        response = client.post("/login", data={"username": "testuser", "password": "wrongpassword"})
    
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid username or password"}

def test_login_nonexistent_user():
    with patch('api.src.login.get_user_by_username', return_value=None):
        response = client.post("/login", data={"username": "nonexistentuser", "password": "anypassword"})
    
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid username or password"}

def test_login_bcrypt_error(mock_user):
    with patch('api.src.login.get_user_by_username', return_value=mock_user), \
         patch('bcrypt.checkpw', side_effect=ValueError()):
        response = client.post("/login", data={"username": "testuser", "password": "anypassword"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid username or password"}

def test_get_current_user_valid_token(mock_user):
    with patch('api.src.login.get_user_by_username', return_value=mock_user):
        token = jwt.encode({"sub": "testuser"}, SECRET_KEY, algorithm=ALGORITHM)
        response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json() == {
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "email": "test@testing.com"
        }

def test_get_current_user_invalid_token():
    token = "invalidtoken"
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}

def test_get_current_user_no_username(mock_user):
    with patch('api.src.login.get_user_by_username', return_value=mock_user):
        token = jwt.encode({}, SECRET_KEY, algorithm=ALGORITHM)
        response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate credentials"

def test_get_current_user_nonexistent_user():
    with patch('api.src.login.get_user_by_username', return_value=None):
        token = jwt.encode({"sub": "nonexistentuser"}, SECRET_KEY, algorithm=ALGORITHM)
        response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate credentials"