"""
Non-writing preview of the historical team-stat repair (#52).

For every stored team snapshot in the chosen seasons, this asks the MLB Stats API
for the corrected value (cumulative regular season, Jan 1 through the snapshot
date) and records what a repair would change. The database session is read-only
and nothing is written to it; results go to a JSONL file plus a summary.

Each preview line carries a fingerprint of the stored row so a later apply step
can refuse to act on rows that changed after this preview was made.

Examples:
    python -m machine_learning.scripts.preview_team_stat_repair --seasons 2025 \\
        --team-ids 139 --max-dates 3 --output /tmp/preview.jsonl
"""

import argparse
import hashlib
import json
import logging
import sys
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy import text

from machine_learning.data.collection.mlb_direct_api import MLBDirectAPI, season_start_date
from machine_learning.data.models.mlb_models import MLBOffensiveStats, MLBDefensiveStats
from shared.database import connect_to_db

# (model, API group, stored column -> (API stat key, caster))
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


def row_fingerprint(values: Dict) -> str:
    """Stable hash of a stored row's id, team, date and values."""
    payload = json.dumps(values, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def proposed_values(api_stats: Dict, columns: Dict) -> Dict:
    """Map an API stat block onto stored column names, using the collector's casting."""
    return {col: caster(api_stats.get(key, 0)) for col, (key, caster) in columns.items()}


def classify(stored: Dict, proposed: Optional[Dict], tolerance: float = 1e-9) -> str:
    """
    'unchanged' when every field already matches, else 'would_change'.

    ``proposed`` is None when the API answered but the team has no regular-season
    games yet on that date (the old collector stored rows for idle clubs too).
    """
    if proposed is None:
        return 'no_stats_yet'
    for col, new in proposed.items():
        old = stored.get(col)
        if old is None or abs(float(old) - float(new)) > tolerance:
            return 'would_change'
    return 'unchanged'


class Previewer:
    def __init__(self, workers: int, delay: float):
        self.workers = workers
        self.delay = delay
        self._local = threading.local()

    def _client(self) -> MLBDirectAPI:
        if not hasattr(self._local, 'client'):
            self._local.client = MLBDirectAPI(raise_on_error=True)
        return self._local.client

    def fetch(self, table: str, team_id: int, day: date) -> Optional[Dict]:
        """Corrected API values for one snapshot, or None when the API has none."""
        _, group, columns = TABLES[table]
        client = self._client()
        start, end = season_start_date(day), day.strftime('%Y-%m-%d')
        time.sleep(self.delay)
        if group == 'hitting':
            data = client.get_team_hitting_stats(team_id, start, end)
            stats = client.extract_hitting_stats(data) if data else None
        else:
            data = client.get_team_pitching_stats(team_id, start, end)
            stats = client.extract_pitching_stats(data) if data else None
        return proposed_values(stats, columns) if stats else None

    def preview_row(self, table: str, row: Dict) -> Dict:
        _, _, columns = TABLES[table]
        stored = {c: row[c] for c in columns}
        try:
            proposed = self.fetch(table, row['team_id'], row['date'])
            status = classify(stored, proposed)
            if row.get('missing'):
                status = 'missing_row' if proposed else 'no_stats_yet'
            error = None
        except Exception as exc:  # network failure must not look like "unchanged"
            proposed, status, error = None, 'fetch_error', str(exc)
        return {
            'table': table, 'id': row['id'], 'team_id': row['team_id'],
            'date': row['date'].isoformat(), 'status': status,
            'stored': stored, 'proposed': proposed, 'error': error,
            'fingerprint': row_fingerprint({'id': row['id'], 'team_id': row['team_id'],
                                            'date': row['date'], **stored}),
        }


def find_missing(session, table: str, seasons: List[int], team_ids: Optional[List[int]],
                 stored_keys: set) -> List[Dict]:
    """(team, date) pairs where the club had a Final game but no stored snapshot."""
    from machine_learning.data.models.mlb_models import MLBSchedule
    missing, seen = [], set()
    for g in session.query(MLBSchedule).filter(MLBSchedule.status == 'Final').order_by(MLBSchedule.date).all():
        if g.date.year not in seasons:
            continue
        for team_id in (g.home_team_id, g.away_team_id):
            key = (team_id, g.date)
            if key in stored_keys or key in seen or (team_ids and team_id not in team_ids):
                continue
            seen.add(key)
            missing.append({'id': None, 'team_id': team_id, 'date': g.date, 'missing': True,
                            **{c: None for c in TABLES[table][2]}})
    return missing


def load_rows(session, table: str, seasons: List[int], team_ids: Optional[List[int]],
              max_dates: Optional[int]) -> List[Dict]:
    model, _, columns = TABLES[table]
    query = session.query(model).filter(
        model.date >= date(min(seasons), 1, 1), model.date <= date(max(seasons), 12, 31)
    ).order_by(model.date, model.team_id)
    if team_ids:
        query = query.filter(model.team_id.in_(team_ids))
    rows = [{'id': r.id, 'team_id': r.team_id, 'date': r.date, **{c: getattr(r, c) for c in columns}}
            for r in query.all() if r.date.year in seasons]
    if max_dates:
        keep = sorted({r['date'] for r in rows})[:max_dates]
        rows = [r for r in rows if r['date'] in keep]
    return rows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--seasons', type=int, nargs='+', required=True)
    parser.add_argument('--team-ids', type=int, nargs='+')
    parser.add_argument('--max-dates', type=int, help='Only the first N snapshot dates (sampling)')
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--delay', type=float, default=0.1, help='Seconds each worker waits before a request')
    parser.add_argument('--output', required=True, help='JSONL file to write (never the database)')
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    session = connect_to_db()
    try:
        # Belt and braces: any accidental write in this process is rejected by Postgres.
        if session.bind.dialect.name == 'postgresql':
            session.execute(text('SET TRANSACTION READ ONLY'))
        work = []
        for t in TABLES:
            rows = load_rows(session, t, args.seasons, args.team_ids, args.max_dates)
            work += [(t, r) for r in rows]
            if not args.max_dates:  # sampling only covers stored rows
                keys = {(r['team_id'], r['date']) for r in rows}
                work += [(t, r) for r in find_missing(session, t, args.seasons, args.team_ids, keys)]
    finally:
        session.rollback()
        session.close()

    logging.info('Previewing %d stored snapshot rows (no database writes)', len(work))
    previewer = Previewer(args.workers, args.delay)
    counts: Counter = Counter()
    with open(args.output, 'w') as out, ThreadPoolExecutor(max_workers=args.workers) as pool:
        for result in pool.map(lambda w: previewer.preview_row(*w), work):
            counts[(result['table'], result['status'])] += 1
            out.write(json.dumps(result) + '\n')

    summary = {f'{t}.{s}': n for (t, s), n in sorted(counts.items())}
    Path(args.output + '.summary.json').write_text(json.dumps(
        {'generated_at': datetime.now().isoformat(), 'seasons': args.seasons,
         'rows': len(work), 'counts': summary}, indent=2))
    print(json.dumps(summary, indent=2))
    return 0 if not any(s == 'fetch_error' for (_, s) in counts) else 3


if __name__ == '__main__':
    sys.exit(main())
