from pydantic import BaseModel
from typing import Optional

class Game(BaseModel):
    id: str
    homeTeam: str
    awayTeam: str
    date: str
    time: str
    odds: Optional[list[str]] = ['+110', '-110']
