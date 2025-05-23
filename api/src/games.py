import traceback
from fastapi import HTTPException
from api.src.models.tables import Odds
from api.src.models.games import Game, GamesResponse
from dateutil import parser
from datetime import timedelta, datetime
from api.src.config import ODDS_API_URL
from api.src.utils import format_american_odds
from shared.database import connect_to_db
import requests
from sqlalchemy import cast, Date, func
from pytz import timezone, utc
    
async def get_games_for_sport(date: str, sport: str, api_sport_param: str):
    try:
        parsed_date = datetime.strptime(date, "%Y-%m-%d")
        return get_games_by_date(parsed_date, sport, api_sport_param)
    except ValueError as e:
        error_message = f"Invalid date format. Please use YYYY-MM-DD format. Error: {str(e)}"
        traceback_message = traceback.format_exc()
        print(f"Error: {error_message}\nTraceback: {traceback_message}")
        raise HTTPException(status_code=400, detail=error_message)
    except Exception as e:
        error_message = f"An error occurred while processing the request. Error: {str(e)}"
        traceback_message = traceback.format_exc()
        print(f"Error: {error_message}\nTraceback: {traceback_message}")
        raise HTTPException(status_code=500, detail=error_message)

def call_odds_api(sport):
    url = ODDS_API_URL.format(sport=sport)
    response = requests.get(url).json()
    return response

def parse_response_and_store_games(odds_response, sport):
    games = []
    eastern = timezone('US/Eastern')
    for game_data in odds_response:
        home_team = game_data['home_team']
        away_team = game_data['away_team']
        commence_time_utc = parser.parse(game_data['commence_time']).replace(tzinfo=utc)
        commence_time_local = commence_time_utc.astimezone(eastern)
        game_id = game_data['id']
        
        fanduel_bookmaker = next((bm for bm in game_data.get('bookmakers', []) if bm['key'] == 'fanduel'), None)
        if fanduel_bookmaker:
            h2h_market = next((market for market in fanduel_bookmaker.get('markets', []) if market['key'] == 'h2h'), None)
            if h2h_market:
                outcomes = {outcome['name']: outcome['price'] for outcome in h2h_market.get('outcomes', [])}
                home_odds = format_american_odds(outcomes.get(home_team, 0))
                away_odds = format_american_odds(outcomes.get(away_team, 0))
                
                game = Game(
                    id=game_id,
                    sport=sport,
                    homeTeam=home_team,
                    awayTeam=away_team,
                    time=commence_time_local.strftime("%Y-%m-%d %H:%M"),
                    homeOdds=home_odds,
                    awayOdds=away_odds
                )
                games.append(game)
                
                if not update_existing_odds_in_db(game_id, home_odds, away_odds):
                    store_odds(game)
    
    return games

def update_existing_odds_in_db(game_id, home_odds, away_odds):
    session = connect_to_db()
    existing = session.query(Odds).filter_by(id=game_id).first()
    if existing:
        existing.home_odds = home_odds
        existing.away_odds = away_odds
        existing.expires = datetime.now() + timedelta(minutes=72)
        session.commit()
        session.close()
        return True
    session.close()
    return False

def store_odds(game: Game):
    session = connect_to_db()
    game = Odds(
        id=game.id,
        sport=game.sport,
        time=game.time,
        home_odds=game.homeOdds,
        away_odds=game.awayOdds,
        home_team=game.homeTeam,
        away_team=game.awayTeam,
        expires=datetime.strptime(game.time, "%Y-%m-%d %H:%M") + timedelta(minutes=72)
    )
    session.add(game)
    session.commit()
    session.close()

def is_data_expired(sport):
    session = connect_to_db()
    current_time = datetime.now()
    nearest_expiration = session.query(func.min(Odds.expires)).filter(Odds.sport == sport).scalar()
    session.close()

    if nearest_expiration is None:
        return True
    return nearest_expiration <= current_time


def get_games_by_date(date, sport, api_sport_param):
    if is_data_expired(sport):
        odds_response = call_odds_api(api_sport_param)
        games = parse_response_and_store_games(odds_response, sport)
        games_for_date = [game for game in games if game.time.split(" ")[0] == date.strftime("%Y-%m-%d")]
        return GamesResponse(list=games_for_date)
    else:
        session = connect_to_db()
        games = session.query(Odds).filter(cast(Odds.time, Date) == date, Odds.sport == sport).all()
        games_list = [
            Game(
                id=game.id,
                sport=sport,
                homeTeam=game.home_team,
                awayTeam=game.away_team,
                time=game.time.strftime("%Y-%m-%d %H:%M"),
                homeOdds=game.home_odds,
                awayOdds=game.away_odds
            )
            for game in games
        ]
        session.close()
        return GamesResponse(list=games_list)
