from typing import Literal, Optional

from pydantic import BaseModel


class NbaAnalyticsResponse(BaseModel):
    id: str
    home_team: str
    away_team: str
    predicted_winner: Optional[str]
    win_probability: float
    home_win_probability: float
    away_win_probability: float
    prediction_method: Literal["market_implied"] = "market_implied"
    key_factors: dict[str, str]
