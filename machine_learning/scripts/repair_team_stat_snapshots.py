"""
Reviewed repair of recent team-stat snapshots (#52).

Three separate operations:

  preview  Read-only. Lists stored offense/defense rows in a date range, asks the
           MLB API for the corrected cumulative regular-season value of each, and
           writes a manifest (original rows with primary keys, proposed values,
           API evidence). Nothing is written to the database.
  apply    Replays exactly the manifest's replacements in one transaction,
           preserving row IDs. Without --execute it only verifies and reports.
  restore  Puts the manifest's original values back (same checks, reversed).

Exports and evidence are written under .local/ (gitignored), never into tracked
source. Apply and restore refuse to run when the preview is incomplete or
ambiguous, when its file hash differs from the one the reviewer approved, or when
the database no longer matches what the preview saw.

Examples:
    python -m machine_learning.scripts.repair_team_stat_snapshots preview
    python -m machine_learning.scripts.repair_team_stat_snapshots apply \\
        --manifest .local/repairs/<run>/manifest.json --manifest-sha256 <hash>
    ... apply ... --execute      # only after the preview was approved
"""

import argparse
import hashlib
import json
import logging
import subprocess
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from sqlalchemy import text

from machine_learning.data.collection.mlb_direct_api import MLBDirectAPI, season_start_date
from machine_learning.data.models.mlb_models import MLBDefensiveStats, MLBOffensiveStats, MLBSchedule
from shared.database import connect_to_db

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FROM_DATE = date(2026, 9, 26)
TOLERANCE = 1e-9

CONTRACT = (
    "A snapshot dated D holds the cumulative regular-season team statistics from "
    "January 1 of D's year through D (MLB Stats API teams/{id}/stats, "
    "stats=byDateRange, gameType=R, season=year of D)."
)

# table -> (model, API group, stored column -> (API stat key, caster))
TABLES = {
    'offense': (MLBOffensiveStats, 'hitting', {
        'team_batting_average': ('avg', float),
        'runs_scored': ('runs', int),
        'home_runs': ('homeRuns', int),
        'on_base_percentage': ('obp', float),
        'slugging_percentage': ('slg', float),
    }),
    'defense': (MLBDefensiveStats, 'pitching', {
        'team_era': ('era', float),
        'runs_allowed': ('runs', int),
        'whip': ('whip', float),
        'strikeouts': ('strikeOuts', int),
        'avg_against': ('avg', float),
    }),
}

# Statuses that make a manifest unsafe to apply.
BLOCKING = {'missing_response', 'fetch_error', 'duplicate_key'}

Fetcher = Callable[[str, int, date], Tuple[Optional[Dict], Optional[Dict]]]


class RepairRefused(Exception):
    """The requested operation is unsafe; nothing was written."""


# ---------------------------------------------------------------- helpers

def values_match(a: Dict, b: Dict, columns) -> bool:
    for col in columns:
        x, y = a.get(col), b.get(col)
        if x is None or y is None:
            if x is not y:
                return False
        elif abs(float(x) - float(y)) > TOLERANCE:
            return False
    return True


def proposed_values(api_stats: Dict, columns: Dict) -> Dict:
    """Map an API stat block onto stored column names, using the collector's casting."""
    return {col: caster(api_stats.get(key, 0)) for col, (key, caster) in columns.items()}


def classify(original: Dict, proposed: Optional[Dict], columns) -> str:
    if proposed is None:
        return 'missing_response'
    return 'unchanged' if values_match(original, proposed, columns) else 'would_change'


def file_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def code_revision() -> Dict:
    try:
        sha = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=REPO_ROOT, capture_output=True,
                             text=True, check=True).stdout.strip()
        dirty = bool(subprocess.run(['git', 'status', '--porcelain'], cwd=REPO_ROOT,
                                    capture_output=True, text=True, check=True).stdout.strip())
        return {'commit': sha, 'uncommitted_changes': dirty}
    except Exception as exc:  # recorded, not fatal: the manifest says what is unknown
        return {'commit': None, 'uncommitted_changes': None, 'error': str(exc)}


def latest_completed_date(session, today: Optional[date] = None) -> Optional[date]:
    """Newest date with a Final game that is strictly before today."""
    today = today or date.today()
    row = session.query(MLBSchedule.date).filter(
        MLBSchedule.status == 'Final', MLBSchedule.date < today
    ).order_by(MLBSchedule.date.desc()).first()
    return row[0] if row else None


def load_candidates(session, from_date: date, through_date: date) -> Dict[str, List[Dict]]:
    out = {}
    for table, (model, _, columns) in TABLES.items():
        rows = session.query(model).filter(
            model.date >= from_date, model.date <= through_date
        ).order_by(model.date, model.team_id, model.id).all()
        out[table] = [{'id': r.id, 'team_id': r.team_id, 'date': r.date.isoformat(),
                       'original': {c: getattr(r, c) for c in columns}} for r in rows]
    return out


