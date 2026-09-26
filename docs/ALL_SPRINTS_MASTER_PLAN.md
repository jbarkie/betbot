# BetBot — All Sprints Master Plan

## Project

**BetBot** — Full-stack sports betting analytics app (FastAPI + PostgreSQL + Angular 19 + NgRx Signals + ML)

---

## Backlog: Next Sprint Candidates

> Prioritized list of potential work items. Reprioritize with `/sprint refine`.
> Last refined 2026-09-10 against the live database and codebase.

### Sprint 8 Candidates — Serving Robustness and Operations

Chosen for Sprint 8 because none of these depend on the dataset, and three come
directly from the Sprint 7 retrospective's own recommendations. Deliberately
excludes model work: the regular season ends around 2026-10-01, so accuracy
experiments batch better into Sprint 9 against a complete season.

- [ ] **Blocking network I/O on the event loop** — `get_starting_pitcher_features()` is sync and calls the MLB Stats API (30s default timeout, up to 3 sequential requests) from inside an `async def` route, stalling the whole event loop. Tier 1 misses for every upcoming game (the backfill only covers played games), so this is the normal path for live predictions, not a rare one. Pre-existing pattern — `games.py:31` calls the Odds API the same way with no timeout at all. Fix both: `asyncio.to_thread`, or a short serving-path timeout. Found in PR #41 review.
- [ ] **Scheduler skip alerting** — The launchd MLB update logs `SKIP` and exits silently when PostgreSQL is down. Two days of data were missed in August 2026 before anyone noticed. Surface a notification or have the next successful run report the catch-up gap.
- [ ] **Data-freshness guard in training** — `train_mlb_model.py` should warn when the newest completed game is more than N days old, so a stale database cannot silently produce a stale model.
- [ ] **Alembic migration CI check** — Fail CI if unapplied migrations exist on the branch. Promoted from Low: PR #41 shipped a migration, and the reviewer could not confirm from CI alone that it applied cleanly.

### Sprint 9 Candidates — Model Accuracy (hold until the season ends, ~2026-10-01)

- [ ] **Full-season v3.4 retrain** — As of the 2026-09-10 refinement, raw completed-game counts had grown from 6,909 on 2026-08-11 to 7,313 (+5.8%). Separately, v3.3 used 6,750 games after training-data filters (5,400 train / 1,350 test); recount eligible samples before retraining. Defer the next retrain until the complete 2026 season to avoid repeating the work shortly afterward. This is a scheduling choice, not evidence that an interim retrain would fail to improve the model: the ~1.35pp standard error describes held-out accuracy uncertainty and cannot be compared with dataset growth.
- [ ] **XGBoost re-evaluation (≥ 2,000 games)** — Gate long cleared: 7,313 completed games total, 2,193 in 2026 as of 2026-09-10. Re-run `--hyperparameter-search` against the v3.3 baseline of 56.44% (AUC 0.5708) with 32 features available. v4.0 tuned params are the starting point.
- [ ] **Pitcher stats over all appearances, not only starts** — Sprint 7 accumulates over prior starts only. Current coverage is 88.4% of game-team slots (12,929 of 14,626), but 16.5% of completed games have at least one side median-imputed, which is the number that matters for training. Counting all prior appearances would cover relievers-turned-starters and season debuts.
- [ ] **Pitcher handedness and platoon splits** — Natural extension of the Sprint 7 `mlb_pitcher_stats` table.

### High Priority (unscheduled)

- [ ] **Prediction transparency in the analytics modal** — The API returns `prediction_method`, `ml_model_name`, `ml_confidence`, `confidence_level` and `feature_importance`, and `models.ts` already declares all five on `AnalyticsResponse`, but `analytics-modal.component.ts` renders none of them. A user cannot tell an ML prediction from the rule-based fallback, even though the 0.55 confidence gate silently decides which one they get. (Supersedes the old "Frontend analytics integration" item, which claimed predictions were API-only — Sprint 1 shipped the modal.)
- [ ] **NFL/NHL parity with MLB analytics** — Add ML-backed game analytics endpoints for NFL and NHL (currently only MLB has the ML prediction pipeline)
- [ ] **NBA analytics endpoint** — Extend the analytics system to NBA games
- [ ] **Model retraining automation** — Scheduled script or cron job to retrain MLB model as new game data accumulates
- [ ] **User favorites/watchlist** — Allow authenticated users to bookmark games or teams

