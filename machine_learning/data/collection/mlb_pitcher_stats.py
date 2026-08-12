"""
Starting Pitcher Stats Collection

Builds cumulative pre-game ERA/WHIP/K9 for the starting pitcher of each team in
each game, sourced from MLB Stats API pitching game logs via direct HTTP (the
same pattern used for team stats).

The no-leakage guarantee comes from how the stats are accumulated: a pitcher's
game log is walked in chronological order, and the row written for a given start
contains only totals from that pitcher's *earlier* starts in the same season. The
game being described never contributes to its own features, and neither does any
later game.
"""

import logging
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from sqlalchemy.orm import Session

from .mlb_direct_api import MLBDirectAPI
from ..models.mlb_models import MLBPitcherStats, MLBSchedule


def parse_innings_pitched(value: Any) -> float:
    """
    Convert an MLB innings-pitched string into a true inning count.

    The API reports innings in "outs" notation, where the digit after the decimal
    point is a count of outs rather than a fraction: "4.1" means four and one
    third innings, not 4.1. Treating the string as a plain float understates
    thirds and inflates every rate stat derived from it.

    Args:
        value: Innings pitched as reported by the API (for example "6.2")

    Returns:
        Innings as a float (for example 6.6667), or 0.0 if unparseable
    """
    if value is None:
        return 0.0

    text = str(value).strip()
    if not text:
        return 0.0

    whole, _, outs = text.partition('.')

    try:
        innings = float(int(whole or 0))
    except ValueError:
        return 0.0

    if outs:
        try:
            innings += int(outs[0]) / 3.0
        except ValueError:
            pass

    return innings


def compute_rate_stats(totals: Dict[str, float]) -> Dict[str, Optional[float]]:
    """
    Derive ERA, WHIP, and K/9 from accumulated counting stats.

    Args:
        totals: Accumulated innings_pitched, earned_runs, hits, walks, strikeouts

    Returns:
        Dict with era, whip, and k9. All three are None when no innings have been
        pitched, since the rates are undefined rather than zero.
    """
    innings = totals.get('innings_pitched', 0.0)

    if innings <= 0:
        return {'era': None, 'whip': None, 'k9': None}

    return {
        'era': round(9.0 * totals.get('earned_runs', 0) / innings, 4),
        'whip': round((totals.get('hits', 0) + totals.get('walks', 0)) / innings, 4),
        'k9': round(9.0 * totals.get('strikeouts', 0) / innings, 4),
    }


def _is_start(split: Dict) -> bool:
    """Return True when a game log split represents a start."""
    try:
        return int(split.get('stat', {}).get('gamesStarted', 0) or 0) == 1
    except (TypeError, ValueError):
        return False


def _accumulate(totals: Dict[str, float], stat: Dict) -> None:
    """Add one game's counting stats into a running total, in place."""
    def as_int(key: str) -> int:
        try:
            return int(stat.get(key, 0) or 0)
        except (TypeError, ValueError):
            return 0

    totals['innings_pitched'] += parse_innings_pitched(stat.get('inningsPitched'))
    totals['earned_runs'] += as_int('earnedRuns')
    totals['hits'] += as_int('hits')
    totals['walks'] += as_int('baseOnBalls')
    totals['strikeouts'] += as_int('strikeOuts')


def build_pregame_rows(splits: List[Dict]) -> List[Dict]:
    """
    Turn one pitcher-season game log into one pre-game stat row per start.

    Splits are sorted by date before accumulating, so the caller does not have to
    rely on the API returning them in order. Only starts produce rows, and only
    prior starts contribute to the totals, matching the Card 2 specification.

    Args:
        splits: Game log splits for a single pitcher and season

    Returns:
        List of dicts with game_id, team_id, era, whip, k9 (rates None before the
        pitcher's first start of the season)
    """
    ordered = sorted(splits, key=lambda s: s.get('date') or '')

    totals = {
        'innings_pitched': 0.0,
        'earned_runs': 0,
        'hits': 0,
        'walks': 0,
        'strikeouts': 0,
    }

    rows: List[Dict] = []

    for split in ordered:
        if not _is_start(split):
            continue

        game_pk = split.get('game', {}).get('gamePk')
        team_id = split.get('team', {}).get('id')

        if game_pk is None or team_id is None:
            continue

        # Snapshot the totals *before* folding this start in.
        row = {'game_id': str(game_pk), 'team_id': int(team_id)}
        row.update(compute_rate_stats(totals))
        rows.append(row)

        _accumulate(totals, split.get('stat', {}))

    return rows