def find_missing_rows(session, candidates: Dict[str, List[Dict]], from_date: date, through_date: date) -> List[Dict]:
    """Clubs with a Final game in range but no stored snapshot. Reported, never inserted."""
    played = set()
    for g in session.query(MLBSchedule).filter(
        MLBSchedule.status == 'Final', MLBSchedule.date >= from_date, MLBSchedule.date <= through_date
    ).all():
        played.update(((g.home_team_id, g.date.isoformat()), (g.away_team_id, g.date.isoformat())))
    missing = []
    for table, rows in candidates.items():
        stored = {(r['team_id'], r['date']) for r in rows}
        missing += [{'table': table, 'team_id': t, 'date': d} for (t, d) in sorted(played - stored)]
    return missing


# ---------------------------------------------------------------- preview

class ApiFetcher:
    """Corrected value for one snapshot, using the production collector's client."""

    def __init__(self, delay: float = 0.1):
        self.delay = delay
        self._local = threading.local()

    def __call__(self, table: str, team_id: int, day: date):
        if not hasattr(self._local, 'client'):
            self._local.client = MLBDirectAPI(raise_on_error=True)
        client = self._local.client
        _, group, columns = TABLES[table]
        start, end = season_start_date(day), day.isoformat()
        time.sleep(self.delay)
        if group == 'hitting':
            raw = client.get_team_hitting_stats(team_id, start, end)
            stats = client.extract_hitting_stats(raw) if raw else None
        else:
            raw = client.get_team_pitching_stats(team_id, start, end)
            stats = client.extract_pitching_stats(raw) if raw else None
        return (proposed_values(stats, columns) if stats else None), raw


def build_preview(session, from_date: date, through_date: date, fetcher: Fetcher, workers: int = 4) -> Dict:
    """Pure read: returns the manifest dict. Never writes to the session."""
    candidates = load_candidates(session, from_date, through_date)
    missing = find_missing_rows(session, candidates, from_date, through_date)

    keys = {t: Counter((r['team_id'], r['date']) for r in rows) for t, rows in candidates.items()}
    work = []
    for table, rows in candidates.items():
        for r in rows:
            work.append((table, r, keys[table][(r['team_id'], r['date'])] > 1))

    def one(item):
        table, row, duplicate = item
        columns = TABLES[table][2]
        entry = {'table': table, 'id': row['id'], 'team_id': row['team_id'], 'date': row['date'],
                 'original': row['original'], 'proposed': None, 'error': None}
        if duplicate:
            entry['status'] = 'duplicate_key'
            return entry, None
        try:
            proposed, raw = fetcher(table, row['team_id'], date.fromisoformat(row['date']))
            entry['proposed'] = proposed
            entry['status'] = classify(row['original'], proposed, columns)
            return entry, raw
        except Exception as exc:  # a failed request must never look like "unchanged"
            entry['status'] = 'fetch_error'
            entry['error'] = str(exc)
            return entry, None

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(one, work))

    rows = [r for r, _ in results]
    evidence = [{'table': r['table'], 'id': r['id'], 'response': raw} for r, raw in results if raw is not None]
    counts = Counter(f"{r['table']}.{r['status']}" for r in rows)
    bind = session.bind
    return {
        'meta': {
            'generated_at': datetime.now().isoformat(timespec='seconds'),
            'contract': CONTRACT,
            'code': code_revision(),
            'from_date': from_date.isoformat(),
            'through_date': through_date.isoformat(),
            'database': getattr(getattr(bind, 'url', None), 'database', None),
        },
        'summary': {
            'rows': len(rows),
            'counts': dict(sorted(counts.items())),
            'blocking': sorted(k for k in counts if k.split('.')[1] in BLOCKING),
            'missing_rows_not_inserted': missing,
        },
        'rows': rows,
        '_evidence': evidence,
    }


