"""Cancellable serving HTTP; historical collection keeps its synchronous client."""

import asyncio
import logging
import time

import httpx

from api.src.pitcher_telemetry import record_event

from machine_learning.data.collection.mlb_direct_api import MLBDirectAPI
from machine_learning.data.collection.mlb_pitcher_stats import (
    parse_pitching_game_log,
    parse_probable_pitchers,
)

logger = logging.getLogger(__name__)


class LivePitcherStatsCollector:
    def __init__(self, client: httpx.AsyncClient, *, lookup_id=None, game_id=None):
        self.client = client
        self.lookup_id = lookup_id
        self.game_id = game_id
        self.last_error = None

    async def _request(self, endpoint, params):
        started = time.perf_counter()
        outcome, status_code = 'error', None
        self.last_error = None
        try:
            response = await self.client.get(f"{MLBDirectAPI.BASE_URL}/{endpoint}", params=params)
            status_code = response.status_code
            response.raise_for_status()
            data = response.json()
            outcome = 'success'
            return data
        except asyncio.CancelledError:
            outcome = 'cancelled'
            raise
        except (httpx.HTTPError, ValueError) as exc:
            self.last_error = ('request_timeout' if isinstance(exc, httpx.TimeoutException)
                               else 'http_error' if isinstance(exc, httpx.HTTPError)
                               else 'invalid_response')
            outcome = self.last_error
            logger.warning("Live MLB request failed: %s", exc)
            return None
        finally:
            record_event(
                'pitcher_http_request', lookup_id=self.lookup_id, game_id=self.game_id,
                request_type='probable_pitchers' if endpoint == 'schedule' else 'game_log',
                pitcher_id=None if endpoint == 'schedule' else endpoint.split('/')[1],
                elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
                outcome=outcome, status_code=status_code,
            )

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
