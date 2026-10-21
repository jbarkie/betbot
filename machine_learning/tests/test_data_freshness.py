"""
Sprint 8 Card 3 (#46): a stale database must not silently produce a stale model.

The whole card is the definition of "fresh": only games with a Final status and
recorded scores count, judged against the run's own end date.
"""

import json
import sys
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from machine_learning.data.processing.data_freshness import check_data_freshness

REF = date(2026, 9, 26)


def _row(d, status='Final', home=3, away=2):
    return {'game_id': f'g{d}', 'date': d, 'status': status,
            'home_score': home, 'away_score': away,
            'home_team_id': 1, 'away_team_id': 2}


def _df(rows):
    return pd.DataFrame(rows, columns=['game_id', 'date', 'status', 'home_score',
                                       'away_score', 'home_team_id', 'away_team_id'])


class TestBoundary:

    def test_exactly_three_days_old_is_fresh_at_default_threshold(self):
        result = check_data_freshness(_df([_row(REF - timedelta(days=3))]), REF, 3)
        assert result.is_stale is False
        assert result.age_days == 3
        assert result.newest_date == REF - timedelta(days=3)

    def test_four_days_old_is_stale_at_default_threshold(self):
        result = check_data_freshness(_df([_row(REF - timedelta(days=4))]), REF, 3)
        assert result.is_stale is True
        assert result.age_days == 4
        assert "limit is 3" in result.reason

    def test_zero_days_old_is_fresh(self):
        result = check_data_freshness(_df([_row(REF)]), REF, 3)
        assert result.is_stale is False and result.age_days == 0

    def test_threshold_is_adjustable_for_offseason(self):
        old = _df([_row(REF - timedelta(days=60))])
        assert check_data_freshness(old, REF, 3).is_stale is True
        assert check_data_freshness(old, REF, 90).is_stale is False

    def test_negative_threshold_rejected(self):
        with pytest.raises(ValueError):
            check_data_freshness(_df([_row(REF)]), REF, -1)


class TestWhatCountsAsCompleted:

    def test_future_scheduled_game_does_not_make_old_data_look_fresh(self):
        rows = [_row(REF - timedelta(days=10)),
                _row(REF + timedelta(days=1), status='Scheduled', home=None, away=None)]
        result = check_data_freshness(_df(rows), REF, 3)
        assert result.is_stale is True
        assert result.newest_date == REF - timedelta(days=10)

    def test_non_final_status_is_ignored_even_with_scores(self):
        rows = [_row(REF - timedelta(days=10)), _row(REF, status='In Progress')]
        result = check_data_freshness(_df(rows), REF, 3)
        assert result.newest_date == REF - timedelta(days=10)

    def test_final_without_scores_is_ignored(self):
        rows = [_row(REF - timedelta(days=10)), _row(REF, home=None, away=None)]
        result = check_data_freshness(_df(rows), REF, 3)
        assert result.newest_date == REF - timedelta(days=10)

    def test_completed_games_after_reference_date_are_ignored(self):
        """A historical --end-date run is judged against its own window."""
        historical_ref = date(2025, 9, 1)
        rows = [_row(historical_ref - timedelta(days=1)), _row(date(2026, 9, 20))]
        result = check_data_freshness(_df(rows), historical_ref, 3)
        assert result.is_stale is False
        assert result.newest_date == historical_ref - timedelta(days=1)
        assert result.reference_date == historical_ref

    def test_accepts_datetime_reference_and_string_dates(self):
        rows = [_row('2026-09-25')]
        result = check_data_freshness(_df(rows), datetime(2026, 9, 26, 15, 30), 3)
        assert result.age_days == 1 and result.is_stale is False


class TestNeverFreshWhenEmpty:

    def test_empty_frame_is_stale(self):
        result = check_data_freshness(_df([]), REF, 3)
        assert result.is_stale is True
        assert result.newest_date is None and result.age_days is None

    def test_none_is_stale(self):
        assert check_data_freshness(None, REF, 3).is_stale is True

    def test_only_scheduled_games_is_stale(self):
        rows = [_row(REF, status='Scheduled', home=None, away=None)]
        result = check_data_freshness(_df(rows), REF, 3)
        assert result.is_stale is True
        assert "no completed games" in result.reason

    def test_all_invalid_dates_is_stale(self):
        rows = [_row('not-a-date'), _row(None)]
        result = check_data_freshness(_df(rows), REF, 3)
        assert result.is_stale is True
        assert result.newest_date is None

    def test_invalid_dates_are_dropped_not_fatal(self):
        rows = [_row('garbage'), _row(REF - timedelta(days=1))]
        result = check_data_freshness(_df(rows), REF, 3)
        assert result.is_stale is False
        assert result.newest_date == REF - timedelta(days=1)

    def test_missing_columns_is_stale(self):
        result = check_data_freshness(pd.DataFrame({'date': [REF]}), REF, 3)
        assert result.is_stale is True
        assert "missing columns" in result.reason


