from api.src.models.mlb_analytics import MlbAnalyticsResponse


async def get_mlb_game_analytics(game_id: str):
    return MlbAnalyticsResponse(id=game_id)