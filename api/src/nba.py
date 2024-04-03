from api.src.models.tables.odds import Odds
from nba_api.live.nba.endpoints import scoreboard
from api.src.models.nba import Game, GamesResponse
from dateutil import parser
from datetime import timedelta, timezone, datetime
from api.src.config import ODDS_API_URL, DB_URL
from api.src.utils import format_american_odds
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pprint   

def fetch_odds(game_id, home_team, away_team):
    response = requests.get(ODDS_API_URL).json()
    pprint.pp(response)
    odds = {}
    for game in response:
        if game['home_team'] == home_team and game['away_team'] == away_team:
            fanduel_bookmaker = next((bm for bm in game.get('bookmakers', []) if bm['key'] == 'fanduel'), None)
            if fanduel_bookmaker:
                h2h_market = next((market for market in fanduel_bookmaker.get('markets', []) if market['key'] == 'h2h'), None)
                if h2h_market:
                    outcomes = {outcome['name']: outcome['price'] for outcome in h2h_market.get('outcomes', [])}
                    odds['home'] = format_american_odds(outcomes.get(home_team, 0))
                    odds['away'] = format_american_odds(outcomes.get(away_team, 0))
    if odds != {}:
        pprint.pp({'game_id': game_id, 'home_team': home_team, 'away_team': away_team, 'odds': odds})
        cache_odds(game_id, odds, home_team, away_team)
    return odds

def connect_to_db():
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session

def cache_odds(game_id, odds_data, home_team, away_team):
    session = connect_to_db()
    expires = datetime.now() + timedelta(minutes=72)
    game = Odds(
        id=game_id,
        time=datetime.now(),
        home_odds=odds_data['home'],
        away_odds=odds_data['away'],
        home_team=home_team,
        away_team=away_team,
        expires=expires
    )
    session.add(game)
    session.commit()

def is_odds_data_cached(game_id):
    session = connect_to_db()
    odds_data = session.query(Odds).filter_by(id=game_id).first()
    return {
            'home': odds_data.home_odds,
            'away': odds_data.away_odds
    } if odds_data and (odds_data.expires is not None and odds_data.expires > datetime.now()) else None

def team_name(game, team):
    city = game[f'{team}Team']['teamCity']
    if city == "LA":
        city = "Los Angeles"
    return f"{city} {game[f'{team}Team']['teamName']}"

def create_game_object(game, date):
    home_team = team_name(game, 'home')
    away_team = team_name(game, 'away')
    game_id = game['gameId']
    cached_odds = is_odds_data_cached(game_id)
    odds = cached_odds if cached_odds else fetch_odds(game_id, home_team, away_team)
    home_odds = str(odds.get('home'))
    away_odds = str(odds.get('away'))
    return Game(
        id=game_id,
        sport='NBA',
        homeTeam=home_team,
        awayTeam=away_team,
        date=date,
        time=parser.parse(game["gameTimeUTC"]).replace(tzinfo=timezone.utc).astimezone(tz=None).strftime("%H:%M"),
        homeOdds=home_odds,
        awayOdds=away_odds
    )

def get_todays_games():
    board = scoreboard.ScoreBoard()
    date = board.score_board_date
    games = board.games.get_dict()
    games_list = [create_game_object(game, date) for game in games]
    return GamesResponse(list=games_list)
