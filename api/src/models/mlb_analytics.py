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

    # ML Model fields
    ml_model_name: Optional[str] = None
    ml_confidence: Optional[str] = None
    home_win_probability: Optional[float] = None
    away_win_probability: Optional[float] = None
    prediction_method: Optional[str] = None  # "machine_learning" or "rule_based"
    feature_importance: Optional[Dict[str, float]] = None

class ModelInfoResponse(BaseModel):
    """Response model for /analytics/mlb/model-info endpoint"""
    ml_model_name: str
    ml_model_type: str
    version: str
    trained_date: str
    is_loaded: bool
    is_available: bool
    metrics: Optional[Dict] = None
    features_count: Optional[int] = None
    error: Optional[str] = None