class MLBPitcherStatsCollector:
    """Fetches pitcher game logs and rosters from the MLB Stats API."""

    def __init__(self, api_client: Optional[MLBDirectAPI] = None):
        self.api = api_client or MLBDirectAPI()

    def get_team_pitchers(self, team_id: int, season: int) -> List[Dict]:
        """
        List every pitcher who appeared on a team's full-season roster.

        Args:
            team_id: MLB team ID
            season: Four-digit season year

        Returns:
            List of dicts with pitcher_id and pitcher_name (empty on failure)
        """
        data = self.api._make_request(
            f"teams/{team_id}/roster",
            {'rosterType': 'fullSeason', 'season': season}
        )

        if not data:
            return []

        pitchers = []
        for entry in data.get('roster', []):
            if entry.get('position', {}).get('abbreviation') != 'P':
                continue
            person = entry.get('person', {})
            if person.get('id') is None:
                continue
            pitchers.append({
                'pitcher_id': int(person['id']),
                'pitcher_name': person.get('fullName'),
            })

        return pitchers

    def get_game_log(self, pitcher_id: int, season: int) -> List[Dict]:
        """
        Fetch a pitcher's pitching game log for one season.

        Args:
            pitcher_id: MLB person ID
            season: Four-digit season year

        Returns:
            List of game log splits (empty on failure or no appearances)
        """
        data = self.api._make_request(
            f"people/{pitcher_id}/stats",
            {'stats': 'gameLog', 'group': 'pitching', 'season': season}
        )

        if not data:
            return []

        for group in data.get('stats', []):
            if group.get('type', {}).get('displayName') == 'gameLog':
                return group.get('splits', []) or []

        return []


def collect_pitcher_stats(
    session: Session,
    seasons: Optional[Iterable[int]] = None,
    collector: Optional[MLBPitcherStatsCollector] = None,
) -> Dict[str, int]:
    """
    Populate mlb_pitcher_stats for every scheduled game in the given seasons.

    Idempotent: existing (game_id, team_id) pairs are loaded up front and skipped,
    so re-running adds only genuinely new starts and never duplicates a row.

    Args:
        session: Database session
        seasons: Seasons to collect; defaults to every season present in mlb_schedule
        collector: Optional collector instance (injected in tests)

    Returns:
        Counts of rows inserted, rows skipped as already present, and pitchers
        whose game log could not be retrieved
    """
    collector = collector or MLBPitcherStatsCollector()

    if seasons is None:
        seasons = sorted({
            date.year
            for (date,) in session.query(MLBSchedule.date).distinct().all()
            if date is not None
        })
    seasons = list(seasons)

    # Only write rows for games we actually track, and only for their two teams.
    known_games: Set[Tuple[str, int]] = set()
    team_ids: Set[int] = set()
    for game_id, home_id, away_id in session.query(
        MLBSchedule.game_id, MLBSchedule.home_team_id, MLBSchedule.away_team_id
    ).all():
        if game_id is None:
            continue
        for team_id in (home_id, away_id):
            if team_id is not None:
                known_games.add((str(game_id), int(team_id)))
                team_ids.add(int(team_id))

    existing: Set[Tuple[str, int]] = {
        (str(game_id), int(team_id))
        for game_id, team_id in session.query(
            MLBPitcherStats.game_id, MLBPitcherStats.team_id
        ).all()
        if game_id is not None and team_id is not None
    }

    logging.info(
        f'Collecting pitcher stats for seasons {seasons}: '
        f'{len(known_games)} game-team slots, {len(existing)} already stored'
    )

    counts = {'inserted': 0, 'skipped': 0, 'failed_pitchers': 0}

    for season in seasons:
        # Dedupe pitchers across rosters — traded players appear on more than one.
        roster: Dict[int, Optional[str]] = {}
        for team_id in sorted(team_ids):
            for pitcher in collector.get_team_pitchers(team_id, season):
                roster.setdefault(pitcher['pitcher_id'], pitcher['pitcher_name'])

        logging.info(f'Season {season}: {len(roster)} unique pitchers on full-season rosters')

        for pitcher_id, pitcher_name in roster.items():
            splits = collector.get_game_log(pitcher_id, season)
            if not splits:
                counts['failed_pitchers'] += 1
                continue

            for row in build_pregame_rows(splits):
                key = (row['game_id'], row['team_id'])

                if key not in known_games:
                    continue
                if key in existing:
                    counts['skipped'] += 1
                    continue

                session.add(MLBPitcherStats(
                    game_id=row['game_id'],
                    team_id=row['team_id'],
                    pitcher_id=pitcher_id,
                    pitcher_name=pitcher_name,
                    era=row['era'],
                    whip=row['whip'],
                    k9=row['k9'],
                ))
                existing.add(key)
                counts['inserted'] += 1

        session.commit()
        logging.info(
            f'Season {season} committed — inserted: {counts["inserted"]}, '
            f'skipped: {counts["skipped"]}, failed pitchers: {counts["failed_pitchers"]}'
        )

    return counts
