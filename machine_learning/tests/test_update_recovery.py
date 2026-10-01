"""Recovery includes missed seasons and never hides incomplete downloads."""

from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from machine_learning.data.collection.mlb_direct_api import MLBDirectAPI, fetch_team_stats_direct
from machine_learning.data.models.mlb_models import (
    MLBTeam, MLBSchedule, MLBOffensiveStats, MLBDefensiveStats,
)
from machine_learning.scripts.update_mlb_data import MLBDataUpdater, recovery_windows
from shared.database import Base


def test_recovery_windows_split_season_boundary():
    assert list(recovery_windows('2025-09-01', '2026-04-02')) == [
        ('2025-09-01', '2025-12-31'), ('2026-01-01', '2026-04-02'),
    ]


@pytest.mark.parametrize('kwargs', [
    {'recover_from': '2999-01-01'},
    {'recover_from': '2025-01-01', 'skip_stats': True},
    {'recover_from': '2025-01-01', 'start_date': '2025-01-01'},
    {'start_date': '2026-01-01'},
    {'start_date': '2026-01-02', 'end_date': '2026-01-01'},
])
def test_invalid_recovery_arguments_fail_before_connecting(kwargs):
    with pytest.raises(ValueError):
        MLBDataUpdater(**kwargs)


def test_recovery_expands_schedule_and_collects_each_pitcher_season():
    updater = MLBDataUpdater(recover_from='2025-09-01')
    updater.end_date = '2026-04-02'
    updater.session = MagicMock()
    season = SimpleNamespace(regular_season_start_date='2026-03-25')
    with patch('machine_learning.scripts.update_mlb_data.fetch_schedule') as schedule, \
         patch('machine_learning.scripts.update_mlb_data.fetch_team_stats_direct') as stats, \
         patch('machine_learning.scripts.update_mlb_data.collect_pitcher_stats') as pitchers:
        pitchers.return_value = {'inserted': 1, 'skipped': 0, 'failed_pitchers': 0}
        updater.update_schedule(season)
        updater.update_team_stats(season)
        updater.update_pitcher_stats(season)
    assert schedule.call_args.args[2] == '2025-09-01'
    assert [(c.args[1:], c.kwargs) for c in stats.call_args_list] == [
        (('2025-09-01', '2025-12-31'), {'require_complete': True}),
        (('2026-01-01', '2026-04-02'), {'require_complete': True}),
    ]
    assert pitchers.call_args.kwargs['seasons'] == [2025, 2026]
    assert pitchers.call_args.kwargs['collector'].api.raise_on_error is True


def test_strict_client_propagates_transport_failure():
    client = MLBDirectAPI(raise_on_error=True)
    with patch.object(client.session, 'get', side_effect=requests.Timeout('offline')):
        with pytest.raises(requests.Timeout):
            client._make_request('schedule')
    client.session.close()


def test_historical_team_request_names_the_season():
    client = MLBDirectAPI()
    with patch.object(client, '_make_request') as request:
        client.get_team_hitting_stats(139, '2025-09-01', '2025-09-02')
    assert request.call_args.args[1] == {
        'season': 2025, 'stats': 'byDateRange', 'group': 'hitting',
        'startDate': '2025-09-01', 'endDate': '2025-09-02',
    }
    client.session.close()


@pytest.mark.parametrize('failure', ['timeout', 'empty'])
def test_partial_recovery_commits_complete_dates_and_retry_skips_them(failure):
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        session.add_all([MLBTeam(id=i, name=f'Team {i}') for i in (1, 2, 3)])
        for day in (1, 2):
            session.add(MLBSchedule(
                game_id=str(day), date=date(2025, 9, day), home_team_id=1,
                away_team_id=2, status='Final', home_score=3, away_score=2,
            ))
        session.commit()
        client = MagicMock()
        client.extract_hitting_stats.return_value = {'avg': '.250'}
        client.extract_pitching_stats.return_value = {'era': '4.0'}

        def download(team_id, start, end):
            if end == '2025-09-02':
                if failure == 'empty':
                    return None
                raise requests.Timeout('second date failed')
            return {'stats': ['valid']}

        client.get_team_hitting_stats.side_effect = download
        with pytest.raises((requests.Timeout, RuntimeError)):
            fetch_team_stats_direct(session, '2025-09-01', '2025-09-02', client, require_complete=True)
        session.rollback()
        assert session.query(MLBOffensiveStats).count() == 2
        assert session.query(MLBDefensiveStats).count() == 2

        client.reset_mock(side_effect=True)
        client.get_team_hitting_stats.return_value = {'stats': ['valid']}
        fetch_team_stats_direct(session, '2025-09-01', '2025-09-02', client, require_complete=True)
        assert session.query(MLBOffensiveStats).count() == 4
        assert session.query(MLBDefensiveStats).count() == 4
        assert all(c.args[2] == '2025-09-02' for c in client.get_team_hitting_stats.call_args_list)
        assert {c.args[0] for c in client.get_team_hitting_stats.call_args_list} == {1, 2}
    finally:
        session.close()
        engine.dispose()


@pytest.mark.parametrize('group,method', [('hitting', 'extract_hitting_stats'), ('pitching', 'extract_pitching_stats')])
def test_date_range_response_is_recognized(group, method):
    client = MLBDirectAPI()
    payload = {'stats': [{'group': {'displayName': group},
                         'type': {'displayName': 'byDateRange'},
                         'splits': [{'stat': {'gamesPlayed': 2}}]}]}
    assert getattr(client, method)(payload) == {'gamesPlayed': 2}
    client.session.close()
