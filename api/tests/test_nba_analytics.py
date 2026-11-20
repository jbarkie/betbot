import asyncio
from datetime import date, datetime
from functools import partial

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from api.src import nba_analytics, nba_results
from api.src.login import get_current_user
from api.src.main import app
from api.src.models.tables import Odds


def _game(event_id, tip, home, away, home_score, away_score, *,
          status="STATUS_FINAL", season_type=2, neutral=False, headline=None):
    return {
        "id": event_id,
        "date": tip,
        "seasonType": {"type": season_type},
        "competitions": [{
            "status": {"type": {"name": status}},
            "neutralSite": neutral,
            "notes": [{"headline": headline}] if headline else [],
            "competitors": [
                {"team": {"abbreviation": home}, "homeAway": "home", "score": {"value": home_score}},
                {"team": {"abbreviation": away}, "homeAway": "away", "score": {"value": away_score}},
            ],
        }],
    }


@pytest.fixture
def espn(monkeypatch):
    boston = [_game("1", "2026-11-01T20:00Z", "BOS", "PHI", 90, 110)]
    boston.extend(
        _game(str(day), f"2026-11-{day:02}T20:00Z", "BOS", "PHI", 110, 100, neutral=day == 2)
        for day in range(2, 11)
    )
    head_to_head = _game("h2h", "2026-11-18T01:00Z", "LAL", "BOS", 110, 105)
    schedules = {
        "bos": [
            *reversed(boston), boston[2], head_to_head,
            _game("same-day", "2026-11-19T01:00Z", "BOS", "LAL", 140, 90),
            _game("later", "2026-11-20T01:00Z", "BOS", "PHI", 140, 90),
            _game("live", "2026-11-16T20:00Z", "BOS", "PHI", 120, 80, status="STATUS_IN_PROGRESS"),
            _game("preseason", "2026-10-15T20:00Z", "BOS", "PHI", 120, 80, season_type=1),
            _game("cup", "2026-11-15T20:00Z", "BOS", "LAL", 120, 80, headline="NBA Cup Championship"),
        ],
        "lal": [head_to_head, _game("road", "2026-11-13T20:00Z", "GS", "LAL", 110, 100)],
    }
    requests = []

    def scoreboard(request):
        team = request.url.path.split("/")[-2]
        assert request.url.params["season"] == "2027"
        assert request.url.params["seasontype"] == "2"
        requests.append(team)
        if team not in schedules:
            return httpx.Response(503)
        return httpx.Response(200, json={
            "requestedSeason": {"year": 2027, "type": 2},
            "team": {"abbreviation": team.upper()},
            "events": schedules[team],
        })

    monkeypatch.setattr(nba_results, "_cache", {})
    monkeypatch.setattr(nba_results.httpx, "AsyncClient",
                        partial(httpx.AsyncClient, transport=httpx.MockTransport(scoreboard)))
    return schedules, requests


@pytest.fixture
def nba_client(monkeypatch, espn):
    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    Odds.__table__.create(engine)
    monkeypatch.setattr(nba_analytics, "connect_to_db", lambda: Session(engine))
    monkeypatch.setitem(app.dependency_overrides, get_current_user, lambda: None)

    def request(home_odds, away_odds, sport="NBA", game_id="odds-1"):
        with Session(engine) as session:
            session.merge(Odds(
                id="odds-1", sport=sport, home_team="Boston Celtics",
                away_team="Los Angeles Lakers", home_odds=home_odds, away_odds=away_odds,
                time=datetime(2026, 11, 18, 19),
            ))
            session.commit()
        with TestClient(app) as client:
            return client.get("/analytics/nba/game", params={"id": game_id})

    yield request
    engine.dispose()


@pytest.mark.parametrize(
    "home_odds, away_odds, winner, home_probability",
    [
        ("-150", "+130", "Boston Celtics", 69 / 119),
        ("+130", "-150", "Los Angeles Lakers", 50 / 119),
        ("-110", "-110", None, 0.5),
    ],
)
def test_nba_market_analytics(nba_client, home_odds, away_odds, winner, home_probability):
    response = nba_client(home_odds, away_odds)

    assert response.status_code == 200
    body = response.json()
    assert body["predicted_winner"] == winner
    assert body["prediction_method"] == "market_implied"
    assert body["home_win_probability"] == pytest.approx(home_probability)
    assert body["away_win_probability"] == pytest.approx(1 - home_probability)
    assert body["win_probability"] == pytest.approx(max(home_probability, 1 - home_probability))


@pytest.mark.parametrize("home_odds, away_odds", [(None, "+130"), ("-150", "--100")])
def test_nba_form_is_available_without_two_valid_prices(nba_client, home_odds, away_odds):
    response = nba_client(home_odds, away_odds)
    assert response.status_code == 200
    body = response.json()
    assert body["home_win_probability"] is None
    assert body["away_win_probability"] is None
    assert body["team_comparison"]["home"]["season_record"] == {"wins": 9, "losses": 2}


