"""Preview never writes; apply/restore refuse unsafe states and are safe to repeat (#52)."""

import json
from datetime import date
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from machine_learning.data.models.mlb_models import (
    MLBTeam, MLBSchedule, MLBOffensiveStats, MLBDefensiveStats,
)
from machine_learning.scripts.repair_team_stat_snapshots import (
    BLOCKING, RepairRefused, build_preview, file_sha256, latest_completed_date,
    load_manifest, run_replacement, write_preview,
)
from shared.database import Base

FROM, THROUGH = date(2026, 9, 26), date(2026, 9, 27)
OFF = dict(runs_scored=50, home_runs=10, team_batting_average=0.2, on_base_percentage=0.3, slugging_percentage=0.4)
DEF = dict(runs_allowed=50, strikeouts=300, team_era=4.0, whip=1.3, avg_against=0.25)
OFF_NEW = dict(team_batting_average=0.251, runs_scored=714, home_runs=183, on_base_percentage=0.32, slugging_percentage=0.41)
DEF_NEW = dict(team_era=3.9, runs_allowed=650, whip=1.25, strikeouts=1400, avg_against=0.24)


@pytest.fixture
def session():
    engine = create_engine('sqlite://')
    Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine)()
    s.add_all([MLBTeam(id=1, name='A'), MLBTeam(id=2, name='B')])
    for day in (date(2026, 9, 25), date(2026, 9, 26), date(2026, 9, 27)):
        s.add(MLBSchedule(game_id=str(day), date=day, home_team_id=1, away_team_id=2,
                          status='Final', home_score=1, away_score=0))
        for team in (1, 2):
            s.add(MLBOffensiveStats(team_id=team, date=day, **OFF))
            s.add(MLBDefensiveStats(team_id=team, date=day, **DEF))
    s.commit()
    yield s
    s.close()
    engine.dispose()


def fetcher(table, team_id, day):
    new = OFF_NEW if table == 'offense' else DEF_NEW
    return dict(new), {'stats': [{'fake': 'payload'}]}


def snapshot(session):
    out = []
    for model in (MLBOffensiveStats, MLBDefensiveStats):
        session.expire_all()
        out += [tuple((c.name, getattr(r, c.name)) for c in model.__table__.columns)
                for r in session.query(model).order_by(model.id).all()]
    return out


def make_manifest(session, tmp_path, fetch=fetcher):
    manifest = build_preview(session, FROM, THROUGH, fetch, workers=1)
    path, digest = write_preview(manifest, tmp_path)
    return path, digest, json.loads(path.read_text())


def test_preview_changes_nothing_and_writes_only_to_the_output_folder(session, tmp_path):
    before = snapshot(session)
    path, digest, manifest = make_manifest(session, tmp_path)
    assert snapshot(session) == before
    assert not session.new and not session.dirty and not session.deleted
    assert sorted(p.name for p in tmp_path.iterdir()) == ['api_evidence.json', 'manifest.json', 'manifest.sha256']
    assert manifest['summary']['rows'] == 8  # 2 dates x 2 teams x offense+defense; 09-25 is out of range
    assert manifest['summary']['counts'] == {'defense.would_change': 4, 'offense.would_change': 4}
    assert manifest['meta']['contract'] and manifest['meta']['code'] and manifest['meta']['generated_at']
    assert digest == file_sha256(path)


def test_preview_flags_unchanged_missing_failed_duplicate_and_missing_rows(session, tmp_path):
    session.add(MLBOffensiveStats(team_id=1, date=FROM, **OFF))          # duplicate key
    session.query(MLBDefensiveStats).filter_by(team_id=2, date=THROUGH).delete()  # row never stored
    session.commit()

    def mixed(table, team_id, day):
        if table == 'offense' and team_id == 2 and day == FROM:
            return dict(OFF), {}                                         # already correct
        if table == 'defense' and team_id == 1 and day == FROM:
            return None, None                                            # API had nothing
        if table == 'defense' and team_id == 1 and day == THROUGH:
            raise TimeoutError('offline')
        return fetcher(table, team_id, day)

    manifest = build_preview(session, FROM, THROUGH, mixed, workers=1)
    counts = manifest['summary']['counts']
    assert counts['offense.duplicate_key'] == 2
    assert counts['offense.unchanged'] == 1
    assert counts['defense.missing_response'] == 1
    assert counts['defense.fetch_error'] == 1
    assert manifest['summary']['blocking']
    assert manifest['summary']['missing_rows_not_inserted'] == [
        {'table': 'defense', 'team_id': 2, 'date': '2026-09-27'}]


def test_latest_completed_date_never_returns_today(session):
    assert latest_completed_date(session, today=date(2026, 9, 28)) == date(2026, 9, 27)
    assert latest_completed_date(session, today=date(2026, 9, 27)) == date(2026, 9, 26)


def test_apply_without_execute_only_verifies(session, tmp_path):
    _, _, manifest = make_manifest(session, tmp_path)
    before = snapshot(session)
    result = run_replacement(session, manifest, 'apply', execute=False)
    assert result == {'direction': 'apply', 'pending': 8, 'already_done': 0, 'executed': False}
    assert snapshot(session) == before


