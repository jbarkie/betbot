"""The total serving budget cancels live I/O, including trickling responses."""

import asyncio
from datetime import date
from unittest.mock import patch

import httpx
import pytest

from api.src import pitcher_lookup


async def test_budget_cancels_stalled_lookup_and_starts_no_more_requests(monkeypatch):
    cancelled = asyncio.Event()

    class Collector:
        async def get_probable_pitchers(self, game_id):
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()

        async def get_game_log(self, *args):
            pytest.fail('No game log should start after the deadline')

    monkeypatch.setattr(pitcher_lookup, 'LIVE_LOOKUP_BUDGET_SECONDS', 0.05)
    result = await asyncio.wait_for(
        pitcher_lookup._live_stats_async('1', date(2026, 7, 1), Collector()), 5
    )
    assert result == {}
    assert cancelled.is_set()


async def test_budget_preserves_completed_side_and_cancels_second_log(monkeypatch):
    cancelled = asyncio.Event()

    class Collector:
        async def get_probable_pitchers(self, game_id):
            return {139: {'pitcher_id': 1}, 138: {'pitcher_id': 2}}

        async def get_game_log(self, pitcher_id, season):
            if pitcher_id == 1:
                return [{'date': '2026-06-01', 'stat': {
                    'gamesStarted': 1, 'inningsPitched': '6.0', 'earnedRuns': 2,
                    'hits': 5, 'baseOnBalls': 1, 'strikeOuts': 6,
                }}]
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()

    monkeypatch.setattr(pitcher_lookup, 'LIVE_LOOKUP_BUDGET_SECONDS', 0.05)
    result = await asyncio.wait_for(
        pitcher_lookup._live_stats_async('1', date(2026, 7, 1), Collector()), 5
    )
    assert result == {139: {'era': 3.0, 'whip': 1.0, 'k9': 9.0}}
    assert cancelled.is_set()


async def test_trickling_response_is_closed_at_total_budget(monkeypatch):
    closed = asyncio.Event()
    chunks = []

    class Trickle(httpx.AsyncByteStream):
        async def __aiter__(self):
            while True:
                chunks.append(b' ')
                yield b' '
                await asyncio.sleep(0.005)

        async def aclose(self):
            closed.set()

    client = httpx.AsyncClient(transport=httpx.MockTransport(
        lambda request: httpx.Response(200, stream=Trickle())
    ))
    monkeypatch.setattr(pitcher_lookup, 'LIVE_LOOKUP_BUDGET_SECONDS', 0.05)
    with patch('httpx.AsyncClient', return_value=client):
        result = await asyncio.wait_for(
            pitcher_lookup._live_stats_async('1', date(2026, 7, 1)), 5
        )
    assert result == {}
    assert chunks
    assert closed.is_set()
    assert client.is_closed


async def test_successful_http_lookup_parses_both_sides_and_closes_client():
    paths = []

    def respond(request):
        paths.append(request.url.path)
        if request.url.path.endswith('/schedule'):
            return httpx.Response(200, json={'dates': [{'games': [{
                'gamePk': 1, 'teams': {
                    'home': {'team': {'id': 139}, 'probablePitcher': {'id': 10}},
                    'away': {'team': {'id': 138}, 'probablePitcher': {'id': 20}},
                },
            }]}]})
        assert request.url.params['season'] == '2026'
        return httpx.Response(200, json={'stats': [{
            'type': {'displayName': 'gameLog'}, 'splits': [{
                'date': '2026-06-01', 'stat': {
                    'gamesStarted': 1, 'inningsPitched': '6.0', 'earnedRuns': 2,
                    'hits': 5, 'baseOnBalls': 1, 'strikeOuts': 6,
                },
            }],
        }]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    with patch('httpx.AsyncClient', return_value=client):
        result = await pitcher_lookup._live_stats_async('1', date(2026, 7, 1))
    assert result == {team: {'era': 3.0, 'whip': 1.0, 'k9': 9.0} for team in (139, 138)}
    assert len(paths) == 3
    assert client.is_closed