def write_preview(manifest: Dict, out_dir: Path) -> Tuple[Path, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    evidence = manifest.pop('_evidence')
    (out_dir / 'api_evidence.json').write_text(json.dumps(evidence))
    path = out_dir / 'manifest.json'
    path.write_text(json.dumps(manifest, indent=1, sort_keys=True))
    digest = file_sha256(path)
    (out_dir / 'manifest.sha256').write_text(digest + '\n')
    return path, digest


# ---------------------------------------------------------------- apply / restore

def _current(session, table: str, row_id: int):
    return session.get(TABLES[table][0], row_id)


def run_replacement(session, manifest: Dict, direction: str, execute: bool, out_dir: Optional[Path] = None) -> Dict:
    """
    Move manifest rows from original -> proposed ('apply') or back ('restore').

    All checks happen before the first write. Rows already at the target are left
    alone, so a repeated invocation is a no-op. Any failure rolls the transaction back.
    """
    if direction not in ('apply', 'restore'):
        raise ValueError(direction)
    src, dst = ('original', 'proposed') if direction == 'apply' else ('proposed', 'original')
    meta, rows = manifest['meta'], manifest['rows']

    blocking = sorted({f"{r['table']}.{r['status']}" for r in rows if r['status'] in BLOCKING})
    if blocking:
        raise RepairRefused(f'preview is incomplete or ambiguous: {", ".join(blocking)}')
    database = getattr(getattr(session.bind, 'url', None), 'database', None)
    if meta.get('database') and database != meta['database']:
        raise RepairRefused(f'preview was made against {meta["database"]!r}, not {database!r}')

    # Completeness: the set of rows in range must be exactly what the preview saw.
    from_d, through_d = date.fromisoformat(meta['from_date']), date.fromisoformat(meta['through_date'])
    for table, (model, _, _) in TABLES.items():
        now = {r.id for r in session.query(model.id).filter(model.date >= from_d, model.date <= through_d)}
        seen = {r['id'] for r in rows if r['table'] == table}
        if now != seen:
            raise RepairRefused(
                f'{table} rows changed since preview: {len(now - seen)} new, {len(seen - now)} gone')

    pending, done, conflicts = [], 0, []
    for r in rows:
        columns = TABLES[r['table']][2]
        obj = _current(session, r['table'], r['id'])
        live = {c: getattr(obj, c) for c in columns}
        if (obj.team_id, obj.date.isoformat()) != (r['team_id'], r['date']):
            conflicts.append((r['table'], r['id'], 'team/date differs'))
        elif r['status'] == 'unchanged':
            if not values_match(live, r['original'], columns):
                conflicts.append((r['table'], r['id'], 'unchanged row was edited'))
        elif values_match(live, r[dst], columns):
            done += 1
        elif values_match(live, r[src], columns):
            pending.append((r, obj))
        else:
            conflicts.append((r['table'], r['id'], 'values differ from the preview'))
    if conflicts:
        raise RepairRefused(f'{len(conflicts)} row(s) changed since preview, e.g. {conflicts[:3]}')

    result = {'direction': direction, 'pending': len(pending), 'already_done': done, 'executed': False}
    if not pending or not execute:
        return result

    if out_dir is None:
        raise RepairRefused('a restoration artifact location is required to execute')
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact = out_dir / f'restore_before_{direction}_{datetime.now().strftime("%Y%m%dT%H%M%S")}.json'
    artifact.write_text(json.dumps([{'table': r['table'], 'id': r['id'], 'values': r[src]}
                                    for r, _ in pending], indent=1))
    try:
        for r, obj in pending:
            for col, val in r[dst].items():
                setattr(obj, col, val)
        session.flush()
        for r, obj in pending:  # re-read and verify before committing
            session.refresh(obj)
            live = {c: getattr(obj, c) for c in TABLES[r['table']][2]}
            if not values_match(live, r[dst], TABLES[r['table']][2]):
                raise RuntimeError(f"post-write check failed for {r['table']} id {r['id']}")
        session.commit()
    except Exception:
        session.rollback()
        raise
    result.update(executed=True, artifact=str(artifact))
    return result


def load_manifest(path: Path, expected_sha256: str) -> Dict:
    actual = file_sha256(path)
    if actual != expected_sha256:
        raise RepairRefused(f'manifest hash {actual} does not match the approved {expected_sha256}')
    return json.loads(Path(path).read_text())


# ---------------------------------------------------------------- CLI

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('preview')
    p.add_argument('--from-date', type=date.fromisoformat, default=DEFAULT_FROM_DATE)
    p.add_argument('--through-date', type=date.fromisoformat, help='Default: latest completed date')
    p.add_argument('--out-dir', type=Path)
    p.add_argument('--workers', type=int, default=4)
    p.add_argument('--delay', type=float, default=0.1)
    for name in ('apply', 'restore'):
        a = sub.add_parser(name)
        a.add_argument('--manifest', type=Path, required=True)
        a.add_argument('--manifest-sha256', required=True, help='Hash of the manifest the reviewer approved')
        a.add_argument('--execute', action='store_true', help='Write changes (default: verify only)')
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    session = connect_to_db()
    try:
        if args.command == 'preview':
            if session.bind.dialect.name == 'postgresql':
                session.execute(text('SET TRANSACTION READ ONLY'))  # writes are rejected by Postgres
            through = args.through_date or latest_completed_date(session)
            if through is None or through < args.from_date:
                print('no completed dates in range')
                return 1
            out_dir = args.out_dir or REPO_ROOT / '.local' / 'repairs' / datetime.now().strftime('%Y%m%dT%H%M%S')
            manifest = build_preview(session, args.from_date, through, ApiFetcher(args.delay), args.workers)
            session.rollback()
            path, digest = write_preview(manifest, out_dir)
            print(json.dumps(manifest['summary'], indent=1))
            print(f'manifest: {path}\nsha256:   {digest}')
            return 0 if not manifest['summary']['blocking'] else 3
        manifest = load_manifest(args.manifest, args.manifest_sha256)
        result = run_replacement(session, manifest, args.command, args.execute, args.manifest.parent)
        print(json.dumps(result, indent=1))
        return 0
    except RepairRefused as exc:
        session.rollback()
        print(f'REFUSED: {exc}', file=sys.stderr)
        return 2
    finally:
        session.close()


if __name__ == '__main__':
    sys.exit(main())
