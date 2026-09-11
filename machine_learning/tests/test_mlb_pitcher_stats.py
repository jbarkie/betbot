"""
Unit tests for starting pitcher stats collection.
"""

import pytest

from machine_learning.data.collection.mlb_pitcher_stats import (
    build_pregame_rows,
    collect_pitcher_stats,
    compute_rate_stats,
    parse_innings_pitched,
)


def _split(date, game_pk, team_id=139, started=1, ip='6.0',
           er=2, hits=5, bb=1, k=7):
    """Build one game log split shaped like the MLB Stats API response."""
    return {
        'date': date,
        'game': {'gamePk': game_pk},
        'team': {'id': team_id},
        'stat': {
            'gamesStarted': started,
            'inningsPitched': ip,
            'earnedRuns': er,
            'hits': hits,
            'baseOnBalls': bb,
            'strikeOuts': k,
        },
    }


class TestParseInningsPitched:
    """Innings are reported in outs notation, not as decimals."""

    @pytest.mark.parametrize('raw,expected', [
        ('6.0', 6.0),
        ('4.1', 4 + 1 / 3),
        ('6.2', 6 + 2 / 3),
        ('0.1', 1 / 3),
        ('0.0', 0.0),
    ])
    def test_outs_notation_converted_to_thirds(self, raw, expected):
        assert parse_innings_pitched(raw) == pytest.approx(expected)

    def test_decimal_one_is_one_third_not_one_tenth(self):
        """Guards the specific bug a naive float() cast would introduce."""
        assert parse_innings_pitched('4.1') != pytest.approx(4.1)
        assert parse_innings_pitched('4.1') == pytest.approx(4.3333, abs=1e-4)

    @pytest.mark.parametrize('raw', [None, '', 'abc', '-'])
    def test_unparseable_values_return_zero(self, raw):
        assert parse_innings_pitched(raw) == 0.0

    def test_accepts_numeric_input(self):
        assert parse_innings_pitched(5) == 5.0


class TestComputeRateStats:
    """ERA/WHIP/K9 derivation from accumulated counting stats."""

    def test_known_values(self):
        totals = {'innings_pitched': 18.0, 'earned_runs': 6,
                  'hits': 15, 'walks': 3, 'strikeouts': 20}
        rates = compute_rate_stats(totals)
        assert rates['era'] == pytest.approx(3.0)
        assert rates['whip'] == pytest.approx(1.0)
        assert rates['k9'] == pytest.approx(10.0)

    def test_zero_innings_yields_none_not_zero(self):
        """Rates are undefined with no innings, and must not read as elite."""
        rates = compute_rate_stats({'innings_pitched': 0.0, 'earned_runs': 0,
                                    'hits': 0, 'walks': 0, 'strikeouts': 0})
        assert rates == {'era': None, 'whip': None, 'k9': None}


