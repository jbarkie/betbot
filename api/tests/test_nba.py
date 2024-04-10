from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from api.src.nba import call_odds_api, is_odds_data_cached, store_odds, team_name, create_game_object, update_existing_odds_in_db
from api.src.main import app

client = TestClient(app)

odds_data = [
    {
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

game = {
        'gameId': 'test_game_id',
        'gameTimeUTC': '2023-06-08T00:00:00Z',
        'homeTeam': {'teamCity': 'Test City', 'teamName': 'Test Team'},
        'awayTeam': {'teamCity': 'LA', 'teamName': 'Test Team'}
}

def test_status():
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_nba_games():
    response = client.get("/nba/games")
    assert response.status_code == 200
    assert len(response.json()['list']) > 0

def test_call_odds_api(mocker):
    mock_response = mocker.patch('requests.get')
    mock_response.return_value.json.return_value = odds_data
    odds_response = call_odds_api()
    assert odds_response == mock_response.return_value.json.return_value

def test_is_odds_data_cached(mocker):
    mock_query = mocker.patch('api.src.nba.connect_to_db')
    mock_query.return_value.query.return_value.filter_by.return_value.first.return_value = None
    assert is_odds_data_cached('test_game_id') == None
    mock_odds_data = mocker.MagicMock()
    mock_odds_data.home_odds = '-200'
    mock_odds_data.away_odds = '+150'
    mock_odds_data.expires = datetime.now() + timedelta(minutes=10)
    mock_query.return_value.query.return_value.filter_by.return_value.first.return_value = mock_odds_data
    assert is_odds_data_cached('test_game_id') == {'home': '-200', 'away': '+150'}

def test_update_existing_odds_in_db(mocker):
    mock_session = mocker.patch('api.src.nba.connect_to_db')
    mock_existing_odds = mocker.MagicMock()
    mock_session.return_value.query.return_value.filter_by.return_value.first.return_value = mock_existing_odds
    assert update_existing_odds_in_db('test_game_id', {'home': '-200', 'away': '+150'}) == True
    assert mock_existing_odds.home_odds == '-200'
    assert mock_existing_odds.away_odds == '+150'
    mock_session.return_value.commit.assert_called_once()
    mock_session.return_value.query.return_value.filter_by.return_value.first.return_value = None
    assert update_existing_odds_in_db('test_game_id', {'home': '-200', 'away': '+150'}) == False

def test_store_odds(mocker):
    mock_session = mocker.patch('api.src.nba.connect_to_db')
    store_odds('test_game_id', {'home': '-200', 'away': '+150'}, 'Test Home Team', 'Test Away Team')
    mock_session.return_value.add.assert_called_once()
    mock_session.return_value.commit.assert_called_once()

def test_team_name():
    test_game = {
        'homeTeam': {'teamCity': 'Test City', 'teamName': 'Test Team'},
        'awayTeam': {'teamCity': 'LA', 'teamName': 'Test Team'}
    }
    assert team_name(test_game, 'home') == 'Test City Test Team'
    assert team_name(test_game, 'away') == 'Los Angeles Test Team'

def test_create_game_object(mocker):
    mocker.patch('api.src.nba.is_odds_data_cached', return_value=None)
    mocker.patch('api.src.nba.update_existing_odds_in_db', return_value=False)
    mocker.patch('api.src.nba.store_odds')
    game_object = create_game_object(game, '2023-06-08', odds_data)
    assert game_object.id == 'test_game_id'
    assert game_object.sport == 'NBA'
    assert game_object.homeTeam == 'Test City Test Team'
    assert game_object.awayTeam == 'Los Angeles Test Team'
    assert game_object.date == '2023-06-08'
    assert game_object.time == '18:00'
    assert game_object.homeOdds == '-200'
    assert game_object.awayOdds == '+150'

def test_odds_equal_to_one(mocker):
    mocker.patch('api.src.nba.is_odds_data_cached', return_value=None)
    mocker.patch('api.src.nba.update_existing_odds_in_db', return_value=False)
    mocker.patch('api.src.nba.store_odds')
    odds_data[0]['bookmakers'][0]['markets'][0]['outcomes'][0]['price'] = 1
    game_object = create_game_object(game, '2023-06-08', odds_data)
    assert game_object.homeOdds == 'None'