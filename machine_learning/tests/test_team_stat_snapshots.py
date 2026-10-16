"""Team-stat snapshots are cumulative per season and used only from strictly earlier dates (#52)."""

from datetime import date, datetime
from unittest.mock import MagicMock

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.src.enhanced_mlb_analytics import EnhancedMLBAnalytics
from machine_learning.analysis.mlb_feature_engineering import GameFeatureGenerator
from machine_learning.data.collection.mlb_direct_api import (
    MLBDirectAPI, fetch_team_stats_direct, season_start_date,
)
from machine_learning.data.models.mlb_models import (
    MLBTeam, MLBSchedule, MLBOffensiveStats, MLBDefensiveStats,
)
from shared.database import Base


@pytest.fixture
def db():
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add_all([MLBTeam(id=1, name='A'), MLBTeam(id=2, name='B')])
    session.commit()
    yield session
    session.close()
    engine.dispose()


def test_season_start_is_january_first_of_the_snapshot_year():
    assert season_start_date(date(2025, 9, 2)) == '2025-01-01'
    assert season_start_date(datetime(2026, 4, 1, 19, 5)) == '2026-01-01'


@pytest.mark.parametrize('method,group', [('get_team_hitting_stats', 'hitting'), ('get_team_pitching_stats', 'pitching')])
def test_requests_ask_for_regular_season_only(method, group):
    client = MLBDirectAPI()
    from unittest.mock import patch
    with patch.object(client, '_make_request') as request:
        getattr(client, method)(139, '2025-01-01', '2025-09-02')
    params = request.call_args.args[1]
    assert params['gameType'] == 'R' and params['group'] == group
    client.session.close()


def test_collector_starts_every_request_at_season_start_not_window_start(db):
    for day in (date(2025, 9, 1), date(2025, 9, 2)):
        db.add(MLBSchedule(game_id=str(day), date=day, home_team_id=1, away_team_id=2,
                           status='Final', home_score=3, away_score=2))
    db.commit()
    client = MagicMock()
    client.get_team_hitting_stats.return_value = {'stats': ['x']}
    client.get_team_pitching_stats.return_value = {'stats': ['x']}
    client.extract_hitting_stats.return_value = {'avg': '.250'}
    client.extract_pitching_stats.return_value = {'era': '4.0'}
    fetch_team_stats_direct(db, '2025-09-01', '2025-09-02', client)
    for call in client.get_team_hitting_stats.call_args_list + client.get_team_pitching_stats.call_args_list:
        assert call.args[1] == '2025-01-01'
    assert {c.args[2] for c in client.get_team_hitting_stats.call_args_list} == {'2025-09-01', '2025-09-02'}


def _frames(rows):
    off = pd.DataFrame([{'team_id': 1, 'date': pd.Timestamp(d), 'team_batting_average': v,
                         'on_base_percentage': v, 'slugging_percentage': v} for d, v in rows])
    de = pd.DataFrame([{'team_id': 1, 'date': pd.Timestamp(d), 'team_era': v, 'whip': v,
                        'strikeouts': int(v * 100)} for d, v in rows])
    return off, de


def test_training_ignores_same_day_and_prior_season_snapshots():
    off, de = _frames([('2024-09-29', 0.111), ('2025-04-09', 0.222), ('2025-04-10', 0.999)])
    fe = GameFeatureGenerator()
    stats = fe._get_current_season_stats(1, pd.Timestamp('2025-04-10'), off, de)
    assert stats['team_batting_average'] == 0.222  # not the same-day 0.999


def test_training_has_no_stats_rather_than_last_seasons_stats():
    off, de = _frames([('2024-09-29', 0.111)])
    fe = GameFeatureGenerator()
    assert fe._get_current_season_stats(1, pd.Timestamp('2025-03-27'), off, de) == {}


def _seed(db, rows):
    for d, v in rows:
        db.add(MLBOffensiveStats(team_id=1, date=d, team_batting_average=v, runs_scored=1,
                                 home_runs=1, on_base_percentage=v, slugging_percentage=v))
        db.add(MLBDefensiveStats(team_id=1, date=d, team_era=v * 10, runs_allowed=1,
                                 whip=v * 5, strikeouts=1, avg_against=v))
    db.commit()


def test_serving_ratings_use_strictly_earlier_same_season_rows(db):
    _seed(db, [(date(2024, 9, 29), 0.111), (date(2025, 4, 9), 0.222), (date(2025, 4, 10), 0.999)])
    svc = EnhancedMLBAnalytics(rolling_window=5)
    game = datetime(2025, 4, 10, 19, 0)
    expected_off = round(0.222 * 0.3 + 0.222 * 0.4 + 0.222 * 0.3, 3)
    assert svc._calculate_offensive_rating(db, 1, game) == expected_off
    expected_def = round((max(0, 6.0 - 2.22) / 6.0) * 0.6 + (max(0, 2.0 - 1.11) / 2.0) * 0.4, 3)
    assert svc._calculate_defensive_rating(db, 1, game) == expected_def


def test_serving_returns_none_when_only_prior_season_rows_exist(db):
    _seed(db, [(date(2024, 9, 29), 0.111)])
    svc = EnhancedMLBAnalytics(rolling_window=5)
    game = datetime(2025, 3, 27, 19, 0)
    assert svc._calculate_offensive_rating(db, 1, game) is None
    assert svc._calculate_defensive_rating(db, 1, game) is None


