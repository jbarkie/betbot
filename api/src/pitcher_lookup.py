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

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, Optional, Tuple

from sqlalchemy.orm import Session

from api.src.ml_config import MLB_MODELS_DIR, MLB_MODEL_CONFIG, MLB_PITCHER_FEATURES
from api.src.pitcher_telemetry import record_event

logger = logging.getLogger(__name__)

# Probable starters are announced a day or two out and rarely change intraday, so
# a short cache keeps a burst of requests for the same game to one API round trip.
# A failed live lookup is cached for the same TTL, so one bad request does not
# retry on every page load.
_CACHE_TTL_SECONDS = 900

# The serving network work has one cancellable budget across all three calls.
# Database queries and prediction computation are outside this budget.
SERVING_API_TIMEOUT_SECONDS = 5
LIVE_LOOKUP_BUDGET_SECONDS = 5

_stats_cache: Dict[str, Tuple[float, Dict, Dict]] = {}
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


async def _live_stats_async(game_id: str, game_date, collector=None, telemetry=None) -> Dict[int, Dict]:
    """Cancel network work at the shared deadline, retaining completed sides."""
    import httpx
    from api.src.live_pitcher_stats import LivePitcherStatsCollector
    from machine_learning.data.collection.mlb_pitcher_stats import compute_cumulative_before

    resolved = {}
    telemetry = telemetry if telemetry is not None else {}
    telemetry.setdefault('lookup_id', uuid.uuid4().hex)
    telemetry['reasons'] = {}
    started = time.perf_counter()
    outcome, stage, active_team = 'completed', 'probable_pitchers', None

    async def collect(source):
        nonlocal stage, active_team, outcome
        probables = await source.get_probable_pitchers(game_id)
        if getattr(source, 'last_error', None):
            outcome = 'upstream_error'
            telemetry['reasons'].update({t: source.last_error for t in telemetry.get('team_ids', [])})
            return
        for team_id in telemetry.get('team_ids', []):
            if team_id not in probables:
                telemetry['reasons'][team_id] = 'starter_not_announced'
        for team_id, pitcher in probables.items():
            stage, active_team = 'game_log', team_id
            splits = await source.get_game_log(pitcher['pitcher_id'], game_date.year)
            if getattr(source, 'last_error', None):
                outcome = 'upstream_error'
                telemetry['reasons'][team_id] = source.last_error
                continue
            stats = compute_cumulative_before(splits, before_date=game_date.strftime('%Y-%m-%d'))
            if stats.get('era') is not None:
                resolved[team_id] = stats
            else:
                telemetry['reasons'][team_id] = 'no_usable_pregame_stats'

    async def run():
        if collector is not None:
            await collect(collector)
        else:
            async with httpx.AsyncClient(timeout=SERVING_API_TIMEOUT_SECONDS) as client:
                await collect(LivePitcherStatsCollector(
                    client, lookup_id=telemetry['lookup_id'], game_id=str(game_id)
                ))

    try:
        await asyncio.wait_for(run(), timeout=LIVE_LOOKUP_BUDGET_SECONDS)
    except asyncio.TimeoutError:
        outcome = 'budget_exhausted'
        logger.warning("Live pitcher lookup exhausted its %.1fs network budget", LIVE_LOOKUP_BUDGET_SECONDS)
    except asyncio.CancelledError:
        outcome = 'cancelled'
        raise
    except Exception as exc:
        outcome = 'lookup_error'
        logger.warning("Live pitcher lookup failed: %s", exc)
    finally:
        telemetry['outcome'] = outcome
        for team_id in telemetry.get('team_ids', []):
            if team_id not in resolved:
                telemetry['reasons'].setdefault(
                    team_id, outcome if outcome != 'completed' else 'no_usable_pregame_stats'
                )
        record_event(
            'pitcher_live_lookup', lookup_id=telemetry['lookup_id'], game_id=str(game_id),
            elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
            budget_ms=LIVE_LOOKUP_BUDGET_SECONDS * 1000, outcome=outcome,
            stage=stage, active_team_id=active_team,
            resolved_team_ids=sorted(resolved),
            fallback_reasons=telemetry['reasons'],
        )
    return resolved


