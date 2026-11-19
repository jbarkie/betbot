import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from api.src import nba_analytics
from api.src.login import get_current_user
from api.src.main import app
from api.src.models.tables import Odds


@pytest.fixture
def nba_client(monkeypatch):
    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    Odds.__table__.create(engine)
    monkeypatch.setattr(nba_analytics, "connect_to_db", lambda: Session(engine))
    monkeypatch.setitem(app.dependency_overrides, get_current_user, lambda: None)

    def request(home_odds, away_odds, sport="NBA", game_id="odds-1"):
        with Session(engine) as session:
            session.add(Odds(
                id="odds-1", sport=sport, home_team="Boston Celtics",
                away_team="Los Angeles Lakers", home_odds=home_odds, away_odds=away_odds,
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
def test_nba_analytics_requires_two_valid_prices(nba_client, home_odds, away_odds):
    assert nba_client(home_odds, away_odds).status_code == 409


@pytest.mark.parametrize("sport, game_id", [("MLB", "odds-1"), ("NBA", "unknown")])
def test_nba_analytics_only_finds_matching_nba_game(nba_client, sport, game_id):
    assert nba_client("-150", "+130", sport, game_id).status_code == 404


def test_nba_analytics_requires_authentication():
    with TestClient(app) as client:
        assert client.get("/analytics/nba/game?id=odds-1").status_code == 401
