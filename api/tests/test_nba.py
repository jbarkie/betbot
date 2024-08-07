from fastapi.testclient import TestClient
from datetime import date, datetime, timedelta
from api.src.models.nba import GamesResponse
from api.src.games import call_odds_api, is_data_expired, store_odds, update_existing_odds_in_db, parse_response_and_store_games, get_games_by_date
from api.src.main import app

client = TestClient(app)

odds_data = [
    {
        'id': 'test_game_id',
        'commence_time': '2023-06-08T00:00:00Z',
        'home_team': 'Test City Test Team',
        'away_team': 'Los Angeles Test Team',
        'bookmakers': [
            {
                'key': 'fanduel',
                'markets': [
                    {
                        'key': 'h2h',
                        'outcomes': [
                            {'name': 'Test City Test Team', 'price': 1.5},
                            {'name': 'Los Angeles Test Team', 'price': 2.5}
                        ]
                    }
                ]
            }
        ]
    }
]

def test_nba_games():
    today = date.today().strftime("%Y-%m-%d")
    response = client.get(f"/nba/games?date={today}")
    assert response.status_code == 200
    assert len(response.json()['list']) >= 0

def test_call_odds_api(mocker):
    mock_response = mocker.patch('requests.get')
    mock_response.return_value.json.return_value = odds_data
    odds_response = call_odds_api()
    assert odds_response == mock_response.return_value.json.return_value

def test_is_data_expired(mocker):
    mock_query = mocker.patch('api.src.nba.connect_to_db')
    mock_query.return_value.query.return_value.scalar.return_value = None
    assert is_data_expired() == True
    mock_query.return_value.query.return_value.scalar.return_value = datetime.now() + timedelta(minutes=10)
    assert is_data_expired() == False

def test_update_existing_odds_in_db(mocker):
    mock_session = mocker.patch('api.src.nba.connect_to_db')
    mock_existing_odds = mocker.MagicMock()
    mock_session.return_value.query.return_value.filter_by.return_value.first.return_value = mock_existing_odds
    assert update_existing_odds_in_db('test_game_id', '-200', '+150') == True
    assert mock_existing_odds.home_odds == '-200'
    assert mock_existing_odds.away_odds == '+150'
    mock_session.return_value.commit.assert_called_once()
    mock_session.return_value.query.return_value.filter_by.return_value.first.return_value = None
    assert update_existing_odds_in_db('test_game_id',  '-200', '+150') == False

def test_store_odds(mocker):
    mock_session = mocker.patch('api.src.nba.connect_to_db')
    game = mocker.MagicMock(
        id='test_game_id',
        time='2023-06-08 00:00',
        homeTeam='Test Home Team',
        awayTeam='Test Away Team',
        homeOdds='-200',
        awayOdds='+150'
    )
    store_odds(game)
    mock_session.return_value.add.assert_called_once()
    mock_session.return_value.commit.assert_called_once()

def test_parse_response_and_store_games(mocker):
    mocker.patch('api.src.nba.update_existing_odds_in_db', return_value=False)
    mocker.patch('api.src.nba.store_odds')
    games = parse_response_and_store_games(odds_data)
    assert len(games) == 1
    game = games[0]
    assert game.sport == 'NBA'
    assert game.homeTeam == 'Test City Test Team'
    assert game.awayTeam == 'Los Angeles Test Team'
    assert game.homeOdds == '-200'
    assert game.awayOdds == '+150'

def test_get_games_by_date(mocker):
    mocker.patch('api.src.nba.is_data_expired', return_value=False)
    mock_query = mocker.patch('api.src.nba.connect_to_db')
    mock_query.return_value.query.return_value.filter.return_value.all.return_value = [
        mocker.MagicMock(
            id='test_game_id',
            home_team='Test Home Team',
            away_team='Test Away Team',
            time=datetime.now(),
            home_odds='-200',
            away_odds='+150'
        )
    ]
    games_response = get_games_by_date(datetime.now().date())
    assert len(games_response.list) == 1
    game = games_response.list[0]
    assert game.id == 'test_game_id'
    assert game.sport == 'NBA'
    assert game.homeTeam == 'Test Home Team'
    assert game.awayTeam == 'Test Away Team'
    assert game.homeOdds == '-200'
    assert game.awayOdds == '+150'

def test_games_invalid_date_format():
    response = client.get("/nba/games?date=invalid-date")
    assert response.status_code == 400
    assert "Invalid date format" in response.json()['detail']

def test_games_internal_server_error(mocker):
    mocker.patch('api.src.main.get_games_by_date', side_effect=Exception("Unexpected error"))
    response = client.get("/nba/games?date=2023-07-31")
    assert response.status_code == 500
    assert "An error occurred while processing the request" in response.json()['detail']

def test_games_no_date_provided():
    response = client.get("/nba/games")
    assert response.status_code == 422