class TestMetadata:

    def test_to_metadata_fields(self):
        result = check_data_freshness(_df([_row(REF - timedelta(days=2))]), REF, 3)
        meta = result.to_metadata()
        assert meta == {
            'newest_completed_game_date': (REF - timedelta(days=2)).isoformat(),
            'data_age_days': 2,
            'max_staleness_days': 3,
            'freshness_reference_date': REF.isoformat(),
        }

    def test_save_model_writes_freshness_fields(self, tmp_path):
        from machine_learning.scripts.train_mlb_model import MLBModelTrainer

        trainer = MLBModelTrainer(model_type='random_forest', verbose=False)
        trainer.pipeline = MagicMock()
        trainer.metrics = {'accuracy': 0.5}
        trainer.freshness = check_data_freshness(_df([_row(REF - timedelta(days=1))]), REF, 3)

        with patch('machine_learning.scripts.train_mlb_model.MLB_MODELS_DIR', tmp_path), \
             patch('machine_learning.scripts.train_mlb_model.joblib.dump'):
            _, metadata_path = trainer.save_model(version='test')

        saved = json.loads(metadata_path.read_text())
        for key in ('newest_completed_game_date', 'data_age_days',
                    'max_staleness_days', 'freshness_reference_date'):
            assert key in saved
        assert saved['data_age_days'] == 1


class TestMainWiring:
    """The gate runs before anything is prepared or fit."""

    STALE = _df([_row(REF - timedelta(days=30))])

    def _run_main(self, argv, schedule):
        from machine_learning.scripts import train_mlb_model as mod

        fetched = (schedule, pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame())
        with patch.object(sys, 'argv', ['train_mlb_model.py'] + argv), \
             patch.object(mod.MLBModelTrainer, 'fetch_data_from_database', return_value=fetched), \
             patch.object(mod.MLBModelTrainer, 'prepare_training_data') as prepare, \
             patch.object(mod.MLBModelTrainer, 'train_and_evaluate', autospec=True,
                          side_effect=lambda self, *a, **k: self.metrics.update({'accuracy': 0.5})) as train, \
             patch.object(mod.MLBModelTrainer, 'save_model', return_value=('m', 'meta')):
            prepare.return_value = pd.DataFrame({'x': range(150)})
            code = None
            try:
                mod.main()
            except SystemExit as e:
                code = e.code
            return code, prepare, train

    def test_fail_on_stale_exits_2_before_any_training(self):
        code, prepare, train = self._run_main(
            ['--end-date', REF.isoformat(), '--fail-on-stale'], self.STALE)
        assert code == 2
        prepare.assert_not_called()
        train.assert_not_called()

    def test_stale_without_flag_warns_and_trains(self, capsys):
        code, prepare, train = self._run_main(['--end-date', REF.isoformat()], self.STALE)
        assert code is None
        train.assert_called_once()
        out = capsys.readouterr().out
        assert "stale" in out and "30 day(s) old" in out

    def test_fresh_data_trains_without_warning(self, capsys):
        fresh = _df([_row(REF - timedelta(days=1))])
        code, prepare, train = self._run_main(
            ['--end-date', REF.isoformat(), '--fail-on-stale'], fresh)
        assert code is None
        train.assert_called_once()
        assert "stale" not in capsys.readouterr().out

    def test_max_staleness_days_flag_relaxes_the_gate(self):
        code, _, train = self._run_main(
            ['--end-date', REF.isoformat(), '--fail-on-stale', '--max-staleness-days', '45'],
            self.STALE)
        assert code is None
        train.assert_called_once()

    def test_help_lists_both_flags(self, capsys):
        from machine_learning.scripts import train_mlb_model as mod
        with patch.object(sys, 'argv', ['train_mlb_model.py', '--help']):
            with pytest.raises(SystemExit):
                mod.main()
        out = capsys.readouterr().out
        assert '--max-staleness-days' in out and '--fail-on-stale' in out
