from unittest.mock import patch, MagicMock
from api.src.login import get_user_by_username
from api.src.models.auth import AuthenticatedUser
from api.src.models.tables import Users

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