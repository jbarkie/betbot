# Sprint 7 Retrospective

**Date:** 2026-08-11
**Branch:** `feature/20260519_Sprint_7`
**PR:** #41
**Goal:** Add starting pitcher ERA/WHIP/K9 as pre-game ML features; retrain the RF baseline on 2026 data.

---

## Sprint Outcomes vs Acceptance Criteria

### Issue #37 — Retrain RF Baseline with 2026 Season Data

| Criterion | Result |
|---|---|
| Training runs to completion on full 2024+2025+2026 dataset | ✅ Met |
| Test accuracy printed and compared against v3.0 baseline (55.09%) | ✅ Met |
| If accuracy ≥ 55.09%: `ml_config.py` bumped, metadata committed | ✅ Met — 56.96%, promoted as v3.2 |
| If accuracy < 55.09%: documented, v3.0 retained | N/A — bar was cleared |
| All 132 existing tests pass | ✅ Met |

### Issue #38 — Starting Pitcher DB Table and Data Collection

| Criterion | Result |
|---|---|
| `mlb_pitcher_stats` exists after `alembic upgrade head` with specified columns | ✅ Met |
| Stats reflect cumulative totals from starts strictly before each game date | ✅ Met — verified against live API |
| Collection is idempotent | ✅ Met |
| `update_mlb_data.py` calls pitcher collection after team stats | ✅ Met |
| 3+ unit tests | ✅ Exceeded — 26 tests |

### Issue #39 — Starting Pitcher Feature Engineering

| Criterion | Result |
|---|---|
| 32 columns output (26 + 6 named as specified) | ✅ Met |
| Missing pitcher data median-imputed, not NaN or 0 | ✅ Met |
| `ml_config.py` lists all 32 features | ✅ Met |
| Training runs with pitcher features; accuracy printed vs baseline | ✅ Met |
| 3+ new unit tests; feature-count tests expect 32 | ✅ Exceeded — 24 tests |

### Issue #40 — Inference-Time Starting Pitcher Lookup

| Criterion | Result |
|---|---|
| Response reflects the six pitcher features | ✅ Met (via `feature_importance`; see note) |
| Unavailable pitcher data returns median-imputed prediction, no 500 | ✅ Met |
| 3+ unit tests with mocked API responses | ✅ Exceeded — 21 tests |
| All existing backend tests pass | ✅ Met — 203 total |

**21/21 applicable criteria met.** Test suite grew from 132 to 203 (+71).

---

## Model Results

| Model | Features | Accuracy | ROC AUC | Outcome |
|---|---|---|---|---|
| v3.0 | 26 | 55.09% | 0.552 | previous production |
| v3.1 | 26 | 53.87% | — | trained 2026-05-20, not promoted |
| v3.2 | 26 | 56.96% | 0.5628 | full-dataset retrain |
| **v3.3** | **32** | 56.44% | **0.5708** | **promoted to production** |

---

## Retrospective

### Acceptance Criteria Coverage

Strong, but one criterion encoded an assumption that the data later contradicted. Issue #39 required `ml_config.py` to list all 32 features — which only makes sense if the 32-feature model actually ships. When v3.3 came in 0.52pp *below* v3.2 on accuracy, that criterion silently became a decision rather than a checkbox. It was escalated to the user rather than mechanically satisfied.

**Lesson:** when a card's acceptance criteria presuppose a positive experimental result, write the conditional branch explicitly, the way Sprint 6's "promote OR document" criterion did. Sprint 6 got this right; Sprint 7 did not, in one card.

### Test Coverage Quality

71 new tests, and two of them earned their keep immediately by catching real defects:

1. `test_game_id_coerced_to_string` caught `build_pitcher_lookup` using `iterrows()`, which upcasts a mixed int/float row to float64 — an integer `game_id` stringified as `"1.0"` and silently missed the schedule's `"1"`. Production data happened to be unaffected because `game_id` is a String column, so this would have sat dormant until some future caller passed integers.
2. The Card 4 fixtures forced the discovery that `odds.id` and MLB's `gamePk` are unrelated id spaces (see below).

The no-leakage tests are the most valuable of the set, because leakage is the failure mode that would make the model look *better* while being worthless.

### Code Quality and Conventions

Splitting `MLB_REQUIRED_FEATURES` into `MLB_BASE_FEATURES` + `MLB_PITCHER_FEATURES` was the right call. It keeps the serving contract explicit while letting a 26-feature model still be trained for comparison, and it made the ordering constraint (the model is fit positionally) testable.

