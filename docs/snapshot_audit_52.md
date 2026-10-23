# Historical team-stat snapshot audit (#52) — DRAFT

Run 2026-10-20 against the local `betbot` database and the MLB Stats API. Read-only:
no database rows were written, no model was retrained, nothing was applied. The
recent-row repair (2026-09-26 onward) is separate and still waiting for approval; see
`docs/sprint8_operations_followup.md`.

## What was checked

1. **Structure of every stored snapshot row** for 2024-2026, a calendar window
   (Mar 20 to Sep 30): how many distinct `runs_scored` values each team holds across a
   season, and whether the values ever decrease from one date to the next.
2. **A date-correct sample from the MLB API**: 6 teams (108, 119, 111, 147, 137, 158)
   at 4 dates per year (Apr 15, Jun 15, Aug 15, Sep 20 or 25), 72 team-dates in all.
   For each, the stored offense `runs_scored` was compared with the API's cumulative
   regular-season runs from Jan 1 through that date (the contract), and with the
   season-end total.
3. A cross-check against runs derived from `mlb_schedule` (see the caveat below).

## Findings

| Season | What the stored rows look like | API sample (24 team-dates) |
|---|---|---|
| 2024 | Every team holds **one single value for the whole season** (all 30 teams, one distinct value each, never changes). Team 108 stores 635 on every date. | **24 of 24** equal the **season-end total**. 0 equal the correct through-date value. |
| 2025 | Two to four distinct values per team across the season, changing on irregular dates (first changes on Apr 23, Jun 12, Jun 27, Aug 13 and later). | 6 equal the season-end total, **18 equal neither** value. 0 equal the correct through-date value. |
| 2026 | Mixed. About 3,129 of 5,580 regular-season offense rows equal schedule-derived cumulative runs. 86 decreases between consecutive dates, which a cumulative count cannot do. | **20 of 24** equal the correct through-date value; 4 equal neither. |

Reading these together:

- **2024:** the stored snapshot for any game date holds the whole season's totals, so
  every 2024 game's "pre-game" team features include games played after it.
- **2025:** the stored values are not date-correct either, and are mostly not season totals.
- **2026:** largely correct, with windowed values mixed in; the recent-row repair covers
  only Sep 26 onward, so earlier 2026 rows that are wrong remain wrong.

Defense (`mlb_defensive_stats`) was checked structurally only (same shape of match
counts as offense: 6 of 5,670 in 2024, 17 of 5,490 in 2025, 3,132 of 5,580 in 2026
against schedule-derived runs allowed). It was **not** sampled against the API.

## Caveats (what this does not establish)

- The API sample is 72 team-dates for runs only. It is strong evidence for the 2024
  pattern (24 of 24) and a real signal for 2025 and 2026, not a full audit of every
  stat column or every row.
- The unfiltered schedule totals mix game types and cannot validate regular-season
  snapshots. Follow-up review matched all 169 stored game IDs for team 108 between
  2024-03-20 and 2024-09-29 to the official MLB schedule: **162 regular-season (`R`)
  and seven spring-training (`S`) games**. This count does not establish corrupt or
  duplicate records. The match counts above remain historical, unfiltered results;
  recompute them after game-type validation.
- Which stored rows the v3.3 model saw cannot be read from its metadata (it records
  train and test sizes of 5,400 and 1,350, not a date range). The model was trained on
  2026-08-11, before any repair.
- **Not shown:** whether the damage helped or hurt the reported accuracy of 56.44%
  (AUC 0.5708). The audit establishes historical data defects, not the exact number
  of affected feature vectors in the saved model. Treat the score as unvalidated
  until the data and game eligibility are corrected and the model is re-evaluated.

## Schedule finding and retraining prerequisite

The official query used for the follow-up was
`GET https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId=108&startDate=2024-03-20&endDate=2024-09-29`.
Match its `gamePk` to stored `game_id`, and inspect `gameType`; do not infer type
from a shared calendar window. Spring-training game `747883` on 2024-03-20 finished
8–8. The other six spring IDs are `747881`, `747850`, `747836`, `747822`, `747811`,
and `747801`.

`mlb_schedule` currently stores no game type. In `mlb_data_pipeline.py`, training
selects dates and `status == 'Final'`, while `home_score > away_score` labels ties
as home losses. The same schedule supplies rolling and head-to-head features.
These are existing behaviors, not changes introduced by this documentation PR.
Whether this particular game survived v3.3's minimum-history filter is unverified.

Before a new regular-season evaluation, preserve/resolve game type, exclude
non-regular games from both training targets and feature histories, and exclude
ties and missing scores from binary win/loss targets. Verify historical game IDs,
dates and scores against the API. Decide postseason serving behavior explicitly;
do not delete legitimate non-regular games merely to make counts equal 162.

## Proposed repair scope (needs your approval; nothing here is authorized)

1. Widen the existing preview/apply/restore utility
   (`machine_learning/scripts/repair_team_stat_snapshots.py`) from `--from-date
   2026-09-26` back to the first stored date, 2024-03-20. That is about 18,200 rows per
   table, roughly 38 times the 959-row recent preview in total, so expect a long preview run and
   gentle request pacing. The utility already refuses to apply a partial, ambiguous or
   hash-mismatched preview, preserves row IDs, and can restore.
   **Known blocker for widening:** the utility treats "API returned no stats" as a
   blocking `missing_response`. The API returns nothing for a team before its first game
   of the year (team 108 returns no stats for 2024-01-01 through 2024-03-27, and stats
   from 2024-03-28), and the table holds about 40 offense rows dated before their team's
   first game. A widened preview would therefore be refused at apply. A decision is
   needed first on what a correct snapshot is on those dates (no row, or zeros), and
   the utility needs a code change to handle it. An independent review of the script
   (2026-10-20) also recommends retry/resume for failed requests, row locking during
   apply, and bulk queries before running it on tens of thousands of rows.
2. Review a preview of the whole range (counts per year, and a sample of proposed
   values) before any apply.
3. Resolve the schedule/game-eligibility prerequisite above as well as the snapshot
   repair before retraining. Save chronological train/test game IDs and dates;
   evaluate candidates on the same clean holdout. Use an untouched later period
   for a fair comparison with v3.3 if its original split cannot be reconstructed.
   Keep the freshness gate on with an explicit, justified offseason threshold.
   Freshness checks recency, not correctness.
4. Until then, treat v3.3 predictions as unvalidated.

Open questions for you: whether the earlier spec ("repair only rows dated 2026-09-26
onward") should be widened, and whether to leave v3.3 serving in the meantime.

The proposed execution order, acceptance criteria, and separate operational
approval are recorded in `ALL_SPRINTS_MASTER_PLAN.md` under
“Post-Sprint-8 data correctness”.