### Medium Priority

- [ ] **Historical odds tracking** — Store odds snapshots over time per game to surface line movement
- [ ] **Push notifications** — Alert users when odds move significantly on a favorited game
- [ ] **Model evaluation dashboard** — Admin page showing prediction accuracy, confusion matrix, and feature importance
- [ ] **Multi-bookmaker comparison** — Expand beyond FanDuel to show best available line across bookmakers
- [ ] **Test coverage improvement** — Backend API coverage is partial; increase to 80%+ with integration tests for analytics endpoints

### Low Priority

- [ ] **Dark/light theme persistence** — Persist user theme preference server-side (currently settings store is in-memory)
- [ ] **Rate limiting** — Add per-user rate limiting to external Odds API proxy endpoints
- [ ] **OpenAPI docs UI** — Enable Swagger UI behind auth in production
- [ ] **Stale data behavior investigation** — When DB data is stale, the API still returns analytics for today's games using last-known team stats. Determine whether this is expected behavior or should surface a warning/error when data is older than N days

### Completed

- [x] **Retrain RF baseline with 2026 season data** — Sprint 7 Card 1. v3.2 at 56.96%, beating the v3.0 baseline of 55.09% by 1.87pp.
- [x] **XGBoost hyperparameter tuning** — Sprint 6 randomized search (n_iter=50) found best CV 56.47% but test 50.49%; RF v3.0 retained. See `docs/sprint6_xgboost_findings.md`.
- [x] **Starting pitcher features** — ERA/WHIP/K9 for the day's scheduled starter. Sprint 7 (#38, #39, #40): new `mlb_pitcher_stats` table (cumulative pre-game stats via MLB Stats API game logs), feature engineering (32 total features), inference-time lookup in `enhanced_mlb_analytics.py`.

---

## Sprint History

| Sprint | Dates | Goal | Outcome |
|--------|-------|------|---------|
| Sprint 1 | 2026-04-16 | Surface ML win probabilities in the game cards analytics modal | Merged — retro complete |
| Sprint 2 | 2026-04-17 | Upgrade Angular from v19 to v21 (via v20), NgRx to v21, jest to v30 | Merged — retro complete |
| Sprint 3 | 2026-04-18 | Backfill full 2024+2025 MLB dataset and retrain ML model v2.0 | PR #26 merged — retro complete |
| Sprint 4 | 2026-04-22 | Fix early-season ML noise (v2.1) + migrate DB to Homebrew PostgreSQL | PR #28 merged — retro complete |
| Sprint 5 | 2026-04-24 | Investigate and improve MLB model accuracy: diagnostics, XGBoost, temporal weighting → v3.0 | PR #33 merged — retro complete |
| Sprint 6 | 2026-05-04 | XGBoost hyperparameter tuning via RandomizedSearchCV; evaluate v4.0 vs RF baseline | PR #36 merged — retro complete |
| Sprint 8 | 2026-09-26 → | Serving robustness and operations: non-blocking external I/O, scheduler skip alerting, training freshness guard, Alembic CI check | PR #48 open, CI green — 27/28 criteria met, 1 partial; tests 203 → 253; retro DRAFT |
| Sprint 7 | 2026-05-20 → 2026-08-11 | Add starting pitcher ERA/WHIP/K9 as pre-game ML features; retrain RF baseline on 2026 data | PR #41 merged — 21/21 criteria met; v3.3 promoted (32 features); tests 132 → 203; retro complete |

---

