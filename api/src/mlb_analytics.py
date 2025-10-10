from api.src.models.mlb_analytics import MlbAnalyticsResponse
from api.src.enhanced_mlb_analytics import get_enhanced_mlb_game_analytics


async def get_mlb_game_analytics(game_id: str):
    """
    Get MLB game analytics using the enhanced analytics service.
    
    This function now uses sophisticated machine learning insights including:
    - Rolling statistics and momentum analysis
    - Offensive and defensive ratings
    - Rest advantage calculations
    - Head-to-head historical performance
    
    Args:
        game_id: ID of the game to analyze
        
    Returns:
        Enhanced MlbAnalyticsResponse with detailed insights
    """
    return await get_enhanced_mlb_game_analytics(game_id)