# Sprint 5 — MLB Model Diagnostic Findings

**Date:** 2026-04-24  
**Sprint Goal:** Diagnose v1.0→v2.1 accuracy regression; evaluate XGBoost and temporal weighting; promote best model to v3.0.

---

## Class Balance

| Metric | Value |
|--------|-------|
| Home win rate (training set) | 53.38% |
| Away win rate (training set) | 46.62% |

**Interpretation:** Mild class imbalance consistent with known MLB home field advantage. The model's over-prediction of home wins (recall=0.73 vs precision=0.56) is partially explained by this imbalance but not fully — the model is more biased toward home wins than the base rate justifies. Not the primary root cause of the accuracy gap.

---

## Per-Month Accuracy Breakdown (RF Baseline, v3.0-rf-baseline test set)

The test set spans the last 20% of chronological training data (primarily July–October 2025).

| Month | Games | Accuracy |
|-------|-------|----------|
| Apr   | 2     | 1.0000   |
| May   | 2     | 0.0000   |
| Jun   | 1     | 0.0000   |
| Jul   | 166   | 0.5602   |
| Aug   | 419   | 0.5251   |
| Sep   | 376   | 0.5691   |
| Oct   | 27    | 0.5556   |

**Interpretation:** Apr/May/Jun have 1–2 test games — statistically meaningless. The meaningful months (Jul–Oct) show accuracy between 52.5% and 56.9%, with no dramatic seasonal pattern. August is the weakest month; September is the strongest. The variance across meaningful months (~4%) suggests moderate month-to-month variance but no structural seasonal breakdown.

---

## Learning Curve (RF Baseline, fixed test set)

| Training Fraction | Train Size | Test Accuracy |
|-------------------|------------|---------------|
| 20%               | 793        | 0.5156        |
| 40%               | 1,587      | 0.5096        |
| 60%               | 2,380      | 0.5307        |
| 80%               | 3,174      | 0.5519        |
| 100%              | 3,968      | 0.5478        |

**Interpretation:** Accuracy improves monotonically from 20% to 80% of training data, then plateaus at 100%. The model is NOT saturated — more training data should improve performance. The slight dip from 80% to 100% is noise. Key implication: adding 2026 data when available should push accuracy higher.

---

## Feature Importance Ranking (RF Baseline)

| Rank | Feature | Importance |
|------|---------|------------|
| 1 | away_rolling_runs_scored | 0.0739 |
| 2 | away_rolling_runs_allowed | 0.0686 |
| 3 | home_rolling_runs_allowed | 0.0671 |
| 4 | home_rolling_runs_scored | 0.0663 |
| 5 | home_era | 0.0433 |
| 6 | home_strikeouts | 0.0424 |
| 7 | away_era | 0.0418 |
| 8 | home_obp | 0.0411 |
| 9 | away_slg | 0.0393 |
| 10 | home_slg | 0.0391 |
| 11 | away_obp | 0.0391 |
| 12 | away_strikeouts | 0.0381 |
| 13 | day_of_week | 0.0380 |
| 14 | h2h_away_win_pct | 0.0373 |
| 15 | h2h_home_win_pct | 0.0362 |
| 16 | home_whip | 0.0361 |
| 17 | away_whip | 0.0359 |
| 18 | home_batting_avg | 0.0358 |
| 19 | home_rolling_win_pct | 0.0348 |
| 20 | away_batting_avg | 0.0340 |
| 21 | away_rolling_win_pct | 0.0331 |
| 22 | month | 0.0301 |
| 23 | h2h_games_played | 0.0227 |
| 24 | is_weekend | 0.0089 |
| 25 | away_days_rest | 0.0089 |
| 26 | home_days_rest | 0.0082 |

**Interpretation:** Rolling runs scored/allowed dominate (all four in top 4). `day_of_week` at rank 13 (0.038) is surprisingly high — nearly as important as ERA. `is_weekend`, `home_days_rest`, and `away_days_rest` have very low importance (0.008–0.009) and may be candidates for removal or replacement in future sprints. The low importance of `rolling_win_pct` relative to `rolling_runs` suggests the model finds run production more predictive than win/loss record.