## Sprint 8 — Serving Robustness and Operations (Active)

> **Status:** Approved 2026-09-26 on `feature/20260922_Sprint_8`. Refined from the
> Sprint 8 candidates above plus an external review of the first draft. Issues: Card 1 #44,
> Card 4 #45, Card 3 #46, Card 2 #47. PR #48. Retrospective: `docs/retrospectives/SPRINT_8_RETROSPECTIVE.md` (DRAFT until approved).

**Goal:** Slow external calls no longer block the API event loop; skipped data refreshes are
recorded and surfaced; training warns or stops when completed-game data is older than a
configured age; CI proves every migration applies, rolls back one step, and re-applies.

**Deliberately excluded:** any model or feature work (Sprint 9, after the season ends ~2026-10-01).

**Execution order:** Card 1 → Card 4 → Card 3 → Card 2.

**Verified code facts the cards rest on (checked 2026-09-26):**
- `api/src/enhanced_mlb_analytics.py:40` is `async def` but every operation inside is synchronous: `connect_to_db()`, ORM queries, and `get_starting_pitcher_features()`.
- `api/src/pitcher_lookup.py::_live_stats` makes up to 3 sequential MLB Stats API calls (schedule + one game log per side) through `MLBDirectAPI`, whose default timeout is 30s (`machine_learning/data/collection/mlb_direct_api.py:22`). Tier 1 (stored row) misses for every upcoming game, so this is the normal live path.
- `api/src/games.py::call_odds_api` calls `requests.get(url)` with no timeout at all.
- `get_mlb_model_service()` is a lazy singleton with no lock; `_stats_cache` and `_medians_cache` in `pitcher_lookup.py` are module-level dicts.
- `schedule_updates.sh` hardcodes `/usr/local/opt/postgresql@14/bin/pg_isready`, logs `SKIP` and exits 0 on failure. No shell tests exist for it.
- `update_mlb_data.py` fetches the whole season schedule but only the last 30 days of team stats by default.
- `train_mlb_model.py::fetch_data` loads every `MLBSchedule` row including future scheduled games; completion is `status == 'Final'` (`mlb_data_pipeline.py:162`); `--end-date` defaults to now.
- CI (`.github/workflows/ci-cd.yml`) has `backend-tests`, `frontend-tests`, `all-checks-passed`. `alembic/env.py` reads `sqlalchemy.url` from `alembic.ini` only; it ignores `DB_URL`. There are 11 migrations, exactly one head, and `alembic check` reports no drift against the current models (run 2026-09-26).
- Alembic's import chain (`env.py` → `api.src.models.tables` → `shared.database` → `api.src.config`) calls `load_dotenv()` and raises `ValueError` unless `ODDS_API_URL`, `DB_URL`, and `SECRET_KEY` are all set. So `api/.env` *is* loaded incidentally when Alembic runs locally, and any CI job that runs Alembic must set all three variables, not only `DB_URL`. Both model modules import the same `Base` from `shared.database`, so the metadata covers API and ML tables together.
- `alembic.ini` was gitignored, so a CI checkout had no Alembic configuration and `alembic heads` exited 255 on the first PR run (found 2026-09-26). It is now tracked with the default local URL; `DB_URL` overrides it.
- CI runs Python 3.9, which has `asyncio.to_thread`.

---

### Card 1 (#44) — Non-blocking external I/O in the analytics and games routes

**Problem:** One slow MLB Stats API or Odds API call stalls every other request on the server.

**Approach:** Run the synchronous work in a worker thread via `asyncio.to_thread` at the route
boundary, and give the serving path short timeouts with defined fallbacks. Backfill keeps its
30s timeout.

**Defined behavior:**
- Serving-path MLB Stats API client: 5s per request. Worst case for one prediction is three
  timeouts, roughly 15s, after which the response still returns 200 using median pitcher values.
  This is the documented user-facing ceiling for this sprint, not "never stalls".
