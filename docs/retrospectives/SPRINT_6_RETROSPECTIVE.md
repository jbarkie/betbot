# Sprint 6 Retrospective

**Date:** 2026-05-04
**Branch:** `feature/20260504_Sprint_6`
**PR:** #36
**Goal:** Tune XGBoost hyperparameters via randomized search to find a configuration competitive with the v3.0 RF baseline (55.09%), then promote or document the result.

---

## Sprint Outcomes vs Acceptance Criteria

### Issue #34 — Implement `--hyperparameter-search` flag

| Criterion | Result |
|---|---|
| `--model-type xgboost --hyperparameter-search` runs to completion with real data | ✅ Met |
| Best params printed as JSON to stdout | ✅ Met |
| Test accuracy with best params logged alongside 51.46% Sprint 5 baseline | ✅ Met |
| `TimeSeriesSplit(n_splits=5)` used (not standard k-fold) | ✅ Met |
| `--hyperparameter-search` with non-XGBoost types raises `ValueError` | ✅ Met |
| 3+ new unit tests added; all existing tests pass | ✅ Met — 6 new tests |

### Issue #35 — Update defaults and promote/document v4.0

| Criterion | Result |
|---|---|
| Default XGBoost params in `_build_pipeline()` updated | ✅ Met |
| `--model-type xgboost` trains with new defaults | ✅ Met |
| `models/mlb/README.md` has v4.0 version entry | ✅ Met |
| `docs/sprint6_xgboost_findings.md` created (accuracy < 55.09%) | ✅ Met |

**10/10 criteria met.**

---

## Search Results

| Metric | Value |
|---|---|
| Best CV accuracy (50 iterations) | 56.47% |
| Test set accuracy (best params) | 50.49% |
| Sprint 5 XGBoost baseline (default params) | 51.46% |
| v3.0 RF production baseline | 55.09% |

RF v3.0 retained as production model. See `docs/sprint6_xgboost_findings.md` for root-cause analysis.

---

## Retrospective

### Acceptance Criteria Coverage
Strong. The conditional acceptance criterion ("promote OR document") worked well — both outcome branches had clear exit conditions before the sprint started. No ambiguity when the test accuracy came in below baseline.

### Test Coverage Quality
6 new unit tests, all meaningful. Patching `create_model()` on the trainer instance (alongside `RandomizedSearchCV`) was the correct approach: it keeps the tests as pure unit tests of search orchestration logic without requiring XGBoost to be installed. This was caught by CI and fixed before merge.

### Code Quality and Conventions
The `_xgboost_override_params` attribute pattern is clean — search results flow into `create_model()` without touching `train_and_evaluate()`'s signature. Adding `RandomizedSearchCV` to top-level imports (rather than inside the method) followed existing style and made mocking straightforward. `--search-iter` was added beyond the approved spec with no complexity cost.

### Documentation Completeness
Full coverage: `sprint6_xgboost_findings.md` (root cause analysis with Objective → Method → Results → Analysis → Recommendation structure), `models/mlb/README.md` (v4.0 version entry), `CLAUDE.md` (new flags + CV vs test accuracy caveat), `ALL_SPRINTS_MASTER_PLAN.md` (backlog and history).

### Phase Discipline
Phases 2–6 followed in order. Minor deviation: CLAUDE.md updated after PR creation rather than as part of Phase 6 step 3. No impact in practice, but the correct order is before `git push`.

### Estimation Accuracy
Both cards came in under estimate. The search itself was ~30 seconds on 409 training games, far faster than the "several minutes" log message suggested. The warning is overcalibrated for large datasets.

### Surprises / Blockers
- **CV vs test accuracy gap** — best CV accuracy was 56.47% (above RF baseline) but test accuracy was 50.49% (below Sprint 5 defaults). Root cause: small dataset (512 games, 90-day window) causes XGBoost to overfit CV folds rather than generalize.
- **CI failure on XGBoost tests** — 4 of the 6 new tests failed in CI because `create_model()` triggers the XGBoost import before `RandomizedSearchCV` is mocked. Fixed by adding `patch.object(trainer, 'create_model')` to those tests.

### Lessons Learned
1. CV accuracy on small datasets (< ~1,500 games) is an optimistic estimate of generalization. Always compare CV accuracy to holdout test accuracy before making a promotion decision.
2. When mocking a method that is called internally before the primary mock is intercepted, patch the internal method as well — or the import it triggers will leak into the test.
3. The 90-day default training window is too small for reliable XGBoost hyperparameter tuning. Either extend the window at search time or wait for more data volume.

---

## Improvement Recommendations Adopted

- **#1**: Added CV vs holdout accuracy caveat to `CLAUDE.md` under the `--hyperparameter-search` bullet.

---

## Backlog Updates

- `XGBoost hyperparameter tuning` marked complete in `ALL_SPRINTS_MASTER_PLAN.md`
- New item added: **XGBoost re-evaluation (≥ 2,000 games)** — re-run `--hyperparameter-search` when 2026 season has ≥ 2,000 completed games (est. late July 2026); v4.0 tuned params are the starting baseline
