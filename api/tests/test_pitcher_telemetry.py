"""Telemetry measures real attempts separately from cached fallback exposure."""

import asyncio
import json
from datetime import date
from unittest.mock import patch

import httpx
import pytest

from api.src import pitcher_lookup
from api.src.pitcher_telemetry import logger
from api.tests.test_pitcher_lookup import _FakeCollector, _log, _seed, session


@pytest.fixture(autouse=True)
def events(caplog):
    pitcher_lookup.reset_caches()
    logger.addHandler(caplog.handler)
    yield lambda event: [json.loads(r.getMessage()) for r in caplog.records
                         if r.name == logger.name and json.loads(r.getMessage())['event'] == event]
    logger.removeHandler(caplog.handler)
    pitcher_lookup.reset_caches()


def test_feature_sources_and_cache_keep_original_fallback_reason(session, events):
    _seed(session, pitcher_rows=[(139, 3.0, 1.1, 9.0)])
    for _ in range(2):
        pitcher_lookup.get_starting_pitcher_features(
            session, 139, 138, date(2026, 7, 1), collector=_FakeCollector()
        )
    first, cached = events('pitcher_features')
    assert first['home']['sources'] == dict.fromkeys(('era', 'whip', 'k9'), 'stored')
    assert first['home']['fallback_reason'] is None
    assert first['away']['fallback_reason'] == 'starter_not_announced'
    assert first['live_attempted'] and not first['cache_hit']
    assert cached['cache_hit'] and not cached['live_attempted']
    assert cached['cache_age_seconds'] >= 0
    assert cached['away'] == first['away']
    assert cached['origin_lookup_id'] == first['lookup_id']
    assert cached['lookup_id'] != first['lookup_id']
    assert len(events('pitcher_live_lookup')) == 1


def test_live_sources_and_unresolved_game_are_logged(session, events):
    _seed(session)
    pitcher_lookup.get_starting_pitcher_features(
        session, 139, 138, date(2026, 7, 1), collector=_FakeCollector(
            probables={139: {'pitcher_id': 1}}, logs={1: [_log('2026-06-01', 1)]}
        )
    )
    assert events('pitcher_features')[0]['home']['sources']['era'] == 'live'
    pitcher_lookup.get_starting_pitcher_features(session, 111, 112, date(2026, 7, 1))
    unresolved = events('pitcher_features')[-1]
    assert not unresolved['live_attempted']
    assert unresolved['home']['fallback_reason'] == 'game_not_resolved'


def test_partial_completion_at_deadline_preserves_live_side_and_logs_reason(session, monkeypatch, events):
    _seed(session)

    class Partial(_FakeCollector):
        async def get_game_log(self, pitcher_id, season):
            if pitcher_id == 1:
                return [_log('2026-06-01', 1)]
            await asyncio.Event().wait()

    monkeypatch.setattr(pitcher_lookup, 'LIVE_LOOKUP_BUDGET_SECONDS', 0.02)
    pitcher_lookup.get_starting_pitcher_features(
        session, 139, 138, date(2026, 7, 1), collector=Partial(
            probables={139: {'pitcher_id': 1}, 138: {'pitcher_id': 2}}
        )
    )
    lookup, = events('pitcher_live_lookup')
    features, = events('pitcher_features')
    assert lookup['outcome'] == 'budget_exhausted'
    assert lookup['resolved_team_ids'] == [139]
    assert lookup['stage'] == 'game_log' and lookup['active_team_id'] == 138
    assert lookup['elapsed_ms'] >= lookup['budget_ms']
    assert features['home']['sources']['era'] == 'live'
    assert features['away']['fallback_reason'] == 'budget_exhausted'
    assert lookup['lookup_id'] == features['lookup_id']


@pytest.mark.parametrize('failure,reason', [('http', 'http_error'), ('timeout', 'request_timeout')])
def test_upstream_failure_is_not_reported_as_unannounced(session, events, failure, reason):
    _seed(session)

    def respond(request):
        if failure == 'timeout':
            raise httpx.ReadTimeout('timed out', request=request)
        return httpx.Response(503)

    client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    with patch('httpx.AsyncClient', return_value=client):
        pitcher_lookup.get_starting_pitcher_features(session, 139, 138, date(2026, 7, 1))
    request, = events('pitcher_http_request')
    lookup, = events('pitcher_live_lookup')
    features, = events('pitcher_features')
    assert request['outcome'] == reason
    assert request['elapsed_ms'] >= 0
    assert lookup['outcome'] == 'upstream_error'
    assert features['home']['fallback_reason'] == reason
    assert request['lookup_id'] == lookup['lookup_id'] == features['lookup_id']


async def test_cancelled_http_request_is_timed_and_closed(monkeypatch, events):
    closed = asyncio.Event()

    class Stall(httpx.AsyncByteStream):
        async def __aiter__(self):
            await asyncio.Event().wait()
            yield b''

        async def aclose(self):
            closed.set()

    client = httpx.AsyncClient(transport=httpx.MockTransport(
        lambda request: httpx.Response(200, stream=Stall())
    ))
    monkeypatch.setattr(pitcher_lookup, 'LIVE_LOOKUP_BUDGET_SECONDS', 0.02)
    with patch('httpx.AsyncClient', return_value=client):
        await pitcher_lookup._live_stats_async('1', date(2026, 7, 1))
    request, = events('pitcher_http_request')
    assert request['outcome'] == 'cancelled'
    assert request['request_type'] == 'probable_pitchers'
    assert request['elapsed_ms'] >= 20
    assert closed.is_set() and client.is_closed


def test_stored_only_features_do_not_create_a_live_attempt(session, events):
    _seed(session, pitcher_rows=[(139, 3.0, 1.1, 9.0), (138, 4.0, 1.3, 8.0)])
    pitcher_lookup.get_starting_pitcher_features(session, 139, 138, date(2026, 7, 1))
    features, = events('pitcher_features')
    assert not features['live_attempted']
    assert not events('pitcher_live_lookup')
    assert not events('pitcher_http_request')
    assert features['home']['fallback_reason'] is features['away']['fallback_reason'] is None


async def test_successful_requests_are_all_counted_and_linked(events):
    def respond(request):
        if request.url.path.endswith('/schedule'):
            return httpx.Response(200, json={'dates': [{'games': [{
                'gamePk': 1, 'teams': {
                    'home': {'team': {'id': 139}, 'probablePitcher': {'id': 10}},
                    'away': {'team': {'id': 138}, 'probablePitcher': {'id': 20}},
                },
            }]}]})
        return httpx.Response(200, json={'stats': [{
            'type': {'displayName': 'gameLog'}, 'splits': [_log('2026-06-01', 1)],
        }]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(respond))
    with patch('httpx.AsyncClient', return_value=client):
        await pitcher_lookup._live_stats_async('1', date(2026, 7, 1))
    requests = events('pitcher_http_request')
    lookup, = events('pitcher_live_lookup')
    assert len(requests) == 3
    assert [r['request_type'] for r in requests] == ['probable_pitchers', 'game_log', 'game_log']
    assert all(r['outcome'] == 'success' and r['status_code'] == 200 for r in requests)
    assert all(r['lookup_id'] == lookup['lookup_id'] for r in requests)
    assert lookup['outcome'] == 'completed' and lookup['resolved_team_ids'] == [138, 139]