- A failed live lookup is cached for the 15-minute TTL like any other result (existing behavior,
  now documented): one bad request does not retry on every page load.
- Odds API: `timeout=(3.05, 10)`. A `requests.Timeout` returns HTTP 504 with detail
  `"Odds provider timed out"`, replacing today's generic 500.
- DB sessions are created, used, and closed inside the worker thread. Already true for both
  paths; a test pins it.
- `MLModelService._load_model` takes a `threading.Lock` so two concurrent first requests load
  the model once. `_stats_cache` writes are whole-dict replacements (atomic under the GIL); no
  change needed beyond a comment.

**Tasks:**
1. `MLBPitcherStatsCollector` accepts a timeout; `pitcher_lookup` builds its default collector with `MLBDirectAPI(timeout=5)`. Test asserts serving uses 5 and the backfill default stays 30. *(Sonnet, ~2h)*
2. `call_odds_api` passes an explicit timeout; `get_games_for_sport` maps `requests.Timeout` to 504. Test for both. *(Sonnet, ~1h)*
3. Move the analytics body into a sync method; the async entry point awaits `asyncio.to_thread(...)`. Same for `get_games_by_date`. *(Sonnet, ~2h)*
4. Add the model-load lock. Test: two threads call `predict` on an unloaded service; `joblib.load` is invoked once. *(Sonnet, ~1h)*
5. Responsiveness tests for both routes: patch the external call with a stub that blocks on a `threading.Event`; run the route as a task; assert an unrelated coroutine completes before the event is released; wrap in `asyncio.wait_for(..., 10)` as a safety net. No sub-second timing assertions. *(Opus, ~3h — novel test pattern, concurrency)*
6. Fallback tests: collector raising `requests.Timeout` yields all six pitcher features equal to the medians and a 200 response. *(Sonnet, ~1h)*

**Acceptance criteria:**
- [ ] `call_odds_api` passes an explicit timeout; a `requests.Timeout` produces HTTP 504 whose detail contains "timed out" (automated test).
- [ ] Serving-path MLB Stats API requests use a 5s timeout; backfill retains 30s (automated test asserts both values).
- [ ] With the live pitcher lookup raising `requests.Timeout`, the analytics response is 200 and all six pitcher features equal the training medians (automated test).
- [ ] For each of the two routes, while the external call is held open, an unrelated coroutine on the same loop completes; each test has a 10s safety timeout and no sub-second assertion (two automated tests).
- [ ] `MLModelService` loads the model exactly once under concurrent first use (automated test).
- [ ] Every existing analytics and games test passes unmodified: response field names and structure unchanged.
- [ ] CLAUDE.md documents the ~15s worst-case prediction latency and the 504 behavior.

**Score:** cognitive 12 (shared state) + risk 8 (4+ files) + 2 (tests) + pattern 5 = 27 → Sonnet, with task 5 escalated to Opus (concurrency-sensitive). Confidence 80%.

---

### Card 4 (#45) — Alembic migration check in CI

**Problem:** CI cannot tell whether a PR's migration applies, rolls back, or has forked the history.

**Tasks:**
1. New `migrations` job with a `postgres:14` service container. Job-level env sets `DB_URL` to the disposable database explicitly (not from secrets), plus placeholder `ODDS_API_URL` and `SECRET_KEY`, because `api.src.config` raises on import without them. *(Sonnet, ~1h)*
2. `alembic/env.py` uses `DB_URL` from the environment when set, otherwise the `alembic.ini` value. Note that `api/.env` is already loaded as a side effect of the import chain, so after this change a local `DB_URL` in `api/.env` takes precedence over `alembic.ini`; today both point at the same database. Document this in CLAUDE.md. *(Haiku, ~1h)*
3. Job steps in order: assert `alembic heads` prints exactly one head (a script counts lines and exits 1 otherwise); `alembic upgrade head`; `alembic downgrade -1`; `alembic upgrade head`. *(Sonnet, ~2h)*
4. Add `migrations` to `all-checks-passed`'s `needs` list and its success condition. *(Haiku, ~0.5h)*
5. `alembic check` as the final step. It passes on the current models today, so it is a required step: the job fails when a model changes without a migration. *(Sonnet, ~0.5h)*