def test_nba_team_comparison_uses_prior_regular_season_finals(nba_client):
    comparison = nba_client("-150", "+130").json()["team_comparison"]
    assert comparison["before"] == "2026-11-18"
    home, away = comparison["home"], comparison["away"]
    assert home["season_record"] == {"wins": 9, "losses": 2}
    assert home["recent_record"] == {"wins": 9, "losses": 1}
    assert home["venue_record"] == {"wins": 8, "losses": 1}
    assert home["head_to_head_record"] == {"wins": 0, "losses": 1}
    assert home["season_margin"] == pytest.approx(65 / 11)
    assert home["recent_margin"] == 8.5
    assert home["latest_result"] == "2026-11-17"
    assert away["venue_record"] == {"wins": 0, "losses": 1}
    assert away["head_to_head_record"] == {"wins": 1, "losses": 0}
    assert away["recent_margin"] == -2.5


@pytest.mark.parametrize("tip, incomplete", [
    ("2026-11-18T01:30Z", True),   # Nov 17 Eastern, before the matchup date.
    ("2026-11-19T01:30Z", False),  # Nov 18 Eastern, on the matchup date.
])
def test_nba_tied_final_preserves_valid_results(nba_client, espn, tip, incomplete):
    schedules, _ = espn
    schedules["bos"].append(_game("bad-final", tip, "BOS", "PHI", 100, 100))

    response = nba_client("-150", "+130")
    assert response.status_code == 200
    home = response.json()["team_comparison"]["home"]
    assert home["season_record"] == {"wins": 9, "losses": 2}
    assert home["season_margin"] == pytest.approx(65 / 11)
    assert home["incomplete"] is incomplete
    assert response.json()["team_comparison"]["away"]["incomplete"] is False


def test_nba_source_failure_preserves_market(nba_client, espn):
    schedules, _ = espn
    del schedules["bos"]
    response = nba_client("-150", "+130")
    assert response.status_code == 200
    assert response.json()["team_comparison"] is None
    assert response.json()["home_win_probability"] == pytest.approx(69 / 119)


def test_nba_schedule_is_reused_for_repeat_analyses(nba_client, espn):
    _, requests = espn
    first = nba_client("-150", "+130").json()
    second = nba_client("-150", "+130").json()
    assert second["team_comparison"] == first["team_comparison"]
    assert sorted(requests) == ["bos", "lal"]


@pytest.mark.parametrize("cancel_first", [False, True])
async def test_concurrent_matchups_share_team_fetch(monkeypatch, cancel_first):
    boston_started, other_matchup_started, release_boston = (asyncio.Event() for _ in range(3))
    requests = []

    async def scoreboard(request):
        team = request.url.path.split("/")[-2]
        requests.append(team)
        events = []
        if team == "bos":
            boston_started.set()
            await release_boston.wait()
            events = [_game("result", "2026-11-17T20:00Z", "BOS", "NY", 110, 100)]
        elif team == "gs":
            other_matchup_started.set()
        return httpx.Response(200, json={
            "requestedSeason": {"year": 2027, "type": 2},
            "team": {"abbreviation": team.upper()},
            "events": events,
        })

    monkeypatch.setattr(nba_results, "_cache", {})
    monkeypatch.setattr(nba_results.httpx, "AsyncClient",
                        partial(httpx.AsyncClient, transport=httpx.MockTransport(scoreboard)))

    matchup_date = date(2026, 11, 18)
    first = asyncio.create_task(nba_results.get_nba_team_comparison(
        "Boston Celtics", "Los Angeles Lakers", matchup_date,
    ))
    try:
        await asyncio.wait_for(boston_started.wait(), timeout=2)
        second = asyncio.create_task(nba_results.get_nba_team_comparison(
            "Boston Celtics", "Golden State Warriors", matchup_date,
        ))
        # The second matchup's other team can reach ESPN while Boston is in flight.
        await asyncio.wait_for(other_matchup_started.wait(), timeout=2)
        if cancel_first:
            first.cancel()
            with pytest.raises(asyncio.CancelledError):
                await first
    finally:
        release_boston.set()

    comparison = await second
    assert comparison.home.season_record.wins == 1
    if not cancel_first:
        assert (await first).home == comparison.home
    assert sorted(requests) == ["bos", "gs", "lal"]


@pytest.mark.parametrize("sport, game_id", [("MLB", "odds-1"), ("NBA", "unknown")])
def test_nba_analytics_only_finds_matching_nba_game(nba_client, sport, game_id):
    assert nba_client("-150", "+130", sport, game_id).status_code == 404


def test_nba_analytics_requires_authentication():
    with TestClient(app) as client:
        assert client.get("/analytics/nba/game?id=odds-1").status_code == 401
