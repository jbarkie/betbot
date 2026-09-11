"""
Tests for inference-time starting pitcher lookup.

The controlling requirement is that a missing starter is an ordinary daily
occurrence, not an error: every path must yield all six features and never raise.
"""

import json
from datetime import date, datetime, timedelta

import pytest

from api.src import pitcher_lookup
from api.src.pitcher_lookup import (
    get_pitcher_medians,
    get_starting_pitcher_features,
    reset_caches,
    resolve_game_pk,
)
from api.src.ml_config import MLB_PITCHER_FEATURES


@pytest.fixture(autouse=True)
def clear_caches():
    reset_caches()
    yield
    reset_caches()


@pytest.fixture
def session():
    """In-memory SQLite session with the MLB tables created."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from shared.database import Base
    import machine_learning.data.models.mlb_models  # noqa: F401

    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    yield db
    db.close()


def _seed(session, game_id='770001', game_date=date(2026, 7, 1),
          home=139, away=138, pitcher_rows=()):
    from machine_learning.data.models.mlb_models import (
        MLBPitcherStats, MLBSchedule, MLBTeam,
    )

    for team_id in (home, away):
        if session.get(MLBTeam, team_id) is None:
            session.add(MLBTeam(id=team_id, name=f'Club {team_id}'))
    session.add(MLBSchedule(game_id=game_id, date=game_date, home_team_id=home,
                            away_team_id=away, status='Scheduled'))
    for team_id, era, whip, k9 in pitcher_rows:
        session.add(MLBPitcherStats(game_id=game_id, team_id=team_id, pitcher_id=1,
                                    pitcher_name='Someone', era=era, whip=whip, k9=k9))
    session.commit()


def _log(date_str, game_pk, started=1, ip='6.0', er=2, hits=5, bb=1, k=7):
    return {
        'date': date_str,
        'game': {'gamePk': game_pk},
        'team': {'id': 139},
        'stat': {'gamesStarted': started, 'inningsPitched': ip, 'earnedRuns': er,
                 'hits': hits, 'baseOnBalls': bb, 'strikeOuts': k},
    }


class _FakeCollector:
    def __init__(self, probables=None, logs=None, raises=False):
        self._probables = probables or {}
        self._logs = logs or {}
        self._raises = raises

    def get_probable_pitchers(self, game_id):
        if self._raises:
            raise RuntimeError("MLB API unreachable")
        return self._probables

    def get_game_log(self, pitcher_id, season):
        if self._raises:
            raise RuntimeError("MLB API unreachable")
        return self._logs.get(pitcher_id, [])


class TestResolveGamePk:
    """The Odds id is an opaque hash, so gamePk must come from matchup + date."""

    def test_finds_matching_scheduled_game(self, session):
        _seed(session)
        assert resolve_game_pk(session, 139, 138, date(2026, 7, 1)) == '770001'

    def test_accepts_datetime(self, session):
        _seed(session)
        assert resolve_game_pk(session, 139, 138, datetime(2026, 7, 1, 23, 5)) == '770001'

    def test_tolerates_one_day_drift_from_utc_times(self, session):
        """A late first pitch stored in UTC can land on the next calendar day."""
        _seed(session, game_date=date(2026, 7, 1))
        assert resolve_game_pk(session, 139, 138, date(2026, 7, 2)) == '770001'

    def test_home_and_away_not_interchangeable(self, session):
        _seed(session)
        assert resolve_game_pk(session, 138, 139, date(2026, 7, 1)) is None

    def test_unknown_matchup_returns_none(self, session):
        _seed(session)
        assert resolve_game_pk(session, 111, 112, date(2026, 7, 1)) is None

    def test_far_off_date_returns_none(self, session):
        _seed(session)
        assert resolve_game_pk(session, 139, 138, date(2026, 9, 1)) is None


class TestPitcherMedians:
    """Serving must impute with the values training used."""

    def test_reads_medians_from_model_metadata(self):
        medians = get_pitcher_medians()
        assert set(medians) == set(MLB_PITCHER_FEATURES)
        for value in medians.values():
            assert isinstance(value, float)

    def test_era_median_is_plausible(self):
        """Guards against reading the wrong metadata key and getting nonsense."""
        assert 2.0 < get_pitcher_medians()['home_starter_era'] < 7.0

    def test_falls_back_when_metadata_unreadable(self, monkeypatch, tmp_path):
        monkeypatch.setattr(pitcher_lookup, 'MLB_MODELS_DIR', tmp_path)
        reset_caches()
        medians = get_pitcher_medians()
        assert medians == pitcher_lookup._FALLBACK_MEDIANS

    def test_falls_back_when_metadata_lacks_medians(self, monkeypatch, tmp_path):
        (tmp_path / pitcher_lookup.MLB_MODEL_CONFIG['metadata_file']).write_text(
            json.dumps({'version': '1.0'})
        )
        monkeypatch.setattr(pitcher_lookup, 'MLB_MODELS_DIR', tmp_path)
        reset_caches()
        assert get_pitcher_medians() == pitcher_lookup._FALLBACK_MEDIANS


class TestGetStartingPitcherFeatures:
    """The six features are always present, whatever goes wrong upstream."""

    def test_uses_stored_rows_without_touching_the_network(self, session):
        _seed(session, pitcher_rows=[(139, 3.00, 1.10, 9.0), (138, 5.00, 1.50, 6.0)])
        collector = _FakeCollector(raises=True)  # any network use would blow up

        features = get_starting_pitcher_features(
            session, 139, 138, date(2026, 7, 1), collector=collector
        )

        assert features['home_starter_era'] == pytest.approx(3.00)
        assert features['away_starter_era'] == pytest.approx(5.00)
        assert features['home_starter_k9'] == pytest.approx(9.0)

    def test_falls_back_to_live_lookup_when_not_stored(self, session):
        _seed(session)
        collector = _FakeCollector(
            probables={139: {'pitcher_id': 500, 'pitcher_name': 'Ace'}},
            logs={500: [_log('2026-04-01', 1, ip='6.0', er=2, hits=5, bb=1, k=7),
                        _log('2026-04-08', 2, ip='6.0', er=2, hits=5, bb=1, k=7)]},
        )

        features = get_starting_pitcher_features(
            session, 139, 138, date(2026, 7, 1), collector=collector
        )

        # 4 ER over 12 IP = 3.00 ERA
        assert features['home_starter_era'] == pytest.approx(3.00)
        # No probable announced for the away side, so it keeps the median.
        assert features['away_starter_era'] == pytest.approx(
            get_pitcher_medians()['away_starter_era']
        )

    def test_live_lookup_excludes_starts_on_or_after_game_date(self, session):
        """A future start must not leak into the line for the game being predicted."""
        _seed(session, game_date=date(2026, 4, 10))
        collector = _FakeCollector(
            probables={139: {'pitcher_id': 500, 'pitcher_name': 'Ace'}},
            logs={500: [_log('2026-04-01', 1, ip='9.0', er=9, hits=9, bb=9, k=0),
                        _log('2026-04-10', 2, ip='9.0', er=0, hits=0, bb=0, k=27)]},
        )

        features = get_starting_pitcher_features(
            session, 139, 138, date(2026, 4, 10), collector=collector
        )

        # Only the first start counts: 9 ER over 9 IP.
        assert features['home_starter_era'] == pytest.approx(9.00)

    def test_unannounced_starter_yields_medians_not_an_error(self, session):
        _seed(session)
        features = get_starting_pitcher_features(
            session, 139, 138, date(2026, 7, 1), collector=_FakeCollector()
        )
        assert features == get_pitcher_medians()

    def test_api_failure_yields_medians_not_an_error(self, session):
        """An MLB API outage must degrade the prediction, never 500 the request."""
        _seed(session)
        features = get_starting_pitcher_features(
            session, 139, 138, date(2026, 7, 1), collector=_FakeCollector(raises=True)
        )
        assert features == get_pitcher_medians()

    def test_unresolvable_game_yields_medians(self, session):
        _seed(session)
        features = get_starting_pitcher_features(
            session, 111, 112, date(2026, 7, 1), collector=_FakeCollector()
        )
        assert features == get_pitcher_medians()

    def test_all_six_keys_always_present(self, session):
        _seed(session)
        for collector in (_FakeCollector(), _FakeCollector(raises=True)):
            features = get_starting_pitcher_features(
                session, 139, 138, date(2026, 7, 1), collector=collector
            )
            assert set(features) == set(MLB_PITCHER_FEATURES)
            assert all(isinstance(v, float) for v in features.values())
            reset_caches()

    def test_never_returns_zero_for_a_missing_starter(self, session):
        """Zero ERA would present an unknown pitcher as untouchable."""
        _seed(session)
        features = get_starting_pitcher_features(
            session, 139, 138, date(2026, 7, 1), collector=_FakeCollector()
        )
        assert all(v != 0 for v in features.values())

    def test_partial_stored_data_fills_the_gap_with_medians(self, session):
        """Home starter known, away not — away must not inherit the home value."""
        _seed(session, pitcher_rows=[(139, 2.00, 0.90, 11.0)])
        features = get_starting_pitcher_features(
            session, 139, 138, date(2026, 7, 1), collector=_FakeCollector()
        )
        assert features['home_starter_era'] == pytest.approx(2.00)
        assert features['away_starter_era'] == pytest.approx(
            get_pitcher_medians()['away_starter_era']
        )

    def test_result_is_cached_across_calls(self, session):
        _seed(session, pitcher_rows=[(139, 3.00, 1.10, 9.0)])

        first = get_starting_pitcher_features(
            session, 139, 138, date(2026, 7, 1), collector=_FakeCollector()
        )
        # A collector that raises would surface if the cache were bypassed.
        second = get_starting_pitcher_features(
            session, 139, 138, date(2026, 7, 1), collector=_FakeCollector(raises=True)
        )
        assert first == second

    def test_cache_distinguishes_different_games(self, session):
        _seed(session, game_id='770001', game_date=date(2026, 7, 1),
              pitcher_rows=[(139, 2.00, 0.90, 11.0)])
        _seed(session, game_id='770002', game_date=date(2026, 8, 20),
              home=200, away=201, pitcher_rows=[(200, 6.00, 1.70, 4.0)])

        a = get_starting_pitcher_features(session, 139, 138, date(2026, 7, 1),
                                          collector=_FakeCollector())
        b = get_starting_pitcher_features(session, 200, 201, date(2026, 8, 20),
                                          collector=_FakeCollector())
        assert a['home_starter_era'] == pytest.approx(2.00)
        assert b['home_starter_era'] == pytest.approx(6.00)