class TestBuildPregameRows:
    """Cumulative accumulation must never include the game being described."""

    def test_first_start_of_season_has_null_rates(self):
        rows = build_pregame_rows([_split('2026-04-01', 1001)])
        assert len(rows) == 1
        assert rows[0]['game_id'] == '1001'
        assert rows[0]['era'] is None
        assert rows[0]['whip'] is None
        assert rows[0]['k9'] is None

    def test_midseason_start_reflects_only_prior_starts(self):
        """Third start carries the totals of starts one and two, nothing later."""
        splits = [
            _split('2026-04-01', 1001, ip='6.0', er=2, hits=5, bb=1, k=6),
            _split('2026-04-07', 1002, ip='6.0', er=4, hits=7, bb=2, k=6),
            _split('2026-04-13', 1003, ip='9.0', er=0, hits=0, bb=0, k=15),
        ]
        rows = build_pregame_rows(splits)
        third = rows[2]

        # 12 IP, 6 ER, 12 H, 3 BB, 12 K from the first two starts only.
        assert third['era'] == pytest.approx(4.5)
        assert third['whip'] == pytest.approx(1.25)
        assert third['k9'] == pytest.approx(9.0)

    def test_no_leakage_from_the_described_game(self):
        """A shutout gem must not improve the row written for that same game."""
        splits = [
            _split('2026-04-01', 1001, ip='5.0', er=5, hits=10, bb=5, k=1),
            _split('2026-04-07', 1002, ip='9.0', er=0, hits=1, bb=0, k=12),
        ]
        rows = build_pregame_rows(splits)
        # Row for game 1002 reflects the ugly first start, not its own shutout.
        assert rows[1]['game_id'] == '1002'
        assert rows[1]['era'] == pytest.approx(9.0)

    def test_relief_appearances_excluded(self):
        """Only starts produce rows, and only starts feed the totals."""
        splits = [
            _split('2026-04-01', 1001, started=0, ip='1.0', er=9, hits=9, bb=9, k=0),
            _split('2026-04-07', 1002, started=1, ip='6.0', er=2, hits=5, bb=1, k=6),
            _split('2026-04-13', 1003, started=1, ip='6.0', er=2, hits=5, bb=1, k=6),
        ]
        rows = build_pregame_rows(splits)
        assert [r['game_id'] for r in rows] == ['1002', '1003']
        assert rows[0]['era'] is None                      # no prior *start*
        assert rows[1]['era'] == pytest.approx(3.0)        # relief line excluded

    def test_splits_sorted_before_accumulating(self):
        """Out-of-order API responses must not corrupt the running totals."""
        ordered = [
            _split('2026-04-01', 1001, ip='6.0', er=2, hits=5, bb=1, k=6),
            _split('2026-04-07', 1002, ip='6.0', er=4, hits=7, bb=2, k=6),
        ]
        rows_in_order = build_pregame_rows(ordered)
        rows_reversed = build_pregame_rows(list(reversed(ordered)))
        assert rows_in_order == rows_reversed

    def test_fractional_innings_accumulate_correctly(self):
        """Two starts of 5.1 IP each total 10 2/3 innings, not 10.2."""
        splits = [
            _split('2026-04-01', 1001, ip='5.1', er=1, hits=0, bb=0, k=0),
            _split('2026-04-07', 1002, ip='5.1', er=1, hits=0, bb=0, k=0),
            _split('2026-04-13', 1003),
        ]
        rows = build_pregame_rows(splits)
        assert rows[2]['era'] == pytest.approx(9.0 * 2 / (10 + 2 / 3), abs=1e-3)

    def test_splits_missing_identifiers_are_skipped(self):
        splits = [
            {'date': '2026-04-01', 'game': {}, 'team': {'id': 139},
             'stat': {'gamesStarted': 1, 'inningsPitched': '6.0'}},
            _split('2026-04-07', 1002),
        ]
        rows = build_pregame_rows(splits)
        assert [r['game_id'] for r in rows] == ['1002']

    def test_empty_log_returns_no_rows(self):
        """Rookie with no appearances yields nothing rather than raising."""
        assert build_pregame_rows([]) == []


class _FakeCollector:
    """Stands in for MLBPitcherStatsCollector without network access."""

    def __init__(self, pitchers, logs):
        self._pitchers = pitchers
        self._logs = logs
        self.log_calls = 0

    def get_team_pitchers(self, team_id, season):
        return self._pitchers.get((team_id, season), [])

    def get_game_log(self, pitcher_id, season):
        self.log_calls += 1
        return self._logs.get((pitcher_id, season), [])


