"""
Inference-time starting pitcher lookup.

Resolves the starting pitcher stats for a game about to be predicted, in three
descending tiers of confidence:

1. A stored row in mlb_pitcher_stats — exact, already leakage-checked, used for
   games the backfill has covered.
2. The announced probable starter from the MLB Stats API, with cumulative stats
   computed from that pitcher's earlier starts this season — used for upcoming
   games the backfill cannot know about yet.
3. The medians recorded in the trained model's metadata — used when a starter has
   not been announced or the API is unreachable.

Tier 3 is why nothing here raises. A missing starter is an ordinary daily
occurrence, not an error, and it must never turn into a 500.
"""

import json
import logging
import time
from typing import Dict, Optional, Tuple

from sqlalchemy.orm import Session

from api.src.ml_config import MLB_MODELS_DIR, MLB_MODEL_CONFIG, MLB_PITCHER_FEATURES

logger = logging.getLogger(__name__)

# Probable starters are announced a day or two out and rarely change intraday, so
# a short cache keeps a burst of requests for the same game to one API round trip.
_CACHE_TTL_SECONDS = 900

_stats_cache: Dict[str, Tuple[float, Dict]] = {}
_medians_cache: Optional[Dict[str, float]] = None

# Used only when a model predates pitcher features or its metadata is unreadable.
# Roughly league-average values, chosen so a missing starter reads as unremarkable
# rather than as an ace or a disaster.
_FALLBACK_MEDIANS = {
    'home_starter_era': 4.00,
    'home_starter_whip': 1.30,
    'home_starter_k9': 8.00,
    'away_starter_era': 4.00,
    'away_starter_whip': 1.30,
    'away_starter_k9': 8.00,
}


def get_pitcher_medians() -> Dict[str, float]:
    """
    Read the imputation medians the production model was trained with.

    Serving has to fill a missing starter with the same value training used;
    recomputing from live data would drift away from what the model was fit on.

    Returns:
        Mapping of pitcher feature name to median value
    """
    global _medians_cache

    if _medians_cache is not None:
        return _medians_cache

    medians = dict(_FALLBACK_MEDIANS)
    try:
        metadata_path = MLB_MODELS_DIR / MLB_MODEL_CONFIG['metadata_file']
        with open(metadata_path) as f:
            stored = json.load(f).get('pitcher_medians') or {}
        for key in MLB_PITCHER_FEATURES:
            if key in stored and stored[key] is not None:
                medians[key] = float(stored[key])
    except (OSError, ValueError, KeyError) as e:
        logger.warning(f"Falling back to default pitcher medians: {e}")

    _medians_cache = medians
    return medians


def reset_caches() -> None:
    """Clear cached medians and pitcher stats. Intended for tests."""
    global _medians_cache
    _medians_cache = None
    _stats_cache.clear()


def resolve_game_pk(
    session: Session,
    home_team_id: int,
    away_team_id: int,
    game_date,
) -> Optional[str]:
    """
    Find the MLB gamePk for a game identified by its matchup and date.

    The analytics endpoint is keyed by the Odds table's id, which is an opaque
    hash from the odds provider and shares nothing with MLB's gamePk. Every
    pitcher source is keyed by gamePk, so the two have to be bridged here.

    Odds times are stored as UTC datetimes while the schedule stores local game
    dates, so a late first pitch can land on the following calendar day. The
    search spans a one-day window on either side to absorb that.

    Args:
        session: Database session
        home_team_id: Home team MLB ID
        away_team_id: Away team MLB ID
        game_date: Date or datetime of the game

    Returns:
        gamePk as a string, or None when no matching scheduled game is found
    """
    try:
        from datetime import timedelta
        from machine_learning.data.models.mlb_models import MLBSchedule

        target = game_date.date() if hasattr(game_date, 'date') else game_date

        row = session.query(MLBSchedule).filter(
            MLBSchedule.home_team_id == int(home_team_id),
            MLBSchedule.away_team_id == int(away_team_id),
            MLBSchedule.date >= target - timedelta(days=1),
            MLBSchedule.date <= target + timedelta(days=1),
        ).order_by(MLBSchedule.date).first()

        return str(row.game_id) if row and row.game_id else None
    except Exception as e:
        logger.warning(f"Could not resolve gamePk for {away_team_id}@{home_team_id}: {e}")
        return None


