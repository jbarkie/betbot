from pydantic import BaseModel
from typing import Optional, Dict

class TeamAnalytics(BaseModel):
    """Analytics for a single team"""
    name: str
    winning_percentage: float
    rolling_win_percentage: Optional[float] = None
    offensive_rating: Optional[float] = None
    defensive_rating: Optional[float] = None
    days_rest: Optional[int] = None
    momentum_score: Optional[float] = None

class MlbAnalyticsResponse(BaseModel):
    id: str
    home_team: str
    away_team: str
    predicted_winner: str
    win_probability: float
    
    # Enhanced analytics
    home_analytics: Optional[TeamAnalytics] = None
    away_analytics: Optional[TeamAnalytics] = None
    key_factors: Optional[Dict[str, str]] = None
    confidence_level: Optional[str] = None