def _live_stats(game_id: str, game_date, collector=None, live_loop=None, telemetry=None) -> Dict[int, Dict]:
    # Called from the analytics worker, never from the API event loop. Cancelling
    # async HTTP closes its connection rather than abandoning a requests thread.
    work = _live_stats_async(game_id, game_date, collector, telemetry)
    if live_loop is not None:
        # Use the server loop so returning a timed-out lookup never waits for a
        # temporary loop's DNS executor to shut down. No DB objects cross over.
        return asyncio.run_coroutine_threadsafe(work, live_loop).result()
    return asyncio.run(work)


def get_starting_pitcher_features(
    session: Session,
    home_team_id: int,
    away_team_id: int,
    game_date,
    collector=None,
    live_loop=None,
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
    started = time.perf_counter()
    lookup_id = uuid.uuid4().hex

    target = game_date.date() if hasattr(game_date, 'date') else game_date
    cache_key = f"{home_team_id}:{away_team_id}:{target}"
    cached = _stats_cache.get(cache_key)
    if cached and (time.time() - cached[0]) < _CACHE_TTL_SECONDS:
        record_event(
            'pitcher_features', lookup_id=lookup_id, cache_hit=True,
            cache_age_seconds=round(time.time() - cached[0], 3), live_attempted=False,
            elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
            home_team_id=home_team_id, away_team_id=away_team_id,
            game_date=target.isoformat(), **cached[2],
        )
        return dict(cached[1])

    game_id = None
    live_attempted = False
    cache_result = True
    telemetry = {'lookup_id': lookup_id, 'team_ids': [home_team_id, away_team_id]}
    provenance = {
        side: {'sources': {stat: 'fallback' for stat in ('era', 'whip', 'k9')},
               'fallback_reason': 'game_not_resolved'}
        for side in ('home', 'away')
    }
    try:
        game_id = resolve_game_pk(session, home_team_id, away_team_id, game_date)
        if game_id is None:
            return features

        by_team: Dict[int, Dict] = {}
        sources = {}

        for team_id in (home_team_id, away_team_id):
            stored = _stored_stats(session, game_id, team_id)
            if stored:
                by_team[int(team_id)] = stored
                sources[int(team_id)] = 'stored'

        # Only reach for the network if the database did not already answer.
        if len(by_team) < 2:
            live_attempted = True
            telemetry['team_ids'] = [t for t in (home_team_id, away_team_id) if int(t) not in by_team]
            try:
                for team_id, stats in _live_stats(game_id, game_date, collector, live_loop, telemetry).items():
                    if int(team_id) not in by_team:
                        sources[int(team_id)] = 'live'
                    by_team.setdefault(int(team_id), stats)
            except Exception as e:
                telemetry['outcome'] = 'lookup_error'
                logger.warning(f"Live pitcher lookup failed for game {game_id}: {e}")

        for prefix, team_id in (('home', home_team_id), ('away', away_team_id)):
            stats = by_team.get(int(team_id))
            provenance[prefix]['fallback_reason'] = telemetry.get('reasons', {}).get(
                int(team_id), telemetry.get('outcome', 'no_usable_pregame_stats')
            )
            if not stats:
                continue
            for stat in ('era', 'whip', 'k9'):
                value = stats.get(stat)
                if value is not None:
                    features[f'{prefix}_starter_{stat}'] = float(value)
                    provenance[prefix]['sources'][stat] = sources[int(team_id)]
            provenance[prefix]['fallback_reason'] = (
                'incomplete_stats' if 'fallback' in provenance[prefix]['sources'].values() else None
            )

    except Exception as e:
        cache_result = False
        for side in provenance.values():
            if 'fallback' in side['sources'].values():
                side['fallback_reason'] = 'feature_resolution_error'
        logger.warning(f"Pitcher feature resolution failed for game {game_id}: {e}")
    finally:
        metadata = {'game_id': game_id, 'origin_lookup_id': lookup_id, **provenance}
        if cache_result:
            _stats_cache[cache_key] = (time.time(), dict(features), metadata)
        record_event(
            'pitcher_features', lookup_id=lookup_id, cache_hit=False,
            cache_age_seconds=None, live_attempted=live_attempted,
            elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
            home_team_id=home_team_id, away_team_id=away_team_id,
            game_date=target.isoformat(), **metadata,
        )

    return features
