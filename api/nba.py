from nba_api.live.nba.endpoints import scoreboard
from models.nba import Game
from models.nba import GamesResponse
from dateutil import parser
from datetime import timezone

board = scoreboard.ScoreBoard()
date = board.score_board_date
games = board.games.get_dict()

def get_todays_games():
    response_list = []
    for game in games:
        homeTeam = game['homeTeam']
        awayTeam = game['awayTeam']
        response_list.append(Game(
            id=game['gameId'],
            sport='NBA',
            homeTeam=homeTeam['teamCity'] + ' ' + homeTeam['teamName'],
            awayTeam=awayTeam['teamCity'] + ' ' + awayTeam['teamName'],
            date=date,
            time=parser.parse(game["gameTimeUTC"]).replace(tzinfo=timezone.utc).astimezone(tz=None).strftime("%H:%M"),
            odds='+110, -110'
        ))
    return GamesResponse(list=response_list)
        