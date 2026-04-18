# Sprint 3 Retrospective

**Date:** 2026-04-18
**Branch:** `feature/20260417_Sprint_3`
**PR:** #26
**Issues:** #23, #24, #25

---

## Sprint Goal

Backfill the full 2024+2025 MLB dataset and retrain the ML model on the expanded data to improve prediction quality.

---

## Acceptance Criteria Outcomes

| Issue | Criterion | Result |
|-------|-----------|--------|
| #23 | `--start-date/--end-date` args control stats fetch range | ✅ Met |
| #23 | No-args run defaults to last 30 days | ✅ Met |
| #24 | `MLBOffensiveStats` 2025 rows ≥ 5,000 | ✅ Met — 6,750 rows |
| #24 | `MLBDefensiveStats` 2025 rows ≥ 5,000 | ✅ Met — 6,750 rows |
| #25 | `training_samples` exceeds pre-sprint value | ✅ Met — 4,322 vs 808 |
| #25 | Model version incremented | ✅ Met — v1.0 → v2.0 |

All 6 acceptance criteria met. However, a quality regression was observed (see Surprises).

---

## Commits

- `4b628a4` fix: propagate --start-date/--end-date CLI args to team stats fetch (#23)
- `f39d70c` feat: retrain MLB model v2.0 on full 2024+2025 dataset and fix training parallelism (#25)
- `f71997c` chore: add v2.0 model metadata (trained on 2024+2025 dataset) (#25)
- `f7ea901` fix: fast-fail scheduler when Docker not running, fix null win probability display
- `0f16e4b` docs: update CLAUDE.md scheduler gotcha to reflect fast-fail behavior
- `0794442` docs: update MLB models README to reflect v2.0 as current model
- `bd095f2` fix: remove log noise from scheduled MLB data updates

---

## Model v2.0 Performance

| Metric | v1.0 (808 games) | v2.0 (4,322 games) | Delta |
|--------|------------------|--------------------|-------|
| Accuracy | 59.1% | 53.8% | -5.3% |
| Precision | 59.4% | 55.4% | -3.9% |
| Recall | 71.0% | 72.7% | +1.7% |
| F1 | 64.7% | 62.9% | -1.8% |
| ROC AUC | 60.9% | 54.8% | -6.0% |

---

## Retrospective

### What Went Well
- All sprint ACs met in a single session
- OOM issue diagnosed and fixed quickly (n_jobs parallelism)
- Three post-sprint bugs caught and fixed before PR merge: scheduler hang, null probability display, log noise
- Most complete documentation pass of any sprint to date

### What Didn't Go Well
- Training OOM was not anticipated at planning time despite the dataset being 5× larger
- v2.0 underperformed v1.0 across all metrics except recall — the sprint ACs passed without catching this quality regression
- Sprint ACs were output-only ("training ran, version incremented") with no quality floor

### Surprises / Blockers
- **OOM during training** — `n_jobs=-1` multiplied memory usage by core count; fixed by setting `n_jobs=1`
- **Model accuracy regression** — v2.0 (53.8%) is worse than v1.0 (59.1%) despite 5× the training data. Likely cause: v1.0 was trained on 808 late-season games with low variance; v2.0 spans two full regular seasons with much higher game-to-game variance. Root cause not yet confirmed — flagged for investigation
- **Scheduler 3-hour hang** — pre-existing bug (Docker Desktop `osascript` quit blocking on wake) surfaced via log review during the sprint; fixed opportunistically

---

## Lessons Learned

1. More training data does not guarantee better model accuracy — dataset composition matters as much as size
2. A calendar-based data cutoff (e.g. post-All-Star only) is not a viable fix: early in the season there is no post-All-Star data. Any solution must work year-round
3. `n_jobs=-1` on large datasets is a memory risk — default to `n_jobs=1` unless memory headroom is confirmed
4. Retraining ACs should include a model quality floor, not just completion criteria

---

## Adopted Recommendations

- **Investigate v2.0 accuracy regression** — added to backlog as high-priority item before next retraining sprint. Specific hypothesis (late-season vs. full-season data composition) to be tested; calendar-based cutoff ruled out as a general solution given early-season constraints.

---

## Deferred / Declined

- Add minimum accuracy gate to retraining AC — valid but deferred; root cause of regression must be understood first
- Add frontend test for null probability fix — deferred; low risk given simplicity of fix
- Add `data_as_of` field to API response — already in backlog as "Stale data behavior investigation"
