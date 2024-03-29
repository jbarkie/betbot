from nba_api.live.nba.endpoints import scoreboard
from models.nba import Game
from models.nba import GamesResponse
from dateutil import parser
from datetime import timezone
from config import NBA_API_KEY
import requests

board = scoreboard.ScoreBoard()
date = board.score_board_date
games = board.games.get_dict()
api_url = 'https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey=' + NBA_API_KEY + '&regions=us&markets=h2h&bookmakers=fanduel'

def get_todays_games():
    response_list = []
    odds_response = requests.get(api_url).json()
    for game in games:
        homeTeam = game['homeTeam']['teamCity'] + ' ' + game['homeTeam']['teamName']
        awayTeam = game['awayTeam']['teamCity'] + ' ' + game['awayTeam']['teamName']
        response_list.append(Game(
            id=game['gameId'],
            sport='NBA',
            homeTeam=homeTeam,
            awayTeam=awayTeam,
            date=date,
            time=parser.parse(game["gameTimeUTC"]).replace(tzinfo=timezone.utc).astimezone(tz=None).strftime("%H:%M"),
            odds=get_current_odds(odds_response, homeTeam, awayTeam)
        ))
    return GamesResponse(list=response_list)

def get_current_odds(data, home_team, away_team):
    for game in data:
        if game['home_team'] == home_team and game['away_team'] == away_team:
            bookmakers = game.get('bookmakers', [])
            if bookmakers:
                fanduel_bookmaker = next((bm for bm in bookmakers if bm['key'] == 'fanduel'), None)
                if fanduel_bookmaker:
                    markets = fanduel_bookmaker.get('markets', [])
                    h2h_market = next((market for market in markets if market['key'] == 'h2h'), None)
                    if h2h_market:
                        outcomes = h2h_market.get('outcomes', [])
                        for outcome in outcomes:
                            if outcome['name'] == home_team:
                                home_odds = outcome['price']
                            elif outcome['name'] == away_team:
                                away_odds = outcome['price']
                        home_odds_formatted = format_american_odds(home_odds)
                        away_odds_formatted = format_american_odds(away_odds)
                        return {
                            'home': home_odds_formatted,
                            'away': away_odds_formatted
                        }
    return {}

def format_american_odds(decimal_odds):
    if decimal_odds == 1.0:
        return 'EVEN'
    elif decimal_odds > 2:
        underdog_odds = round(100 * (decimal_odds - 1))
        return f"+{underdog_odds}"
    else:
        favorite_odds = round(100 / (decimal_odds - 1))
        return f"-{favorite_odds}"