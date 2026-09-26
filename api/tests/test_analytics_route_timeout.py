"""
Sprint 8 review: a timing-out live pitcher lookup must still produce HTTP 200
with median pitcher values, proven through the real HTTP endpoint.

Everything between the route and the network is real: the FastAPI route, the
analytics body on its worker thread, the three-tier pitcher lookup, the
serving-path collector, and MLBDirectAPI's request handling. Only two things
are replaced: the socket-level HTTP call (forced to raise requests.Timeout) and
the trained model (a fake that records the features it was given, so the test
can see what the pitcher fallback produced).
"""

from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest
import requests
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.src import pitcher_lookup
from api.src.login import get_current_user
from api.src.main import app
from api.src.ml_config import MLB_PITCHER_FEATURES

GAME_TIME = datetime(2026, 7, 1, 19, 5)
HOME, AWAY = 139, 138


@pytest.fixture
def db():
    """In-memory database shared across threads, since the route runs on a worker."""
    from shared.database import Base
    import api.src.models.tables  # noqa: F401
    from api.src.models.tables import Odds
    from machine_learning.data.models.mlb_models import MLBSchedule, MLBTeam

    engine = create_engine(
        'sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    make_session = sessionmaker(bind=engine)

    seed = make_session()
    seed.add_all([
        MLBTeam(id=HOME, name='Tampa Bay Rays', wins=45, losses=38, games_played=83,
                winning_percentage=0.542),
        MLBTeam(id=AWAY, name='St. Louis Cardinals', wins=40, losses=43, games_played=83,
                winning_percentage=0.482),
        MLBSchedule(game_id='770001', date=date(2026, 7, 1), home_team_id=HOME,
                    away_team_id=AWAY, status='Scheduled'),
        Odds(id='odds-hash-1', sport='MLB', time=GAME_TIME, home_odds='-120',
             away_odds='+110', home_team='Tampa Bay Rays',
             away_team='St. Louis Cardinals', expires=GAME_TIME),
    ])
    seed.commit()
    seed.close()
    return make_session


@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = lambda: MagicMock(username='testuser')
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def clear_pitcher_caches():
    pitcher_lookup.reset_caches()
    yield
    pitcher_lookup.reset_caches()


def _recording_model_service(captured):
    service = MagicMock()
    service.is_available = True

    def predict(features):
        captured.update(features)
        return 'home', 0.62, {
            'ml_model_name': 'fake_v0',
            'model_confidence': 'Medium',
            'home_win_probability': 0.62,
            'away_win_probability': 0.38,
            'confidence_margin': 0.24,
            'feature_importance': None,
            'use_ml_prediction': True,
        }

    service.predict.side_effect = predict
    return service


def test_live_lookup_timeout_returns_200_with_median_pitcher_features(db, client):
    captured = {}
    socket_calls = []

    def timing_out_get(self, url, *args, **kwargs):
        socket_calls.append((url, kwargs.get('timeout')))
        raise requests.Timeout(f"{url} did not answer")

    with patch('api.src.enhanced_mlb_analytics.connect_to_db', side_effect=lambda: db()), \
         patch('api.src.enhanced_mlb_analytics.get_mlb_model_service',
               return_value=_recording_model_service(captured)), \
         patch.object(requests.Session, 'get', timing_out_get):
        response = client.get('/analytics/mlb/game?id=odds-hash-1')

    assert response.status_code == 200
    body = response.json()
    assert body['prediction_method'] == 'machine_learning'
    assert body['home_team'] == 'Tampa Bay Rays'

    # The live tier was genuinely attempted, over the network, with the
    # serving timeout, and it timed out.
    assert socket_calls, "the live pitcher lookup never reached the network"
    assert all(timeout == pitcher_lookup.SERVING_API_TIMEOUT_SECONDS for _, timeout in socket_calls)
    assert any('schedule' in url for url, _ in socket_calls)

    # The model received the training-time medians for all six pitcher features.
    medians = pitcher_lookup.get_pitcher_medians()
    assert set(MLB_PITCHER_FEATURES) <= set(captured)
    for name in MLB_PITCHER_FEATURES:
        assert captured[name] == medians[name], name