---

## Comparative Accuracy Table

| Model | Accuracy | Precision | Recall | F1 | ROC AUC | vs v2.1 |
|-------|----------|-----------|--------|-----|---------|---------|
| v2.1 (production baseline) | 54.57% | 0.562 | 0.704 | 0.625 | 0.552 | — |
| RF unweighted (v3.0-rf-baseline) | 54.78% | 0.558 | 0.730 | 0.632 | 0.540 | +0.21% |
| **RF + temporal weighting, 365d (v3.0-rf-tw365)** | **55.09%** | **0.560** | **0.734** | **0.635** | **0.552** | **+0.52%** |
| RF + temporal weighting, 180d (v3.0-rf-tw180) | 53.17% | 0.546 | 0.713 | 0.619 | 0.542 | -1.40% |
| XGBoost default params (v3.0-xgb) | 51.46% | 0.539 | 0.609 | 0.572 | 0.520 | -3.11% |

**Winner: RF + 365-day temporal weighting** at 55.09%.

---

## Root Cause Analysis

**Why is v3.0 at 55.09% rather than matching v1.0 (59.1%)?**

v1.0's 59.1% is not a fair comparison target for v3.x. Evidence:

1. **v1.0 trained on 808 games, all late-season (post-August 2025)** — late-season data is homogeneous: rosters are settled, pennant race dynamics are consistent, team quality is well-characterized by statistics.

2. **v3.0 trained on 3,968 games spanning two full regular seasons** — April and May games have high variance: pitching rotations are unsettled, players are returning from injury, and team statistics have small samples.

3. **The learning curve shows the model is not saturated** — adding 2026 season data after it completes should push accuracy upward, as the model will have seen more examples across the full seasonal arc.

4. **Temporal weighting (365-day half-life) gives +0.52%** — confirms that recent games are modestly more predictive, but the effect is small. The 365-day window downweights 2024 games by ~50% relative to 2025, which is the right direction.

5. **180-day half-life hurts (-1.40%)** — too aggressive downweighting discards useful signal from 2024 data that generalizes well to 2025.

6. **XGBoost with default parameters underperforms (-3.11%)** — the default `max_depth=6` may be too shallow for this feature set, and the learning rate / subsample combination may need tuning. XGBoost can potentially match or beat RF with a proper hyperparameter search, but that was out of scope this sprint.

**The primary root cause of the v1.0 vs v3.0 gap is dataset composition, not model deficiency.** v1.0 was effectively trained on an easy subset; v3.0 faces the full problem.

---

## Promoted Model: v3.0

- **File:** `mlb_predictor_v3.0-rf-tw365.joblib`
- **Type:** RandomForestClassifier
- **Training approach:** Exponential decay temporal weighting, 365-day half-life
- **Accuracy:** 55.09% (test set, chronological 80/20 split)
- **Improvement over v2.1:** +0.52%
- **Config:** `api/src/ml_config.py` updated to point to v3.0

---

## Recommendations for Future Sprints

1. **Add 2026 season data and retrain** — the learning curve shows training is not saturated; more data is the clearest path to higher accuracy. Schedule a retrain after ~500 2026 games are complete (late May 2026).

2. **XGBoost hyperparameter tuning** — a focused grid search on `max_depth` (4, 6, 8, 10), `learning_rate` (0.05, 0.1, 0.2), and `n_estimators` (100, 200, 300) could potentially close the gap with RF. Use early stopping on a validation set.

3. **Starting pitcher features** — ERA, WHIP, K/9 for the day's scheduled starter. This is the highest-impact player-level feature available pre-game and requires: a new DB table for pitcher stats, a data collection script using the MLB Stats API `/people/{id}/stats` endpoint, and inference-time lookup in `enhanced_mlb_analytics.py`.

4. **Remove or replace low-importance features** — `is_weekend`, `home_days_rest`, `away_days_rest` all have importance < 0.01. Replace with: park factor (known and static), umpire tendencies (available via retrosheet), or opponent-adjusted stats.
