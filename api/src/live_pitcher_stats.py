"""Cancellable serving HTTP; historical collection keeps its synchronous client."""

import logging

import httpx

from machine_learning.data.collection.mlb_direct_api import MLBDirectAPI
from machine_learning.data.collection.mlb_pitcher_stats import (
    parse_pitching_game_log,
    parse_probable_pitchers,
)

logger = logging.getLogger(__name__)


class LivePitcherStatsCollector:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def _request(self, endpoint, params):
        try:
            response = await self.client.get(f"{MLBDirectAPI.BASE_URL}/{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("Live MLB request failed: %s", exc)
            return None

    async def get_probable_pitchers(self, game_id):
        data = await self._request(
            'schedule', {'sportId': 1, 'gamePk': game_id, 'hydrate': 'probablePitcher'}
        )
        return parse_probable_pitchers(data, game_id)

    async def get_game_log(self, pitcher_id, season):
        data = await self._request(
            f'people/{pitcher_id}/stats',
            {'stats': 'gameLog', 'group': 'pitching', 'season': season},
        )
        return parse_pitching_game_log(data)