**Acceptance criteria:**
- [ ] A `migrations` CI job runs on push and PR to main against a service-container PostgreSQL using its own `DB_URL`.
- [ ] The job fails when `alembic heads` reports more than one head (the counting step is a shell script with a unit test that feeds it two-head output).
- [ ] The job runs `upgrade head`, `downgrade -1`, `upgrade head` in that order and fails on any non-zero exit. Rollback coverage is the latest migration only, stated in the workflow comment.
- [ ] `all-checks-passed` requires `migrations` in both `needs` and its result check.
- [ ] `alembic check` runs last and the job fails on model drift (verified locally once by adding a throwaway column, not committed).
- [ ] CLAUDE.md states that Alembic reads `DB_URL` from the environment when set, that `api/.env` is loaded through the config import, and that all three required config variables must be present wherever Alembic runs.

**Score:** cognitive 5 + risk 4 (2-3 files) + pattern 5 = 14 → Haiku by score, assigned Sonnet because a wrong CI job blocks every later PR. Confidence 90%.

---

### Card 3 (#46) — Data-freshness guard in training

**Problem:** A stale database silently produces a stale model. Future scheduled rows in
`mlb_schedule` would make an old database look fresh if the check were naive.

**Definitions:**
- **Fresh data** = the newest `date` among schedule rows with `status == 'Final'` and both scores non-null is at most `max_staleness_days` before the reference date.
- **Reference date** = the training `end_date` (defaults to today). A historical run with `--end-date` is judged against its own window, so intentional experiments are not falsely stale.
- **No usable completed games** = stale, always. Invalid or null dates are dropped before taking the max.
- Boundary: age of exactly `max_staleness_days` is fresh; one day more is stale.

**Tasks:**
1. `check_data_freshness(schedule_df, reference_date, max_staleness_days) -> FreshnessResult(newest_date, age_days, is_stale)` in `machine_learning/data/processing/`. *(Sonnet, ~2h)*
2. Wire into `train_mlb_model.py` before any fitting: `--max-staleness-days` (default 3), `--fail-on-stale` (exit code 2 before training). Default is warn and continue. *(Sonnet, ~1h)*
3. Write `newest_completed_game_date`, `data_age_days`, `max_staleness_days`, and `freshness_reference_date` into model metadata. *(Haiku, ~0.5h)*
4. Tests: 3 days fresh vs 4 days stale; future scheduled rows ignored; empty frame stale; NaT rows dropped; `--fail-on-stale` exits 2 and never calls fit; warn mode trains. *(Sonnet, ~2h)*
5. CLAUDE.md: the check covers completed-game recency at training time only. It does not check team or pitcher stat freshness and does not monitor a deployed model. Offseason: raise `--max-staleness-days`. *(Haiku, ~0.5h)*

**Acceptance criteria:**
- [ ] Freshness uses only rows with `status == 'Final'` and non-null scores; a future scheduled row does not change the result (automated test).
- [ ] Reference date is the training `end_date`; a `--end-date` run against matching historical data reports fresh (automated test).
- [ ] Empty or all-invalid-date input reports stale (automated test).
- [ ] Age of exactly 3 days is fresh, 4 days is stale, at the default threshold (automated test).
- [ ] `--fail-on-stale` exits with code 2 before any model fitting; without it a warning is logged and training proceeds (automated tests).
- [ ] Model metadata for a new training run contains the four freshness fields.
- [ ] CLAUDE.md documents the scope limits and the offseason adjustment.

**Score:** cognitive 5 + risk 4 + 2 (tests) + pattern 0 = 11 → Haiku by score, assigned Sonnet because the definition of "fresh" is the whole card. Confidence 90%.

