"""
Training-time data freshness check.

Answers one question before a model is fit: how old is the newest game with a
usable result, relative to the date the training run is targeting?

What counts as usable: a schedule row whose status is Final and whose scores
are both present. Scheduled or in-progress games never count, so a database
full of future fixtures cannot look fresh. Rows dated after the reference date
are ignored too, so an intentional historical run (``--end-date``) is judged
against its own window rather than against today.

Scope: this checks game-result recency at training time only. It says nothing
about team or pitcher statistics, and it does not monitor a model after it has
been deployed. In the offseason, raise the threshold explicitly.
"""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

import pandas as pd


@dataclass(frozen=True)
class FreshnessResult:
    newest_date: Optional[date]
    age_days: Optional[int]
    is_stale: bool
    reason: str
    reference_date: date
    max_staleness_days: int

    def to_metadata(self) -> dict:
        """Fields persisted alongside the model so later readers know what data it saw."""
        return {
            'newest_completed_game_date': self.newest_date.isoformat() if self.newest_date else None,
            'data_age_days': self.age_days,
            'max_staleness_days': self.max_staleness_days,
            'freshness_reference_date': self.reference_date.isoformat(),
        }


def _as_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return pd.Timestamp(value).date()


def check_data_freshness(
    schedule_df: pd.DataFrame,
    reference_date,
    max_staleness_days: int,
) -> FreshnessResult:
    """
    Report how old the newest completed game is relative to reference_date.

    Args:
        schedule_df: Schedule rows with at least date, status, home_score, away_score
        reference_date: The date the training run targets (its end_date)
        max_staleness_days: Largest acceptable age in days; exactly this many is fresh

    Returns:
        FreshnessResult. Empty input, no completed games, or no parseable dates all
        report stale, never fresh.
    """
    if max_staleness_days < 0:
        raise ValueError("max_staleness_days must be non-negative")

    ref = _as_date(reference_date)

    def stale(reason: str) -> FreshnessResult:
        return FreshnessResult(None, None, True, reason, ref, max_staleness_days)

    if schedule_df is None or len(schedule_df) == 0:
        return stale("no schedule rows")

    required = {'date', 'status', 'home_score', 'away_score'}
    missing = required - set(schedule_df.columns)
    if missing:
        return stale(f"schedule is missing columns: {sorted(missing)}")

    completed = schedule_df[
        (schedule_df['status'] == 'Final')
        & schedule_df['home_score'].notna()
        & schedule_df['away_score'].notna()
    ]
    if completed.empty:
        return stale("no completed games with recorded scores")

    dates = pd.to_datetime(completed['date'], errors='coerce').dropna()
    if dates.empty:
        return stale("completed games have no parseable dates")

    dates = dates.dt.normalize()
    on_or_before = dates[dates.dt.date <= ref]
    if on_or_before.empty:
        return stale(f"no completed games on or before {ref.isoformat()}")

    newest = on_or_before.max().date()
    age = (ref - newest).days
    is_stale = age > max_staleness_days
    reason = (
        f"newest completed game is {age} day(s) old; limit is {max_staleness_days}"
        if is_stale else
        f"newest completed game is {age} day(s) old, within {max_staleness_days}"
    )
    return FreshnessResult(newest, age, is_stale, reason, ref, max_staleness_days)
