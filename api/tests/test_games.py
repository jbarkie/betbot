from fastapi import HTTPException
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from api.src.games import get_games_by_date, get_games_for_sport, is_data_expired, parse_response_and_store_games, store_odds, update_existing_odds_in_db
from api.src.main import app
from api.src.models.nba import Game, GamesResponse
from api.src.login import get_current_user
from api.src.models.tables import Odds

mock_user = {"username": "testuser"}

async def override_get_current_user():
    return mock_user

app.dependency_overrides[get_current_user] = override_get_current_user

@pytest.fixture
def client():
    return TestClient(app)

@pytest.mark.parametrize("endpoint", ["/nba/games", "/mlb/games", "/nfl/games", "/nhl/games"])
def test_games(endpoint, client):
    mock_game = Game(
        id='test_game_id',
        sport='TEST',
        homeTeam='Test Home Team',
        awayTeam='Test Away Team',
        time=datetime.now().strftime("%Y-%m-%d %H:%M"),
        homeOdds='-200',
        awayOdds='+150'
    )

    with patch('api.src.games.get_games_by_date', return_value=GamesResponse(list=[mock_game])):
        today = datetime.now().strftime("%Y-%m-%d")
        response = client.get(f"{endpoint}?date={today}")
        
        assert response.status_code == 200
        assert len(response.json()['list']) > 0

@pytest.mark.parametrize("endpoint", ["/nba/games", "/mlb/games", "/nfl/games", "/nhl/games"])
def test_games_invalid_date_format(endpoint, client):
    response = client.get(f"{endpoint}?date=invalid-date")
    assert response.status_code == 400
    assert "Invalid date format" in response.json()['detail']

@pytest.mark.parametrize("endpoint", ["/nba/games", "/mlb/games", "/nfl/games", "/nhl/games"])
def test_games_no_date_provided(endpoint, client):
    response = client.get(endpoint)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_get_games_for_sport_500_error():
    with patch('api.src.games.get_games_by_date', side_effect=Exception("Unexpected error")):
        with pytest.raises(HTTPException) as exc_info:
            await get_games_for_sport("2023-08-18", "NBA", "basketball_nba")
        assert exc_info.value.status_code == 500
        assert "An error occurred while processing the request" in str(exc_info.value.detail)

def test_parse_response_and_store_games():
    mock_odds_response = [
        {
            'id': 'test_game_id',
            'home_team': 'Home Team',
            'away_team': 'Away Team',
            'commence_time': '2023-08-18T20:00:00Z',
            'bookmakers': [
                {
                    'key': 'fanduel',
                    'markets': [
                        {
                            'key': 'h2h',
                            'outcomes': [
                                {'name': 'Home Team', 'price': 1.5},
                                {'name': 'Away Team', 'price': 2.5}
                            ]
                        }
                    ]
                }
            ]
        }
    ]
    
    with patch('api.src.games.update_existing_odds_in_db', return_value=False), \
         patch('api.src.games.store_odds') as mock_store_odds:
        games = parse_response_and_store_games(mock_odds_response, 'NBA')
        assert len(games) == 1
        assert games[0].id == 'test_game_id'
        assert games[0].sport == 'NBA'
        assert games[0].homeTeam == 'Home Team'
        assert games[0].awayTeam == 'Away Team'
        mock_store_odds.assert_called_once()

def test_update_existing_odds_in_db():
    mock_session = MagicMock()
    mock_session.query.return_value.filter_by.return_value.first.return_value = MagicMock(spec=Odds)
    
    with patch('api.src.games.connect_to_db', return_value=mock_session):
        result = update_existing_odds_in_db('test_game_id', '-150', '+130')
        assert result is True
        mock_session.commit.assert_called_once()

def test_store_odds():
    mock_session = MagicMock()
    mock_game = Game(
        id='test_game_id',
        sport='NBA',
        homeTeam='Home Team',
        awayTeam='Away Team',
        time='2023-08-18 20:00',
        homeOdds='-150',
        awayOdds='+130'
    )
    
    with patch('api.src.games.connect_to_db', return_value=mock_session):
        store_odds(mock_game)
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

def test_is_data_expired():
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.scalar.return_value = datetime.now() - timedelta(hours=2)
    
    with patch('api.src.games.connect_to_db', return_value=mock_session):
        result = is_data_expired('NBA')
        assert result is True

def test_get_games_by_date_expired_data():
    mock_odds_response = [
        {
            'id': 'test_game_id',
            'home_team': 'Home Team',
            'away_team': 'Away Team',
            'commence_time': '2023-08-18T20:00:00Z',
            'bookmakers': [
                {
                    'key': 'fanduel',
                    'markets': [
                        {
                            'key': 'h2h',
                            'outcomes': [
                                {'name': 'Home Team', 'price': 1.5},
                                {'name': 'Away Team', 'price': 2.5}
                            ]
                        }
                    ]
                }
            ]
        }
    ]
    
    with patch('api.src.games.is_data_expired', return_value=True), \
         patch('api.src.games.call_odds_api', return_value=mock_odds_response), \
         patch('api.src.games.update_existing_odds_in_db', return_value=False), \
         patch('api.src.games.store_odds'):
        result = get_games_by_date(datetime(2023, 8, 18), 'NBA', 'basketball_nba')
        assert isinstance(result, GamesResponse)
        assert len(result.list) == 1
        assert result.list[0].id == 'test_game_id'

def test_get_games_by_date_non_expired_data():
    mock_db_games = [
        MagicMock(
            id='test_game_id',
            sport='NBA',
            home_team='Home Team',
            away_team='Away Team',
            time=datetime(2023, 8, 18, 20, 0),
            home_odds='-150',
            away_odds='+130'
        )
    ]
    
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.all.return_value = mock_db_games
    
    with patch('api.src.games.is_data_expired', return_value=False), \
         patch('api.src.games.connect_to_db', return_value=mock_session):
        result = get_games_by_date(datetime(2023, 8, 18), 'NBA', 'basketball_nba')
        assert isinstance(result, GamesResponse)
        assert len(result.list) == 1
        assert result.list[0].id == 'test_game_id'

@pytest.fixture(scope="module", autouse=True)
def cleanup_override():
    yield
    app.dependency_overrides.pop(get_current_user, None)