---

### Card 2 (#47) — Scheduler skip recording and notification

**Problem:** `schedule_updates.sh` logs `SKIP` and exits 0 when PostgreSQL is down. Two days
were missed in August 2026 before anyone noticed.

**Definitions:**
- **Marker file** `logs/mlb_update_skips.log`: one line per skipped attempt, `YYYY-MM-DD HH:MM:SS`. Skipped attempts and distinct days are both derivable from it; the resume message reports both.
- **RESUMED**, not CATCH-UP: a successful run proves updates resumed, not that every gap was recovered. The updater fetches the full season schedule but only 30 days of team stats, so if the first skip is older than 30 days the RESUMED line also prints the manual backfill command with `--start-date`.
- Notifications are best effort: `osascript` failure or absence never changes the exit code or the marker.

**Tasks:**
1. Make the readiness check, log directory, update command, and notifier injectable via environment variables (`BETBOT_PG_ISREADY`, `BETBOT_LOG_DIR`, `BETBOT_UPDATE_CMD`, `BETBOT_NOTIFY_CMD`). Default `pg_isready` path resolves through `brew --prefix postgresql@14`, falling back to the current hardcoded path. *(Sonnet, ~2h)*
2. On skip: append to the marker, notify (best effort), exit 0. *(Haiku, ~1h)*
3. On successful update: if the marker exists, log `RESUMED: N skipped attempt(s) across M day(s), first skip <date>`, notify, delete the marker. On a failed update, the marker is untouched. *(Sonnet, ~1h)*
4. `machine_learning/tests/test_schedule_updates.py`: runs the script via `subprocess` with the env overrides pointing at a temp dir and stub commands. Cases: skip creates marker; two skips give two lines; success clears marker and logs RESUMED with correct counts; failed update preserves marker; missing notifier command still records the skip and exits 0; first skip older than 30 days prints the backfill command. *(Sonnet, ~3h)*
5. Manual check: run the script with `BETBOT_PG_ISREADY=/usr/bin/false` and confirm the macOS notification appears. No need to stop PostgreSQL. *(Haiku, ~0.5h)*

**Acceptance criteria:**
- [ ] A skipped run appends one timestamped line to `logs/mlb_update_skips.log` and exits 0 (automated test).
- [ ] A successful update after skips logs a `RESUMED` line with attempt count, distinct-day count, and first-skip date, then removes the marker (automated test).
- [ ] A failed update leaves the marker unchanged (automated test).
- [ ] With the notifier command missing or failing, the skip is still recorded and the exit code is still 0 (automated test).
- [ ] When the first skip is more than 30 days old, the RESUMED line includes the `--start-date` backfill command (automated test).
- [ ] Manual: notification appears when the readiness check is overridden to fail, with PostgreSQL still running.
- [ ] CLAUDE.md documents the marker file, the env overrides, and that RESUMED does not imply full recovery.

**Score:** cognitive 8 + risk 4 + pattern 10 (no shell tests exist in the repo) = 22 → Sonnet. Confidence 85%.

---

### Estimate

| Card | Tasks | Est. hours | Model |
|---|---|---|---|
| 1 | 6 | ~10 | Sonnet, task 5 Opus |
| 4 | 5 | ~5.5 | Sonnet / Haiku |
| 3 | 5 | ~6 | Sonnet / Haiku |
| 2 | 5 | ~7.5 | Sonnet / Haiku |

### Approval

When approved: change this header to "(Active)", create four GitHub issues from the cards,
record their numbers in `.claude/sprint_status.json`, and commit per issue.

---

## Sprint 2 — Angular Upgrade (Planned)

**Goal:** Upgrade the frontend from Angular 19 to the latest stable Angular release, keeping all tests green and the app fully functional.

**Background:** The frontend currently runs Angular `^19.0.5` / CLI `^19.0.6`. Angular releases major versions every 6 months; staying current reduces security exposure and ensures access to new signals/control flow APIs. The `ng update` migration tooling handles most mechanical changes, but NgRx Signals and Jest config require manual verification.