def _stored_stats(session: Session, game_id: str, team_id: int) -> Optional[Dict]:
    """Read a pre-computed row from mlb_pitcher_stats, if the backfill covered it."""
    try:
        from machine_learning.data.models.mlb_models import MLBPitcherStats

        row = session.query(MLBPitcherStats).filter(
            MLBPitcherStats.game_id == str(game_id),
            MLBPitcherStats.team_id == int(team_id),
        ).first()

        if row is None or row.era is None:
            return None

        return {'era': row.era, 'whip': row.whip, 'k9': row.k9}
    except Exception as e:
        logger.warning(f"Stored pitcher lookup failed for game {game_id}: {e}")
        return None


def _live_stats(game_id: str, game_date, collector=None) -> Dict[int, Dict]:
    """
    Fetch announced starters for a game and compute their season-to-date lines.

    Returns:
        Mapping of team_id to {era, whip, k9}; empty when nothing is announced
    """
    from machine_learning.data.collection.mlb_pitcher_stats import (
        MLBPitcherStatsCollector,
        compute_cumulative_before,
    )

    collector = collector or MLBPitcherStatsCollector()
    season = game_date.year
    before = game_date.strftime('%Y-%m-%d') if hasattr(game_date, 'strftime') else None

    resolved = {}
    for team_id, pitcher in collector.get_probable_pitchers(game_id).items():
        splits = collector.get_game_log(pitcher['pitcher_id'], season)
        if not splits:
            continue
        stats = compute_cumulative_before(splits, before_date=before)
        if stats.get('era') is not None:
            resolved[team_id] = stats

    return resolved


def get_starting_pitcher_features(
    session: Session,
    home_team_id: int,
    away_team_id: int,
    game_date,
    collector=None,
) -> Dict[str, float]:
    """
    Build the six starting pitcher features for one game.

    Never raises and never returns a partial dict: every one of the six keys is
    always present, median-imputed where real data could not be resolved.

    Args:
        session: Database session
        home_team_id: Home team MLB ID
        away_team_id: Away team MLB ID
        game_date: Date or datetime of the game
        collector: Optional collector instance (injected in tests)

    Returns:
        Dict of the six pitcher feature names to float values
    """
    medians = get_pitcher_medians()
    features = dict(medians)

    target = game_date.date() if hasattr(game_date, 'date') else game_date
    cache_key = f"{home_team_id}:{away_team_id}:{target}"
    cached = _stats_cache.get(cache_key)
    if cached and (time.time() - cached[0]) < _CACHE_TTL_SECONDS:
        return dict(cached[1])

    try:
        game_id = resolve_game_pk(session, home_team_id, away_team_id, game_date)
        if game_id is None:
            _stats_cache[cache_key] = (time.time(), dict(features))
            return features

        by_team: Dict[int, Dict] = {}

        for team_id in (home_team_id, away_team_id):
            stored = _stored_stats(session, game_id, team_id)
            if stored:
                by_team[int(team_id)] = stored

        # Only reach for the network if the database did not already answer.
        if len(by_team) < 2:
            try:
                for team_id, stats in _live_stats(game_id, game_date, collector).items():
                    by_team.setdefault(int(team_id), stats)
            except Exception as e:
                logger.warning(f"Live pitcher lookup failed for game {game_id}: {e}")

        for prefix, team_id in (('home', home_team_id), ('away', away_team_id)):
            stats = by_team.get(int(team_id))
            if not stats:
                continue
            for stat in ('era', 'whip', 'k9'):
                value = stats.get(stat)
                if value is not None:
                    features[f'{prefix}_starter_{stat}'] = float(value)

        _stats_cache[cache_key] = (time.time(), dict(features))

    except Exception as e:
        logger.warning(f"Pitcher feature resolution failed for game {game_id}: {e}")

    return features
