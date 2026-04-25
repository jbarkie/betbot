# Sprint 4 Retrospective

**Sprint:** 4
**Date:** 2026-04-22
**Branch:** `feature/20260418_Sprint_4`
**PR:** #28

---

## Sprint Goal

Improve ML prediction reliability by fixing early-season data noise, and remove Docker as a local development dependency.

---

## Acceptance Criteria Results

### Issue 1 — ML rolling feature noise fix

| AC | Result | Notes |
|----|--------|-------|
| `prepare_training_data()` excludes games where either team has < N prior games | ✅ Met | Threshold set to N=10, not the initially proposed N=5 (see Surprises) |
| v2.1 test-set accuracy ≥ 55.0% | ⚠️ Near-miss | 54.57% — 0.43% short of target; accepted per plan guidance |
| All 103 backend tests pass | ✅ Met | 106 total after 3 new pipeline tests added |

### Issue 2 — Homebrew PostgreSQL migration

| AC | Result | Notes |
|----|--------|-------|
| API starts and serves `/mlb/games` without Docker | ⚠️ Not explicitly verified | Tests and scheduler pass; API startup not smoke-tested this session |
| All 103 tests pass without Docker | ✅ Met | |
| `CLAUDE.md` updated with Homebrew setup instructions | ✅ Met | |
| `docker-compose.yml` retained with CI/onboarding comment | ✅ Met | |

---

## Model Performance Summary

| Version | Accuracy | Training Games | Notes |
|---------|----------|---------------|-------|
| v1.0 | 59.1% | 808 | Late-season 2024 only; low variance |
| v2.0 | 53.8% | 4,322 | Full 2024+2025; early-season noise unfixed |
| v2.1 | 54.57% | 5,304 | Full 2024+2025; early-season games excluded (threshold=10) |

---

## Retrospective

### What Went Well

- Both sprint issues completed in a single session
- The root cause of the accuracy regression was correctly diagnosed and fixed — the threshold=10 approach is semantically clean (matches the rolling window size)
- Homebrew PostgreSQL migration was smooth once the correct DB name was identified
- 3 new unit tests cover the core behavioral change and document the threshold contract

### What Could Be Better

- The 55% accuracy AC was not met (54.57%). The gap between v1.0 (59.1%) and v2.1 (54.57%) is still large and unresolved — v1.0's advantage likely comes from training on lower-variance late-season data, not just the rolling window issue
- The API startup was not explicitly smoke-tested as part of AC verification
- N=5 threshold was proposed in the plan but proved insufficient; the plan should have specified "threshold equals rolling window size" as the rationale rather than a fixed N=5

### Surprises / Blockers

1. **Docker DB name mismatch** — `POSTGRES_DB=db` in `docker-compose.yml` creates a default database named `db`, but the application had separately created a database named `betbot`. Dumping `-d db` produced an empty dump. Fix: always inspect actual database names with `\l` before migrating.
2. **Homebrew install path** — postgresql@14 was installed at `/usr/local` (x86_64/Rosetta) not `/opt/homebrew` (arm64). `brew --prefix postgresql@14` resolves the correct path reliably.
3. **N=5 threshold had minimal impact** — Only removed ~114 games (2% of dataset). The remaining variance comes from games 6-9 where the rolling window is partially populated but still unreliable. Matching the threshold to the full window (N=10) removed 187 additional games and recovered 0.77% accuracy.

---

## Lessons Learned

1. **Match min_games_threshold to the rolling window** — Any threshold below the window size still includes games where rolling features are partially populated (NaN→0 for the missing slots). The semantically correct threshold is `N = rolling_window_size`
2. **Verify actual DB names before migrating** — `POSTGRES_DB` in docker-compose sets the default DB for the superuser, not necessarily what the application uses. Always run `psql \l` to confirm
3. **Use `brew --prefix <formula>` for binary paths** — Hardcoding `/opt/homebrew` or `/usr/local` breaks cross-architecture installs; `brew --prefix` always resolves correctly
4. **The v1.0 vs v2.x accuracy gap remains open** — The early-season filter helps but does not close the gap. v1.0 trained on late-season games with lower team-performance variance. Investigating season-relative weighting or post-All-Star-only retraining (with a fallback for April/May) remains a backlog item

---

## Improvement Actions Applied

- [x] Added 3 unit tests for `MLBDataPipeline.prepare_training_data()` threshold behavior
- [x] Updated `machine_learning/models/mlb/README.md` to reflect v2.1 as current model
- [x] Updated `README.md`, `machine_learning/README.md` to remove Docker DB references and reflect port 5432