### Acceptance Criteria

- [ ] `@angular/core`, `@angular/cli`, and all `@angular/*` packages updated to latest stable
- [ ] `@ngrx/signals` updated to a version compatible with the new Angular major (check NgRx release notes)
- [ ] `typescript` version updated to the range required by the new Angular (Angular dictates TS floor/ceiling)
- [ ] `jest-preset-angular` updated to a version compatible with the new Angular
- [ ] `ng build` produces a clean production build with no errors or warnings introduced by the upgrade
- [ ] All frontend tests pass (`npm test`)
- [ ] Dev server starts and the app is functional end-to-end (auth, game cards, analytics modal, theme toggle)
- [ ] Any automated migration schematics run by `ng update` are reviewed and committed separately from manual fixes

### Tasks

1. **Research** — Run `ng update` dry-run; review Angular changelog and migration guide for each skipped major; note breaking changes relevant to standalone components, signals, and control flow
2. **Dependency bump** — Run `ng update @angular/core @angular/cli` (use `--force` only if a peer dep conflict cannot be resolved otherwise); commit schematic output separately
3. **NgRx update** — Update `@ngrx/signals` to compatible version; review API changes to `signalStore`, `withState`, `withMethods`, `patchState`, `rxMethod`
4. **TypeScript & tooling** — Update `typescript`, `jest-preset-angular`, and `@types/*` packages to compatible versions; fix any type errors surfaced
5. **Test suite** — Run `npm test`; fix any broken specs (likely import path or API shape changes)
6. **Build verification** — Run `ng build`; resolve any template or strict-mode errors
7. **Manual smoke test** — Start dev server; verify auth flow, game list, analytics modal, and theme toggle work correctly
8. **esbuild / bundler config** — Check `angular.json` for any builder config changes required by the new version

### Risks

- **NgRx Signals API churn** — NgRx Signals is still stabilizing; minor API renames between versions are common. Check `@ngrx/signals` changelog before upgrading.
- **Jest / jest-preset-angular compatibility** — New Angular versions sometimes require a matching `jest-preset-angular` release that lags by a few weeks.
- **TypeScript strictness** — Angular upgrades sometimes raise the minimum TS version, which can surface latent type errors in existing code.
- **Schematic safety** — `ng update` schematics modify files automatically. Review every schematic change before committing to avoid unintended rewrites.

---

## Sprint 5 — MLB ML Accuracy Investigation (Active)

**Goal:** Diagnose the v1.0→v2.1 accuracy regression, implement and evaluate XGBoost and temporal sample weighting, and promote the best-performing approach to v3.0.

**Background:** v2.1 (RandomForestClassifier) achieves 54.57% on 5,304 full-season games vs v1.0's 59.1% on 808 late-season games. Root cause hypothesis: full-season variance (high early-season noise) suppresses accuracy. No temporal weighting, hyperparameter tuning, or gradient boosting has been tried. XGBoost is already installed in the venv.

### Acceptance Criteria

- [ ] `--diagnostics` flag prints per-month accuracy table, home win rate, learning curve (5 data points), and feature importance ranking
- [ ] `--model-type xgboost` trains to completion; accuracy logged vs v2.1 baseline
- [ ] `--temporal-weighting --half-life N` trains with exponential decay weights; running without flag is identical to current behavior
- [ ] `_compute_sample_weights()` unit tests pass (monotonically non-decreasing, ratio check)
- [ ] v3.0 model promoted in `ml_config.py`; accuracy ≥ 54.57%; root-cause doc committed
- [ ] All API tests pass after version bump

### Issues

| # | Title |
|---|-------|
| #29 | MLB Diagnostic Analysis: Per-Month Accuracy, Class Balance, and Learning Curves |
| #30 | Add XGBoost as a Supported MLB Model Type |
| #31 | Add Temporal Sample Weighting to MLB Model Training |
| #32 | Promote Best MLB Model Candidate to v3.0 |

