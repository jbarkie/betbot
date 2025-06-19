from pydantic import BaseModel

class MlbAnalyticsResponse(BaseModel):
    id: str
    home_team: str
    away_team: str
    predicted_winner: str
    win_probability: float