@pytest.fixture
def session():
    """In-memory SQLite session with the MLB tables created."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from shared.database import Base
    import machine_learning.data.models.mlb_models  # noqa: F401  (registers tables)

    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    yield db
    db.close()


def _seed_schedule(session):
    from machine_learning.data.models.mlb_models import MLBSchedule, MLBTeam
    from datetime import date

    session.add_all([MLBTeam(id=139, name='Rays'), MLBTeam(id=138, name='Cardinals')])
    session.add_all([
        MLBSchedule(game_id='1001', date=date(2026, 4, 1),
                    home_team_id=139, away_team_id=138, status='Final'),
        MLBSchedule(game_id='1002', date=date(2026, 4, 7),
                    home_team_id=139, away_team_id=138, status='Final'),
    ])
    session.commit()


class TestCollectPitcherStats:
    """End-to-end collection against an in-memory database."""

    def test_inserts_one_row_per_known_start(self, session):
        _seed_schedule(session)
        collector = _FakeCollector(
            pitchers={(139, 2026): [{'pitcher_id': 500, 'pitcher_name': 'Ace Pitcher'}],
                      (138, 2026): []},
            logs={(500, 2026): [_split('2026-04-01', 1001),
                                _split('2026-04-07', 1002)]},
        )

        counts = collect_pitcher_stats(session, seasons=[2026], collector=collector)

        from machine_learning.data.models.mlb_models import MLBPitcherStats
        rows = session.query(MLBPitcherStats).order_by(MLBPitcherStats.game_id).all()
        assert counts['inserted'] == 2
        assert [r.game_id for r in rows] == ['1001', '1002']
        assert rows[0].pitcher_name == 'Ace Pitcher'
        assert rows[0].era is None                       # season debut
        assert rows[1].era == pytest.approx(3.0)         # 2 ER over 6 IP

    def test_rerun_is_idempotent(self, session):
        _seed_schedule(session)
        pitchers = {(139, 2026): [{'pitcher_id': 500, 'pitcher_name': 'Ace Pitcher'}],
                    (138, 2026): []}
        logs = {(500, 2026): [_split('2026-04-01', 1001), _split('2026-04-07', 1002)]}

        from machine_learning.data.models.mlb_models import MLBPitcherStats

        first = collect_pitcher_stats(session, seasons=[2026],
                                      collector=_FakeCollector(pitchers, logs))
        count_after_first = session.query(MLBPitcherStats).count()

        second = collect_pitcher_stats(session, seasons=[2026],
                                       collector=_FakeCollector(pitchers, logs))
        count_after_second = session.query(MLBPitcherStats).count()

        assert first['inserted'] == 2
        assert second['inserted'] == 0
        assert second['skipped'] == 2
        assert count_after_first == count_after_second == 2

    def test_pitcher_with_no_starts_produces_no_rows(self, session):
        """Rookie or pure reliever must be counted, not crash the run."""
        _seed_schedule(session)
        collector = _FakeCollector(
            pitchers={(139, 2026): [{'pitcher_id': 777, 'pitcher_name': 'Rookie Arm'}],
                      (138, 2026): []},
            logs={},  # no game log at all
        )

        counts = collect_pitcher_stats(session, seasons=[2026], collector=collector)

        from machine_learning.data.models.mlb_models import MLBPitcherStats
        assert counts['inserted'] == 0
        assert counts['failed_pitchers'] == 1
        assert session.query(MLBPitcherStats).count() == 0

    def test_starts_in_untracked_games_are_ignored(self, session):
        """A start against a game absent from mlb_schedule must not be written."""
        _seed_schedule(session)
        collector = _FakeCollector(
            pitchers={(139, 2026): [{'pitcher_id': 500, 'pitcher_name': 'Ace Pitcher'}],
                      (138, 2026): []},
            logs={(500, 2026): [_split('2026-04-01', 9999)]},  # unknown gamePk
        )

        counts = collect_pitcher_stats(session, seasons=[2026], collector=collector)
        assert counts['inserted'] == 0

    def test_pitchers_deduped_across_rosters(self, session):
        """A traded pitcher appears on two rosters but is fetched once."""
        _seed_schedule(session)
        collector = _FakeCollector(
            pitchers={
                (139, 2026): [{'pitcher_id': 500, 'pitcher_name': 'Traded Arm'}],
                (138, 2026): [{'pitcher_id': 500, 'pitcher_name': 'Traded Arm'}],
            },
            logs={(500, 2026): [_split('2026-04-01', 1001)]},
        )

        collect_pitcher_stats(session, seasons=[2026], collector=collector)
        assert collector.log_calls == 1