### Scope Boundaries

- No pitcher/lineup player data (separate sprint)
- No hyperparameter grid search
- No LightGBM (XGBoost covers gradient boosting hypothesis)
- No frontend accuracy dashboard

---

## Lessons Learned (Running Log)

**Sprint 5 (2026-04-24)**
- v1.0's 59.1% accuracy was never a fair comparison target — it trained on ~800 late-season homogeneous games. The gap vs. v2.x is a dataset composition artifact, not a model deficiency. Always specify the test split and comparison dataset in accuracy-related ACs.
- XGBoost with default parameters scored 51.46% vs RF 55.09% — the 3.3-point gap is likely hyperparameter-driven, not algorithmic. `max_depth=6` may be too shallow; needs a tuning sprint before XGBoost can be fairly evaluated.
- The learning curve is the most actionable diagnostic: model accuracy improves monotonically to 80% of training data, confirming the model is not saturated. More 2026 data is the clearest path to higher accuracy.
- Temporal weighting (365-day half-life) gave only +0.52% — directionally correct but small. Aggressive weighting (180-day) hurts (-1.40%): discards useful 2024 signal.
- Test the CI environment (Python 3.9, only `api/requirements.txt`) mentally at test-writing time. Optional ML dependencies like xgboost must use `pytest.importorskip` to skip gracefully rather than fail.
- Commit per GitHub issue during development, not one large commit at Phase 6 — adopted as CLAUDE.md workflow policy.

**Sprint 4 (2026-04-22)**
- Match `min_games_threshold` to the rolling window size — any threshold below the window size still includes games where rolling features are partially populated (NaN→0). Threshold=10 (matching `rolling_window=10`) was correct; the initially proposed threshold=5 had minimal impact
- Verify actual DB names before migrating — `POSTGRES_DB` in docker-compose sets the default DB for the role, not necessarily what the application uses; always run `\l` in psql to confirm
- Use `brew --prefix <formula>` to resolve Homebrew binary paths — hardcoding `/opt/homebrew` or `/usr/local` breaks on cross-architecture installs
- The v1.0 vs v2.x accuracy gap remains open after the min-games fix — the residual variance is from full-season dataset composition, not early-season noise alone

**Sprint 3 (2026-04-18)**
- More training data does not guarantee better model accuracy — v2.0 trained on 5,403 games scored 53.8% accuracy vs v1.0's 59.1% on 808 games. v1.0 likely benefited from late-season homogeneity (smaller variance); v2.0 faces full two-year regular-season variance. Root cause unresolved — investigate before next retraining sprint
- A calendar-based data cutoff (e.g. post-All-Star only) is not a viable fix: early in the season (April) there is no post-All-Star data at all. Any solution must work year-round
- `n_jobs=-1` on sklearn estimators multiplies memory by core count — always set `n_jobs=1` when training on large datasets unless memory headroom is confirmed
- Retraining ACs should include a model quality floor (e.g. accuracy ≥ previous model on same test set), not just "training completed and version incremented"

**Sprint 2 (2026-04-17)**
- For Angular major-version upgrades, check `npm show @angular/core version --tag latest` before planning — `ng update` dry-run only steps one major at a time and does not reflect the true latest version on npm

**Sprint 1 (2026-04-17)**
- Specify which component owns state in AC: container components own loading/error; presentational components own display-only states
- `data-testid` attributes make tests more resilient to CSS changes — use them for test-facing elements
- `gh pr edit` is broken in this environment due to GitHub Projects (classic) deprecation; use `gh api repos/{owner}/{repo}/pulls/{n}` instead

---

## Notes

- ML `.joblib` model files are gitignored; always retrain after a fresh clone
- PostgreSQL runs on port **5432** (standard Homebrew default); local dev uses Homebrew postgresql@14
- Frontend at `localhost:4200`; API CORS is configured for that origin only
