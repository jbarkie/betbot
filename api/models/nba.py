from pydantic import BaseModel
from typing import Optional

class Game(BaseModel):
    id: str
    sport: str
    homeTeam: str
    awayTeam: str
    date: str
    time: str
    odds: dict

class GamesResponse(BaseModel):
    list: list[Game]
