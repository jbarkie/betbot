# Sprint 5 Retrospective

**Date:** 2026-04-24  
**Branch:** `feature/20260424_Sprint_5`  
**PR:** #33  
**Goal:** Diagnose the v1.0→v2.1 accuracy regression, implement and evaluate XGBoost and temporal sample weighting, and promote the best-performing approach to v3.0.

---

## Sprint Outcomes vs. Acceptance Criteria

### Issue #29 — Diagnostic Analysis

| Criterion | Result |
|-----------|--------|
| `--diagnostics` prints per-month accuracy table | ✅ Met |
| Home win rate logged to two decimal places | ✅ Met (53.38%) |
| Learning curve logged at 20/40/60/80/100% | ✅ Met |
| Feature importance ranking (all 26) printed for tree-based models | ✅ Met |
| Findings committed to `sprint5_diagnostic_findings.md` | ✅ Met |

### Issue #30 — XGBoost Model Type

| Criterion | Result |
|-----------|--------|
| `--model-type xgboost` trains to completion | ✅ Met |
| XGBoost accuracy logged vs. v2.1 baseline | ✅ Met (51.46%) |
| `argparse choices` includes `'xgboost'` | ✅ Met |
| `xgboost` pinned in `requirements.txt` | ✅ Met |
| All existing `test_ml_model_service.py` tests pass unmodified | ⚠️ Partial — existing tests unmodified ✅; new XGBoost test required a follow-up CI fix |

### Issue #31 — Temporal Sample Weighting

| Criterion | Result |
|-----------|--------|
| `--temporal-weighting --half-life 365` runs without error | ✅ Met |
| Unweighted run produces identical results to existing behavior | ✅ Met |
| Log prints min/max weight and max/min ratio | ✅ Met |
| Weighted vs. unweighted accuracy logged and compared | ✅ Met |
| Unit test asserts monotonically non-decreasing weights | ✅ Met (8 tests) |

### Issue #32 — Promote Best Model to v3.0

| Criterion | Result |
|-----------|--------|
| `ml_config.py` updated to v3.0 pointing to best model | ✅ Met (RF + 365d weighting) |
| v3.0 accuracy ≥ 54.57%; root-cause doc if < 59.1% | ✅ Met (55.09%; root cause documented) |
| All API tests pass | ✅ Met (115/115) |
| `models/mlb/README.md` version table updated | ✅ Met |
| `sprint5_diagnostic_findings.md` has all five required sections | ✅ Met |

**19/20 criteria fully met.**

---

## Retrospective

### Acceptance Criteria Coverage
Strong. All criteria were measurable and verifiable. The "must not regress from v2.1" floor was well-designed — it gave a hard lower bound regardless of whether the 59.1% target was reached.

### Test Coverage Quality
Good. 8 unit tests for `_compute_sample_weights()` cover length, positivity, monotonicity, half-life math, and edge cases. The XGBoost inference integration test added meaningful coverage. CI failure revealed a gap: the test assumed xgboost would always be available without accounting for the CI environment. The `pytest.importorskip` fix was correct but required an extra commit.

### Code Quality and Conventions
Good. All three features landed in `train_mlb_model.py` with clear method boundaries. The float32 JSON serialization fix was accompanied by an explanatory comment. One issue: all changes were committed in a single Phase 6 commit rather than per-issue — this was the approved improvement for future sprints.

### Documentation Completeness
Strong. `sprint5_diagnostic_findings.md` is a detailed artifact for future reference. `models/mlb/README.md` now has a version history table. `CLAUDE.md` and `README.md` were updated post-sprint after prompting — should happen in Phase 6.

### Phase Discipline
Followed well. Planning was thorough. Parallel training runs (XGBoost, RF-365, RF-180) saved meaningful time. The CI failure was caught after PR creation rather than before — a minor miss in Phase 5.

### Estimation Accuracy
Well-calibrated. All four issues completed in one session. Learning curve computation was faster than expected. Parallel training runs saved significant elapsed time.

### Surprises or Blockers
- **XGBoost float32 JSON serialization** — XGBoost returns `numpy.float32` feature importances which `json.dump` rejects. Required a follow-up fix commit and second CI run.
- **XGBoost underperformed significantly** (51.46% vs 54.78% RF) — the 3.3-point gap with default parameters was larger than anticipated. Needs hyperparameter tuning for a fair comparison.
- **Temporal weighting gain was modest** (+0.52%) — confirmed the hypothesis directionally, but the learning curve finding (model not saturated) is the more actionable insight.

### Lessons Learned
- v1.0's 59.1% accuracy was never a fair comparison target — it trained on late-season homogeneous data. The accuracy gap is a dataset composition artifact, not a model deficiency. Should have been documented earlier in sprint history.
- XGBoost needs a dedicated hyperparameter tuning sprint before being evaluated fairly against RandomForest.
- The CI environment (Python 3.9, only `api/requirements.txt`) should be modeled at test-writing time, not discovered at push time.
- The learning curve is the clearest diagnostic signal: the model is not saturated, and adding 2026 season data is the highest-value next step.

---

## Approved Workflow Improvement

**Recommendation 3 adopted:** Commit per GitHub issue during development rather than one large commit at Phase 6. Makes git history bisectable — especially important for ML experiments where individual changes need to be reverted independently. Added to `CLAUDE.md` under Sprint Workflow.

---

## Model Results Summary

| Model | Accuracy | vs v2.1 |
|-------|----------|---------|
| v2.1 (prior production) | 54.57% | — |
| RF unweighted | 54.78% | +0.21% |
| **RF + temporal weighting 365d (v3.0)** | **55.09%** | **+0.52%** |
| RF + temporal weighting 180d | 53.17% | -1.40% |
| XGBoost default params | 51.46% | -3.11% |

---

## Recommended Next Actions (for backlog)

1. Retrain v4.0 when 2026 season has ≥ 500 completed games (est. late May 2026)
2. XGBoost hyperparameter tuning sprint (grid search on `max_depth`, `learning_rate`, `n_estimators`)
3. Starting pitcher features sprint (ERA/WHIP/K9 for day's starter — highest-impact player-level feature available pre-game)
