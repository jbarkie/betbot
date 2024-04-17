from pydantic import BaseModel

class Game(BaseModel):
    id: str
    sport: str
    homeTeam: str
    awayTeam: str
    time: str
    homeOdds: str
    awayOdds: str

class GamesResponse(BaseModel):
    list: list[Game]
