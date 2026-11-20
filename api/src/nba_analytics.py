import asyncio
import re
from typing import Optional

from fastapi import HTTPException

from api.src.models.nba_analytics import NbaAnalyticsResponse
from api.src.models.tables import Odds
from api.src.nba_results import get_nba_team_comparison
from shared.database import connect_to_db


def _implied_probability(moneyline: Optional[str]) -> Optional[float]:
    # The odds cache stores signed American prices, or a missing-price sentinel.
    if not re.fullmatch(r"[+-][1-9][0-9]{2,}", moneyline or ""):
        return None
    price = int(moneyline)
    return 100 / (price + 100) if price > 0 else -price / (100 - price)


def _read_game(game_id: str) -> Odds:
    with connect_to_db() as session:
        game = session.query(Odds).filter_by(id=game_id, sport="NBA").one_or_none()
        if game is None:
            raise HTTPException(status_code=404, detail="NBA game not found")
        return game


async def get_nba_game_analytics(game_id: str) -> NbaAnalyticsResponse:
    game = await asyncio.to_thread(_read_game, game_id)
    comparison = (
        await get_nba_team_comparison(game.home_team, game.away_team, game.time.date())
        if game.time is not None else None
    )

    analytics = NbaAnalyticsResponse(
        id=game.id, home_team=game.home_team, away_team=game.away_team, team_comparison=comparison,
    )

    home_implied = _implied_probability(game.home_odds)
    away_implied = _implied_probability(game.away_odds)
    if home_implied is None or away_implied is None:
        return analytics

    # Normalize the two break-even probabilities to remove the quoted overround.
    total = home_implied + away_implied
    analytics.home_win_probability = home_implied / total
    analytics.away_win_probability = away_implied / total
    analytics.win_probability = max(home_implied, away_implied) / total
    if home_implied > away_implied:
        analytics.predicted_winner = game.home_team
    elif away_implied > home_implied:
        analytics.predicted_winner = game.away_team

    analytics.key_factors = {
        "moneylines": f"Cached FanDuel moneylines: {game.away_team} {game.away_odds}, "
                      f"{game.home_team} {game.home_odds}.",
        "method": "Probabilities are normalized to 100%; this is not an independent prediction.",
    }
    return analytics
