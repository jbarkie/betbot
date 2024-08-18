import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from datetime import date, datetime, timedelta
from api.src.main import app
from api.src.games import get_games_by_date, store_odds
from api.src.login import create_access_token
from api.src.models.nba import Game
from api.src.models.tables import Odds

client = TestClient(app)

@pytest.fixture(autouse=True)
def mock_db_connection():
    with patch('api.src.games.connect_to_db') as mock:
        yield mock

@pytest.fixture(autouse=True)
def mock_odds_api():
    with patch('api.src.games.call_odds_api') as mock:
        mock.return_value = [
            {
                'id': 'test_game_id',
                'commence_time': '2023-06-08T00:00:00Z',
                'home_team': 'Test Home Team',
                'away_team': 'Test Away Team',
                'bookmakers': [
                    {
                        'key': 'fanduel',
                        'markets': [
                            {
                                'key': 'h2h',
                                'outcomes': [
                                    {'name': 'Test Home Team', 'price': 1.5},
                                    {'name': 'Test Away Team', 'price': 2.5}
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
        yield mock

def get_headers():
    token = create_access_token(data={"sub": "test"}, expires_delta=timedelta(minutes=30))
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.parametrize("endpoint", ["/nba/games", "/mlb/games", "/nfl/games", "/nhl/games"])
def test_games(endpoint, mock_db_connection):
    mock_session = MagicMock()
    mock_db_connection.return_value = mock_session
    
    mock_expiration = datetime.now() + timedelta(hours=1)  # Data not expired
    mock_session.query.return_value.filter.return_value.scalar.return_value = mock_expiration
    
    mock_session.query.return_value.filter.return_value.all.return_value = [
        MagicMock(
            id='test_game_id',
            sport='TEST',
            home_team='Test Home Team',
            away_team='Test Away Team',
            time=datetime.now(),
            home_odds='-200',
            away_odds='+150'
        )
    ]

    today = date.today().strftime("%Y-%m-%d")
    response = client.get(f"{endpoint}?date={today}", headers=get_headers())
    assert response.status_code == 200
    assert len(response.json()['list']) > 0

@pytest.mark.parametrize("endpoint", ["/nba/games", "/mlb/games", "/nfl/games", "/nhl/games"])
def test_games_invalid_date_format(endpoint):
    response = client.get(f"{endpoint}?date=invalid-date", headers=get_headers())
    assert response.status_code == 400
    assert "Invalid date format" in response.json()['detail']

@pytest.mark.parametrize("endpoint", ["/nba/games", "/mlb/games", "/nfl/games", "/nhl/games"])
def test_games_internal_server_error(endpoint):
    with patch('api.src.games.get_games_by_date', side_effect=Exception("Unexpected error")):
        response = client.get(f"{endpoint}?date=2023-07-31", headers=get_headers())
        assert response.status_code == 500
        assert "An error occurred while processing the request" in response.json()['detail']

@pytest.mark.parametrize("endpoint", ["/nba/games", "/mlb/games", "/nfl/games", "/nhl/games"])
def test_games_no_date_provided(endpoint):
    response = client.get(endpoint, headers=get_headers())
    assert response.status_code == 422

@pytest.mark.parametrize("endpoint, sport, api_sport", [
    ("/nba/games", "NBA", "basketball_nba"),
    ("/mlb/games", "MLB", "baseball_mlb"),
    ("/nfl/games", "NFL", "americanfootball_nfl"),
    ("/nhl/games", "NHL", "icehockey_nhl")
])
def test_games_expired_data(endpoint, sport, api_sport, mock_db_connection, mock_odds_api):
    mock_session = MagicMock()
    mock_db_connection.return_value = mock_session

    mock_expiration = datetime.now() - timedelta(hours=1) 
    mock_session.query.return_value.filter.return_value.scalar.return_value = mock_expiration

    mock_odds_api.return_value = [
        {
            'id': 'test_game_id',
            'commence_time': datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            'home_team': 'Test Home Team',
            'away_team': 'Test Away Team',
            'bookmakers': [
                {
                    'key': 'fanduel',
                    'markets': [
                        {
                            'key': 'h2h',
                            'outcomes': [
                                {'name': 'Test Home Team', 'price': 1.5},
                                {'name': 'Test Away Team', 'price': 2.5}
                            ]
                        }
                    ]
                }
            ]
        }
    ]

    with patch('api.src.games.is_data_expired', return_value=True), \
         patch('api.src.games.get_games_by_date', wraps=get_games_by_date) as wrapped_get_games:
        today = date.today().strftime("%Y-%m-%d")
        response = client.get(f"{endpoint}?date={today}", headers=get_headers())

        assert response.status_code == 200
        assert len(response.json()['list']) > 0, f"No games returned for {sport}"

        mock_odds_api.assert_called_once_with(api_sport)

    game = response.json()['list'][0]
    assert game['sport'] == sport
    assert game['homeTeam'] == 'Test Home Team'
    assert game['awayTeam'] == 'Test Away Team'

def test_store_odds():
    mock_game = Game(
        id="test_game_id",
        sport="TEST",
        homeTeam="Home Team",
        awayTeam="Away Team",
        time="2024-08-17 15:30",
        homeOdds="-150",
        awayOdds="+130"
    )
    mock_session = MagicMock()

    with patch('api.src.games.connect_to_db', return_value=mock_session):
        store_odds(mock_game)

        mock_session.add.assert_called_once()

        added_odds = mock_session.add.call_args[0][0]

        assert isinstance(added_odds, Odds)
        assert added_odds.id == "test_game_id"
        assert added_odds.sport == "TEST"
        assert added_odds.home_team == "Home Team"
        assert added_odds.away_team == "Away Team"
        assert added_odds.time == "2024-08-17 15:30"
        assert added_odds.home_odds == "-150"
        assert added_odds.away_odds == "+130"
        
        expected_expiration = datetime.strptime(mock_game.time, "%Y-%m-%d %H:%M") + timedelta(minutes=72)
        assert added_odds.expires == expected_expiration

        mock_session.commit.assert_called_once()