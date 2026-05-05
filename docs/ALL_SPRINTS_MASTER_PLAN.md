# BetBot — All Sprints Master Plan

## Project

**BetBot** — Full-stack sports betting analytics app (FastAPI + PostgreSQL + Angular 19 + NgRx Signals + ML)

---

## Backlog: Next Sprint Candidates

> Prioritized list of potential work items. Reprioritize with `/sprint refine`.

### High Priority

- [ ] **Retrain v4.0 with 2026 season data** — Sprint 5 learning curve shows model is not saturated. Retrain when 2026 season has ≥ 500 completed games (est. late May 2026). v3.0 baseline is 55.09%.
- [x] **XGBoost hyperparameter tuning** — Sprint 6 randomized search (n_iter=50) found best CV 56.47% but test 50.49%; RF v3.0 retained. See `docs/sprint6_xgboost_findings.md`.
- [ ] **XGBoost re-evaluation (≥ 2,000 games)** — Re-run `--hyperparameter-search` when 2026 season has ≥ 2,000 completed games (est. late July 2026). v4.0 tuned params are the starting baseline.
- [ ] **Starting pitcher features** — ERA/WHIP/K9 for the day's scheduled starter. Highest-impact player-level feature available pre-game. Requires new DB table, data collection script, and inference-time lookup in `enhanced_mlb_analytics.py`.
- [ ] **NFL/NHL parity with MLB analytics** — Add ML-backed game analytics endpoints for NFL and NHL (currently only MLB has the ML prediction pipeline)
- [ ] **NBA analytics endpoint** — Extend the analytics system to NBA games
- [ ] **Frontend analytics integration** — Display ML predictions and confidence scores in the game cards UI (currently only available via API)
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
- [ ] **Alembic migration CI check** — Fail CI if unapplied migrations exist on branch
- [ ] **Stale data behavior investigation** — When DB data is stale, the API still returns analytics for today's games using last-known team stats. Determine whether this is expected behavior or should surface a warning/error when data is older than N days

---

## Sprint History

| Sprint | Dates | Goal | Outcome |
|--------|-------|------|---------|
| Sprint 1 | 2026-04-16 | Surface ML win probabilities in the game cards analytics modal | Merged — retro complete |
| Sprint 2 | 2026-04-17 | Upgrade Angular from v19 to v21 (via v20), NgRx to v21, jest to v30 | Merged — retro complete |
| Sprint 3 | 2026-04-18 | Backfill full 2024+2025 MLB dataset and retrain ML model v2.0 | PR #26 merged — retro complete |
| Sprint 4 | 2026-04-22 | Fix early-season ML noise (v2.1) + migrate DB to Homebrew PostgreSQL | PR #28 merged — retro complete |
| Sprint 5 | 2026-04-24 | Investigate and improve MLB model accuracy: diagnostics, XGBoost, temporal weighting → v3.0 | PR #33 open — retro complete |
| Sprint 6 | 2026-05-04 | XGBoost hyperparameter tuning via RandomizedSearchCV; evaluate v4.0 vs RF baseline | PR #36 open — retro pending |

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
