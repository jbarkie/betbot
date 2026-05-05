# Sprint 6: XGBoost Hyperparameter Tuning — Findings

**Date:** 2026-05-04
**Branch:** `feature/20260504_Sprint_6`
**Related issues:** #34, #35

---

## Objective

Determine whether XGBoost, with tuned hyperparameters, can match or beat the v3.0 Random Forest baseline of **55.09%** test accuracy. Sprint 5 shipped XGBoost with sklearn-default params and scored **51.46%**.

---

## Method

`RandomizedSearchCV` with `TimeSeriesSplit(n_splits=5)`, `n_iter=50`, `scoring='accuracy'`.

**Parameter space searched:**

| Parameter | Values |
|---|---|
| `max_depth` | 3, 4, 5, 6, 7, 8 |
| `learning_rate` | 0.01, 0.05, 0.08, 0.1, 0.15, 0.2 |
| `n_estimators` | 100, 200, 300, 500 |
| `subsample` | 0.6, 0.7, 0.8, 0.9, 1.0 |
| `colsample_bytree` | 0.6, 0.7, 0.8, 0.9, 1.0 |
| `min_child_weight` | 1, 3, 5, 7 |
| `gamma` | 0, 0.1, 0.2, 0.5 |

**Training data:** 512 games (90-day window ending 2026-05-04), 409 train / 103 test split.

---

## Results

| Metric | Value |
|---|---|
| Best CV accuracy (search) | **56.47%** |
| Test set accuracy (best params) | **50.49%** |
| Sprint 5 XGBoost baseline (default params) | 51.46% |
| v3.0 RF production baseline | **55.09%** |

**Best params found:**

```json
{
  "subsample": 0.7,
  "n_estimators": 200,
  "min_child_weight": 1,
  "max_depth": 6,
  "learning_rate": 0.15,
  "gamma": 0.5,
  "colsample_bytree": 1.0
}
```

---

## Analysis: Why CV Accuracy ≠ Test Accuracy

The 56.47% CV score looked promising, but the 50.49% test score reveals a gap. Three likely causes:

### 1. Small training dataset
The search ran on **512 games** (90-day window into the 2026 season). This is far smaller than the v3.0 RF training set (3,968 games — full 2024+2025 seasons). With small data:
- Each CV fold gets ~82 training games and ~82 validation games
- `RandomizedSearchCV` selects the param set that happened to align with the validation fold's noise
- The "best" params are partly memorizing temporal artifacts of the small window

### 2. CV score optimism on time-series data
Even with `TimeSeriesSplit`, CV folds are all drawn from the same 90-day window. If that window has a structural shift (e.g., early-season effects, team-level noise from 2026 roster changes), the best CV params will be tuned to that structure — which does not generalize to the test tail.

### 3. XGBoost's sensitivity to data volume
Random Forest is an averaging ensemble — adding trees reduces variance, and it is relatively robust to small N. XGBoost is a sequential boosting model: each tree corrects the residuals of the previous. On small datasets, boosting tends to overfit the residual noise rather than real signal, even with regularization params like `gamma` and `min_child_weight`.

---

## Recommendation

**Keep v3.0 RF as the production model.** `ml_config.py` is unchanged.

**Re-evaluate XGBoost once ≥ 2,000 games are available** (estimated late July 2026 if 2026-season collection continues). At that data volume:
- CV folds will be larger and more representative
- XGBoost's regularization will have real signal to regularize against, not noise
- The CV vs test accuracy gap should narrow

The tuned params (`learning_rate=0.15, gamma=0.5, colsample_bytree=1.0`) are now the hardcoded XGBoost defaults in `train_mlb_model.py`. They are saved as **v4.0** and should be the starting point for any future re-evaluation.

---

## Backlog Update

The "XGBoost hyperparameter tuning" backlog item is resolved. The new backlog item:

> **XGBoost re-evaluation (≥ 2,000 games)** — Re-run `--model-type xgboost --hyperparameter-search` when 2026 season has ≥ 2,000 completed games. v4.0 tuned params are the starting baseline. Expected: late July 2026.
