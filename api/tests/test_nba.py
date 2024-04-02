from fastapi.testclient import TestClient
from api.src.nba import fetch_odds, is_odds_data_cached, cache_odds, team_name, create_game_object
from api.src.main import app

client = TestClient(app)

def test_status():
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_nba_games():
    response = client.get("/nba/games")
    assert response.status_code == 200
    assert len(response.json()['list']) > 0

def test_fetch_odds(mocker):
    mock_response = mocker.patch('requests.get')
    mock_response.return_value.json.return_value = [
        {
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
    odds = fetch_odds('test_game_id', 'Test Home Team', 'Test Away Team')
    assert odds == {'home': '-200', 'away': '+150'}

def test_is_odds_data_cached(mocker):
    mock_query = mocker.patch('api.src.nba.connect_to_db')
    mock_query.return_value.query.return_value.filter_by.return_value.first.return_value = None
    assert is_odds_data_cached('test_game_id') == None
    mock_odds_data = mocker.MagicMock()
    mock_odds_data.home_odds = '-200'
    mock_odds_data.away_odds = '+150'
    mock_query.return_value.query.return_value.filter_by.return_value.first.return_value = mock_odds_data
    assert is_odds_data_cached('test_game_id') == {'home': '-200', 'away': '+150'}

def test_cache_odds(mocker):
    mock_session = mocker.patch('api.src.nba.connect_to_db')
    cache_odds('test_game_id', {'home': '-200', 'away': '+150'}, 'Test Home Team', 'Test Away Team')
    mock_session.return_value.add.assert_called_once()
    mock_session.return_value.commit.assert_called_once()

def test_team_name():
    game = {
        'homeTeam': {'teamCity': 'Test City', 'teamName': 'Test Team'},
        'awayTeam': {'teamCity': 'LA', 'teamName': 'Test Team'}
    }
    assert team_name(game, 'home') == 'Test City Test Team'
    assert team_name(game, 'away') == 'Los Angeles Test Team'

def test_create_game_object(mocker):
    game = {
        'gameId': 'test_game_id',
        'gameTimeUTC': '2023-06-08T00:00:00Z',
        'homeTeam': {'teamCity': 'Test City', 'teamName': 'Test Team'},
        'awayTeam': {'teamCity': 'LA', 'teamName': 'Test Team'}
    }
    mocker.patch('api.src.nba.is_odds_data_cached', return_value=None)
    mocker.patch('api.src.nba.fetch_odds', return_value={'home': '-200', 'away': '+150'})
    game_object = create_game_object(game, '2023-06-08')
    assert game_object.id == 'test_game_id'
    assert game_object.sport == 'NBA'
    assert game_object.homeTeam == 'Test City Test Team'
    assert game_object.awayTeam == 'Los Angeles Test Team'
    assert game_object.date == '2023-06-08'
    assert game_object.time == '18:00'
    assert game_object.homeOdds == '-200'
    assert game_object.awayOdds == '+150'