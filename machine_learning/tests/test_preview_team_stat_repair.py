"""The repair preview classifies rows correctly and can never write to the database."""

from datetime import date
from unittest.mock import patch

from machine_learning.scripts.preview_team_stat_repair import (
    TABLES, Previewer, classify, proposed_values, row_fingerprint,
)

STORED = {'team_batting_average': 0.26, 'runs_scored': 92, 'home_runs': 16,
          'on_base_percentage': 0.336, 'slugging_percentage': 0.385}


def test_proposed_values_use_collector_casting():
    api = {'avg': '.233', 'runs': 3, 'homeRuns': 1, 'obp': '.250', 'slg': '.367'}
    assert proposed_values(api, TABLES['offense'][2]) == {
        'team_batting_average': 0.233, 'runs_scored': 3, 'home_runs': 1,
        'on_base_percentage': 0.25, 'slugging_percentage': 0.367}


def test_classify_unchanged_changed_and_idle_club():
    assert classify(STORED, dict(STORED)) == 'unchanged'
    assert classify(STORED, {**STORED, 'runs_scored': 3}) == 'would_change'
    assert classify(STORED, None) == 'no_stats_yet'


def test_fingerprint_changes_when_a_stored_value_changes():
    base = {'id': 1, 'team_id': 139, 'date': date(2025, 3, 28), **STORED}
    assert row_fingerprint(base) == row_fingerprint(dict(base))
    assert row_fingerprint(base) != row_fingerprint({**base, 'runs_scored': 93})


def test_network_failure_is_reported_never_treated_as_unchanged():
    previewer = Previewer(workers=1, delay=0)
    row = {'id': 1, 'team_id': 139, 'date': date(2025, 3, 28), **STORED}
    with patch.object(Previewer, 'fetch', side_effect=TimeoutError('offline')):
        result = previewer.preview_row('offense', row)
    assert result['status'] == 'fetch_error' and result['proposed'] is None


def test_missing_row_with_api_data_is_flagged_for_insert():
    previewer = Previewer(workers=1, delay=0)
    row = {'id': None, 'team_id': 110, 'date': date(2026, 10, 14), 'missing': True,
           **{c: None for c in TABLES['offense'][2]}}
    with patch.object(Previewer, 'fetch', return_value=dict(STORED)):
        assert previewer.preview_row('offense', row)['status'] == 'missing_row'