def test_apply_replaces_in_place_keeps_ids_leaves_out_of_range_alone_and_saves_restore_artifact(session, tmp_path):
    _, _, manifest = make_manifest(session, tmp_path)
    ids_before = {m.__tablename__: [r.id for r in session.query(m).order_by(m.id)]
                  for m in (MLBOffensiveStats, MLBDefensiveStats)}
    outside = session.query(MLBOffensiveStats).filter_by(date=date(2026, 9, 25), team_id=1).one().runs_scored
    result = run_replacement(session, manifest, 'apply', execute=True, out_dir=tmp_path)
    assert result['executed'] and result['pending'] == 8
    session.expire_all()
    assert {m.__tablename__: [r.id for r in session.query(m).order_by(m.id)]
            for m in (MLBOffensiveStats, MLBDefensiveStats)} == ids_before
    row = session.query(MLBOffensiveStats).filter_by(date=FROM, team_id=1).one()
    assert row.runs_scored == 714 and row.team_batting_average == 0.251
    assert session.query(MLBOffensiveStats).filter_by(date=date(2026, 9, 25), team_id=1).one().runs_scored == outside
    artifact = json.loads(open(result['artifact']).read())
    assert len(artifact) == 8 and artifact[0]['values']['runs_scored'] == 50


def test_repeated_apply_is_a_no_op(session, tmp_path):
    _, _, manifest = make_manifest(session, tmp_path)
    run_replacement(session, manifest, 'apply', execute=True, out_dir=tmp_path)
    after_first = snapshot(session)
    again = run_replacement(session, manifest, 'apply', execute=True, out_dir=tmp_path)
    assert again == {'direction': 'apply', 'pending': 0, 'already_done': 8, 'executed': False}
    assert snapshot(session) == after_first
    assert len(list(tmp_path.glob('restore_before_apply_*.json'))) == 1


def test_restore_puts_originals_back_and_is_also_repeatable(session, tmp_path):
    original = snapshot(session)
    _, _, manifest = make_manifest(session, tmp_path)
    run_replacement(session, manifest, 'apply', execute=True, out_dir=tmp_path)
    assert snapshot(session) != original
    assert run_replacement(session, manifest, 'restore', execute=True, out_dir=tmp_path)['executed']
    assert snapshot(session) == original
    assert run_replacement(session, manifest, 'restore', execute=True, out_dir=tmp_path)['pending'] == 0


@pytest.mark.parametrize('blocker', ['missing', 'error', 'duplicate'])
def test_apply_refuses_incomplete_or_ambiguous_previews(session, tmp_path, blocker):
    if blocker == 'duplicate':
        session.add(MLBDefensiveStats(team_id=1, date=FROM, **DEF))
        session.commit()

    def bad(table, team_id, day):
        if blocker == 'missing' and team_id == 1:
            return None, None
        if blocker == 'error' and team_id == 1:
            raise TimeoutError('offline')
        return fetcher(table, team_id, day)

    _, _, manifest = make_manifest(session, tmp_path, bad)
    before = snapshot(session)
    with pytest.raises(RepairRefused, match='incomplete or ambiguous'):
        run_replacement(session, manifest, 'apply', execute=True, out_dir=tmp_path)
    assert snapshot(session) == before


def test_apply_refuses_when_a_row_changed_after_preview(session, tmp_path):
    _, _, manifest = make_manifest(session, tmp_path)
    session.query(MLBOffensiveStats).filter_by(team_id=1, date=FROM).one().runs_scored = 51
    session.commit()
    before = snapshot(session)
    with pytest.raises(RepairRefused, match='changed since preview'):
        run_replacement(session, manifest, 'apply', execute=True, out_dir=tmp_path)
    assert snapshot(session) == before


def test_apply_refuses_when_rows_were_added_or_removed_after_preview(session, tmp_path):
    _, _, manifest = make_manifest(session, tmp_path)
    session.add(MLBOffensiveStats(team_id=2, date=THROUGH, **OFF))  # a scheduler run wrote another row
    session.commit()
    with pytest.raises(RepairRefused, match='rows changed since preview'):
        run_replacement(session, manifest, 'apply', execute=True, out_dir=tmp_path)


def test_apply_refuses_a_preview_from_another_database(session, tmp_path):
    _, _, manifest = make_manifest(session, tmp_path)
    manifest['meta']['database'] = 'some_other_db'
    with pytest.raises(RepairRefused, match='some_other_db'):
        run_replacement(session, manifest, 'apply', execute=True, out_dir=tmp_path)


def test_failure_mid_apply_rolls_everything_back(session, tmp_path):
    _, _, manifest = make_manifest(session, tmp_path)
    before = snapshot(session)
    calls = {'n': 0}
    real_refresh = session.refresh

    def flaky(obj, *a, **k):
        calls['n'] += 1
        if calls['n'] == 3:
            raise RuntimeError('database went away')
        return real_refresh(obj, *a, **k)

    with patch.object(session, 'refresh', side_effect=flaky):
        with pytest.raises(RuntimeError):
            run_replacement(session, manifest, 'apply', execute=True, out_dir=tmp_path)
    assert snapshot(session) == before


def test_manifest_must_match_the_approved_hash(session, tmp_path):
    path, digest, _ = make_manifest(session, tmp_path)
    assert load_manifest(path, digest)['rows']
    with pytest.raises(RepairRefused, match='does not match'):
        load_manifest(path, '0' * 64)
    path.write_text(path.read_text().replace('"proposed"', '"proposed" '))  # edited after review
    with pytest.raises(RepairRefused, match='does not match'):
        load_manifest(path, digest)


def test_blocking_statuses_are_exactly_the_unsafe_ones():
    assert BLOCKING == {'missing_response', 'fetch_error', 'duplicate_key'}
