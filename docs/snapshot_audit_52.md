# Historical team-stat snapshot audit (#52) — DRAFT

Run 2026-10-20 against the local `betbot` database and the MLB Stats API. Read-only:
no database rows were written, no model was retrained, nothing was applied. The
recent-row repair (2026-09-26 onward) is separate and still waiting for approval; see
`docs/sprint8_operations_followup.md`.

## What was checked

1. **Structure of every stored snapshot row** for 2024-2026, regular-season dates
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
- `mlb_schedule` is not a reliable reference. For team 108 in 2024 it holds 169
  completed games between Mar 20 and Sep 29, where a season has 162, so its derived
  totals do not equal true totals. The schedule-derived match counts above are a rough
  signal only; the API sample is the real evidence.
- Which stored rows the v3.3 model saw cannot be read from its metadata (it records
  train and test sizes of 5,400 and 1,350, not a date range). The model was trained on
  2026-08-11, before any repair.
- **Not shown:** whether the damage helped or hurt the reported accuracy of 56.44%
  (AUC 0.5708). That number was measured on features that were wrong for most training
  rows, so it should not be treated as a trustworthy estimate until the data is
  repaired and the model retrained and re-evaluated.

## Proposed repair scope (needs your approval; nothing here is authorized)

1. Widen the existing preview/apply/restore utility
   (`machine_learning/scripts/repair_team_stat_snapshots.py`) from `--from-date
   2026-09-26` back to the first stored date, 2024-03-20. That is about 18,200 rows per
   table, roughly 19 times the 959-row recent preview, so expect a long preview run and
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
3. Only after an approved apply, retrain and compare against v3.3 on the same
   held-out games, with the freshness gate on.
4. Until then, treat v3.3 predictions as unvalidated.

Open questions for you: whether the earlier spec ("repair only rows dated 2026-09-26
onward") should be widened, and whether to leave v3.3 serving in the meantime.
