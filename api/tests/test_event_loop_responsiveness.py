"""
Sprint 8 Card 1 (#44): slow external calls must not block the event loop.

The analytics and games routes wrap synchronous work (DB sessions, the Odds
API, the MLB Stats API) in asyncio.to_thread. These tests hold that work open
on a threading.Event and check that an unrelated coroutine on the same loop
still completes. Each test has a generous safety timeout and no sub-second
timing assertion, so a slow CI runner cannot turn them flaky.
"""

import asyncio
import threading
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
import requests
from fastapi import HTTPException

from api.src import games
from api.src.enhanced_mlb_analytics import EnhancedMLBAnalytics
from api.src.games import (
    ODDS_API_TIMEOUT_DETAIL,
    ODDS_API_TIMEOUT_SECONDS,
    call_odds_api,
    get_games_for_sport,
)
from api.src.models.games import GamesResponse

SAFETY_TIMEOUT = 10


class _Gate:
    """A blocking stub that records which thread ran it and waits to be released."""

    def __init__(self):
        self.release = threading.Event()
        self.entered = threading.Event()
        self.thread_was_main = None

    def block(self, *args, **kwargs):
        self.thread_was_main = threading.current_thread() is threading.main_thread()
        self.entered.set()
        self.release.wait(SAFETY_TIMEOUT)


async def _unrelated_work():
    """Stand-in for another request being served on the same loop."""
    await asyncio.sleep(0)
    return "done"


async def _assert_loop_stays_free(gate, route_coro):
    task = asyncio.create_task(route_coro)

    # Wait until the blocking stub has actually started on its worker thread.
    await asyncio.wait_for(asyncio.to_thread(gate.entered.wait, SAFETY_TIMEOUT), SAFETY_TIMEOUT)
    assert gate.entered.is_set()

    # The route is still held open; unrelated work must still complete.
    result = await asyncio.wait_for(_unrelated_work(), SAFETY_TIMEOUT)
    assert result == "done"
    assert not task.done(), "route finished before its external call was released"
    assert gate.thread_was_main is False, "blocking work ran on the event loop thread"

    gate.release.set()
    return task


class TestGamesRouteResponsiveness:

    async def test_unrelated_coroutine_completes_while_odds_lookup_is_blocked(self):
        gate = _Gate()

        def blocked_lookup(*args, **kwargs):
            gate.block()
            return GamesResponse(list=[])

        with patch("api.src.games.get_games_by_date", side_effect=blocked_lookup):
            task = await _assert_loop_stays_free(
                gate, get_games_for_sport("2026-07-01", "MLB", "baseball_mlb")
            )
            response = await asyncio.wait_for(task, SAFETY_TIMEOUT)

        assert response.list == []

    async def test_odds_timeout_maps_to_504(self):
        with patch("api.src.games.get_games_by_date", side_effect=requests.Timeout("slow upstream")):
            with pytest.raises(HTTPException) as exc_info:
                await get_games_for_sport("2026-07-01", "MLB", "baseball_mlb")

        assert exc_info.value.status_code == 504
        assert "timed out" in exc_info.value.detail
        assert exc_info.value.detail == ODDS_API_TIMEOUT_DETAIL

    def test_call_odds_api_passes_explicit_timeout(self):
        fake = MagicMock()
        fake.json.return_value = []
        with patch("api.src.games.requests.get", return_value=fake) as mock_get:
            call_odds_api("baseball_mlb")

        assert mock_get.call_args.kwargs["timeout"] == ODDS_API_TIMEOUT_SECONDS
        connect, read = ODDS_API_TIMEOUT_SECONDS
        assert connect > 0 and read > 0

    async def test_invalid_date_is_still_400_before_any_blocking_work(self):
        with patch("api.src.games.get_games_by_date") as lookup:
            with pytest.raises(HTTPException) as exc_info:
                await get_games_for_sport("not-a-date", "MLB", "baseball_mlb")
        assert exc_info.value.status_code == 400
        lookup.assert_not_called()


class TestAnalyticsRouteResponsiveness:

    async def test_unrelated_coroutine_completes_while_analytics_db_work_is_blocked(self):
        gate = _Gate()
        service = EnhancedMLBAnalytics()

        def blocked_connect(*args, **kwargs):
            gate.block()
            session = MagicMock()
            session.query.return_value.filter_by.return_value.first.return_value = None
            return session

        with patch("api.src.enhanced_mlb_analytics.connect_to_db", side_effect=blocked_connect):
            task = await _assert_loop_stays_free(gate, service.get_enhanced_game_analytics("game-1"))
            with pytest.raises(ValueError, match="not found"):
                await asyncio.wait_for(task, SAFETY_TIMEOUT)

    async def test_session_is_opened_and_closed_on_the_worker_thread(self):
        """DB sessions must never be shared with the event loop thread."""
        service = EnhancedMLBAnalytics()
        threads = {}
        session = MagicMock()
        session.query.return_value.filter_by.return_value.first.return_value = None
        session.close.side_effect = lambda: threads.__setitem__("close", threading.current_thread())

        def connect(*args, **kwargs):
            threads["open"] = threading.current_thread()
            return session

        with patch("api.src.enhanced_mlb_analytics.connect_to_db", side_effect=connect):
            with pytest.raises(ValueError):
                await service.get_enhanced_game_analytics("game-1")

        assert threads["open"] is threads["close"]
        assert threads["open"] is not threading.main_thread()
        session.close.assert_called_once()