# --- collection contract: boundaries never depend on how collection was invoked ---

def _api_payload(group):
    stat = {'hitting': {'avg': '.251', 'runs': 714, 'homeRuns': 183, 'obp': '.320', 'slg': '.410'},
            'pitching': {'era': '3.90', 'runs': 650, 'whip': '1.25', 'strikeOuts': 1400, 'avg': '.240'}}[group]
    return {'stats': [{'group': {'displayName': group}, 'type': {'displayName': 'byDateRange'},
                       'splits': [{'stat': stat}]}]}


class RecordingClient(MLBDirectAPI):
    """Real extraction and request building; only the HTTP call is replaced."""

    def __init__(self):
        super().__init__()
        self.requests = []

    def _make_request(self, endpoint, params=None):
        self.requests.append((endpoint, dict(params)))
        return _api_payload(params['group'])


def _final_games(db, days):
    for i, day in enumerate(days):
        db.add(MLBSchedule(game_id=f'g{i}', date=day, home_team_id=1, away_team_id=2,
                           status='Final', home_score=3, away_score=2))
    db.commit()


def _requests_for(client, team_id, day):
    return [p for e, p in client.requests
            if e == f'teams/{team_id}/stats' and p['endDate'] == day.isoformat()]


@pytest.mark.parametrize('window', [('2025-09-02', '2025-09-02'), ('2025-08-03', '2025-09-02'),
                                    ('2025-04-01', '2025-09-30')])
def test_same_team_and_date_get_identical_boundaries_for_any_collection_range(db, window):
    _final_games(db, [date(2025, 9, 2)])
    client = RecordingClient()
    fetch_team_stats_direct(db, *window, client, today=date(2025, 10, 1))
    seen = _requests_for(client, 1, date(2025, 9, 2))
    assert {p['group'] for p in seen} == {'hitting', 'pitching'}
    assert all(p['startDate'] == '2025-01-01' and p['season'] == 2025 and p['gameType'] == 'R' for p in seen)


def test_recovery_across_two_seasons_resets_at_each_season_boundary(db):
    from machine_learning.scripts.update_mlb_data import recovery_windows
    _final_games(db, [date(2025, 9, 28), date(2026, 4, 2)])
    client = RecordingClient()
    for first, last in recovery_windows('2025-09-01', '2026-04-30'):
        fetch_team_stats_direct(db, first, last, client, require_complete=True, today=date(2026, 6, 1))
    assert {p['startDate'] for p in _requests_for(client, 1, date(2025, 9, 28))} == {'2025-01-01'}
    assert {p['startDate'] for p in _requests_for(client, 1, date(2026, 4, 2))} == {'2026-01-01'}
    assert {p['season'] for p in _requests_for(client, 1, date(2026, 4, 2))} == {2026}


def test_current_day_is_never_stored_as_a_finalized_snapshot(db):
    _final_games(db, [date(2025, 9, 1), date(2025, 9, 2)])
    client = RecordingClient()
    fetch_team_stats_direct(db, '2025-09-01', '2025-09-02', client, today=date(2025, 9, 2))
    stored = {r.date for r in db.query(MLBOffensiveStats).all()}
    assert stored == {date(2025, 9, 1)}
    assert not _requests_for(client, 1, date(2025, 9, 2))
    # the next day's run stores it, once the day is complete
    fetch_team_stats_direct(db, '2025-09-01', '2025-09-02', client, today=date(2025, 9, 3))
    assert {r.date for r in db.query(MLBOffensiveStats).all()} == {date(2025, 9, 1), date(2025, 9, 2)}


# --- selection with non-midnight game timestamps ---

def test_training_evening_game_cannot_see_its_own_midnight_snapshot():
    off, de = _frames([('2025-04-09', 0.222), ('2025-04-10', 0.999)])
    fe = GameFeatureGenerator()
    for stamp in ('2025-04-10 00:00', '2025-04-10 19:05', '2025-04-10 23:59'):
        stats = fe._get_current_season_stats(1, pd.Timestamp(stamp), off, de)
        assert stats['team_batting_average'] == 0.222


def test_training_future_snapshots_are_excluded():
    off, de = _frames([('2025-04-09', 0.222), ('2025-04-11', 0.999)])
    fe = GameFeatureGenerator()
    stats = fe._get_current_season_stats(1, pd.Timestamp('2025-04-10 19:05'), off, de)
    assert stats['team_batting_average'] == 0.222


def test_serving_evening_game_cannot_see_same_day_or_future_snapshots(db):
    _seed(db, [(date(2025, 4, 9), 0.222), (date(2025, 4, 10), 0.999), (date(2025, 4, 11), 0.777)])
    svc = EnhancedMLBAnalytics(rolling_window=5)
    expected = round(0.222 * 0.3 + 0.222 * 0.4 + 0.222 * 0.3, 3)
    for stamp in (datetime(2025, 4, 10, 0, 0), datetime(2025, 4, 10, 23, 59)):
        assert svc._calculate_offensive_rating(db, 1, stamp) == expected
