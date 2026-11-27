from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel


class NbaRecord(BaseModel):
    wins: int
    losses: int


class NbaTeamResults(BaseModel):
    season_record: NbaRecord
    recent_record: NbaRecord
    venue_record: NbaRecord
    head_to_head_record: NbaRecord
    season_margin: Optional[float]
    recent_margin: Optional[float]
    latest_result: Optional[date]
    incomplete: bool


class NbaTeamComparison(BaseModel):
    before: date
    home: NbaTeamResults
    away: NbaTeamResults


class NbaAnalyticsResponse(BaseModel):
    id: str
    home_team: str
    away_team: str
    predicted_winner: Optional[str] = None
    win_probability: Optional[float] = None
    home_win_probability: Optional[float] = None
    away_win_probability: Optional[float] = None
    prediction_method: Literal["market_implied"] = "market_implied"
    key_factors: Optional[dict[str, str]] = None
    team_comparison: Optional[NbaTeamComparison] = None