Sourcing `PITCHER_FEATURES` in the pipeline from `ml_config` rather than redeclaring it removed a live drift risk between training and serving.

### Documentation Completeness

CLAUDE.md, both READMEs, and the model version history were all updated in the same commits as the code. Two entries were added specifically to stop future sessions repeating this sprint's mistakes: the Gini-vs-permutation-importance caveat, and the `odds.id` ≠ `gamePk` bridge.

### Phase Discipline

Followed. Commit-per-issue held, and every card was committed and its issue closed with measured results before the next began. Phase 7 completed before merge, per convention.

One deviation: Card 1 was reopened for review at the user's request rather than closed on sight. That was correct — the review is what surfaced that the dataset had grown 18% since v3.1, which is what produced the sprint's largest single accuracy gain.

### Estimation Accuracy

The backfill was the big miss, in the good direction: estimated 15–20 minutes for ~2,500 API calls, actual **3.6 minutes** with zero failures. The estimate assumed per-call latency similar to the team-stats collector, which suffers repeated 30s timeouts. The pitcher endpoints proved far more reliable.

### Surprises and Blockers

1. **PostgreSQL was down before any sprint work started.** A stale `postmaster.pid` (referencing a PID macOS had reassigned to an unrelated process) put the service in an error state, and the launchd scheduler had silently skipped 2026-08-10 and 2026-08-11. The scheduler's SKIP-and-exit behaviour worked exactly as designed, but nothing surfaces those skips — they only appear if someone reads the log.

2. **The premise of the session's first question was wrong, but productive.** The suspicion that v3.1 trained on a truncated dataset turned out to be the `min_games_threshold=10` filter behaving correctly. Investigating it anyway revealed the far more important fact that the dataset had grown 18% since, which flipped Card 1's outcome from "more data does not help" to a 1.87pp gain.

3. **`odds.id` is not `gamePk`.** The analytics endpoint is keyed by an opaque odds-provider hash. Passing it to the MLB API would have resolved nothing and quietly served median-imputed pitcher stats for every single game — a failure indistinguishable from working code, since the endpoint would still return 200s with plausible predictions.

4. **Gini importance was actively misleading.** It ranked the six new features #1–#5, which would have justified a triumphant write-up. Permutation importance on held-out data put the best of them #3 with roughly average per-feature contribution.

### Lessons Learned

1. **Re-validate stale experimental results before building on them.** A negative result from three months ago was still shaping the backlog. The conditions that produced it no longer held.
2. **Never trust Gini importance for continuous features in a Random Forest.** Use permutation importance on held-out data before claiming a feature helps.
3. **A statistically insignificant accuracy change is a judgment call, not a verdict.** Reporting the noise floor (±1.35pp here) alongside the delta is what made the v3.3 decision tractable.
4. **Identifier spaces that look joinable often are not.** Two systems both calling a field "game id" is not evidence they mean the same thing.
5. **Silent skips are near-invisible failures.** The scheduler correctly logged and exited, but two days of missing data went unnoticed until someone happened to look.

---

## Improvement Recommendations

1. **Alert on scheduler skips.** The launchd job logs `SKIP` and exits silently. Add a macOS notification, or have the next successful run report how many days it had to catch up.
2. **Write conditional acceptance criteria for experimental cards.** Adopt Sprint 6's "promote OR document" pattern whenever a card's later criteria depend on an experiment succeeding.
3. **Add a data-freshness assertion to training.** `train_mlb_model.py` should warn when the most recent completed game is more than N days old, so a stale database cannot silently produce a stale model.
4. **Record the noise floor in the model version history.** Accuracy deltas smaller than the test set's standard error should be labelled as such in the README table.
5. **Raise pitcher coverage above 89.7%.** Accumulating over all prior *appearances* rather than prior *starts* would cover relievers-turned-starters and season debuts.
6. **Consider a permutation-importance flag on `--diagnostics`.** The Gini table printed today is the misleading one.

---

## Follow-Up Backlog Candidates

- Pitcher stat accumulation over all appearances, not only starts (coverage 89.7% → ~100%)
- Pitcher handedness and home/away platoon splits as additional features
- Re-run XGBoost hyperparameter search now that the dataset exceeds 6,700 games
- Scheduler skip alerting
- Data-freshness guard in the training script
