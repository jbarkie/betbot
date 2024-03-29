from nba_api.live.nba.endpoints import scoreboard
from models.nba import Game, GamesResponse
from dateutil import parser
from datetime import timezone
from config import ODDS_API_URL
import requests

def fetch_odds(home_team, away_team):
    response = requests.get(ODDS_API_URL).json()
    for game in response:
        if game['home_team'] == home_team and game['away_team'] == away_team:
            fanduel_bookmaker = next((bm for bm in game.get('bookmakers', []) if bm['key'] == 'fanduel'), None)
            if fanduel_bookmaker:
                h2h_market = next((market for market in fanduel_bookmaker.get('markets', []) if market['key'] == 'h2h'), None)
                if h2h_market:
                    outcomes = {outcome['name']: outcome['price'] for outcome in h2h_market.get('outcomes', [])}
                    return {
                        'home': format_american_odds(outcomes.get(home_team, 0)),
                        'away': format_american_odds(outcomes.get(away_team, 0))
                    }
    return {}

def format_american_odds(decimal_odds):
    if decimal_odds > 2:
        underdog_odds = round(100 * (decimal_odds - 1))
        return f"+{underdog_odds}"
    else:
        favorite_odds = round(100 / (decimal_odds - 1))
        return f"-{favorite_odds}"

def create_game_object(game, date):
    home_team = f"{game['homeTeam']['teamCity']} {game['homeTeam']['teamName']}"
    away_team = f"{game['awayTeam']['teamCity']} {game['awayTeam']['teamName']}"
    return Game(
        id=game['gameId'],
        sport='NBA',
        homeTeam=home_team,
        awayTeam=away_team,
        date=date,
        time=parser.parse(game["gameTimeUTC"]).replace(tzinfo=timezone.utc).astimezone(tz=None).strftime("%H:%M"),
        odds=fetch_odds(home_team, away_team)
    )

def get_todays_games():
    board = scoreboard.ScoreBoard()
    date = board.score_board_date
    games = board.games.get_dict()
    games_list = [create_game_object(game, date) for game in games]
    return GamesResponse(list=games_list)
