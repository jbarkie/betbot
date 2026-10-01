# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BetBot is a full-stack sports betting application displaying and analyzing odds for NBA, MLB, NFL, and NHL games using machine learning:

1. **Backend API** (`api/`) - FastAPI + PostgreSQL
2. **Frontend Client** (`frontend/`) - Angular 19 + NgRx Signals
3. **Machine Learning** (`machine_learning/`) - Data collection, processing, and ML model analysis

## Development Commands

### Backend API

```bash
# Run API server (from project root with venv activated)
python3 -m api.src.main

# Run tests with coverage (from project root)
coverage run -m pytest api/tests/ machine_learning/tests/ && coverage report -m

# Run a specific test file or function
pytest api/tests/test_specific_file.py::test_specific_function
pytest machine_learning/tests/test_train_mlb_model.py -v

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1

# Start/stop PostgreSQL (native Homebrew — preferred for local dev)
brew services start postgresql@14
brew services stop postgresql@14

# Start/stop PostgreSQL (Docker — CI and onboarding only)
cd env && docker-compose up -d
cd env && docker-compose down
```

### Frontend

```bash
cd frontend
npm start                 # Dev server
ng build                  # Production build
npm test                  # Jest tests
npm run test:coverage     # With coverage
npm run test:watch        # Watch mode
```

### Machine Learning

```bash
# Update MLB data
python machine_learning/scripts/update_mlb_data.py
python machine_learning/scripts/update_mlb_data.py --dry-run
python machine_learning/scripts/update_mlb_data.py --skip-stats  # faster

# Train model
python machine_learning/scripts/train_mlb_model.py
python machine_learning/scripts/train_mlb_model.py --model-type logistic_regression --version 1.1
python machine_learning/scripts/train_mlb_model.py --model-type xgboost --version 4.0
python machine_learning/scripts/train_mlb_model.py --model-type xgboost --hyperparameter-search --version 4.0  # search + train
python machine_learning/scripts/train_mlb_model.py --model-type xgboost --hyperparameter-search --search-iter 100 --version 4.0  # wider search
python machine_learning/scripts/train_mlb_model.py --temporal-weighting --half-life 365 --version 3.0
python machine_learning/scripts/train_mlb_model.py --with-pitcher-features --temporal-weighting --half-life 365 --version 3.3  # 32 features incl. starting pitcher
python machine_learning/scripts/train_mlb_model.py --diagnostics --verbose  # full diagnostic output
python machine_learning/scripts/train_mlb_model.py --fail-on-stale  # exit 2 instead of warning when data is stale
python machine_learning/scripts/train_mlb_model.py --max-staleness-days 120  # offseason: relax the freshness gate

# Install the automated daily data refresh (run once after cloning)
cp com.betbot.mlb-update.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.betbot.mlb-update.plist

# Run the scheduler manually (useful for testing or catching up missed days)
bash machine_learning/scripts/schedule_updates.sh
```

## Architecture

### Backend (`api/src/`)

- **`main.py`** - FastAPI app, CORS middleware, all route definitions
- **`config.py`** - Environment variable loading
- **`games.py`** - `get_games_for_sport()`: checks DB cache, falls back to external Odds API
- **`login.py`** - JWT logic (`create_access_token`, `authenticate_user`, `get_current_user`)
- **`register.py`** - User registration with bcrypt hashing
- **`ml_model_service.py`** - Singleton model loader/cache
- **`ml_config.py`** - Model paths, versions, feature definitions
- **`enhanced_mlb_analytics.py`** - Integrates ML predictions with game analytics
- **`models/`** - Pydantic response models AND SQLAlchemy table definitions (both in same directory)
- **`shared/database.py`** - Shared `connect_to_db()` used by both API and ML modules

### Frontend (`frontend/src/app/`)

- **Angular 19** standalone components (no NgModules)
- **NgRx Signals stores:** `auth.store.ts`, `sports.store.ts` (factory pattern via `createSportsStore(sport)`), `settings.store.ts`
- **Components:** `components/` organized by feature; each sport has a dedicated component; shared: `game`, `games-list`, `nav-bar`, `page-header`, `alert-message`, `toast`
- **Services:** `services/auth/`, `services/sports/`, `services/analytics/`, `services/theme/`
- **Styling:** Tailwind CSS + daisyUI

### Machine Learning (`machine_learning/`)

- **`data/collection/`** - MLB Stats API fetching via `python-mlb-statsapi`; team stats use direct HTTP (bypasses library for reliability)
- **`data/models/`** - SQLAlchemy models: `MLBTeam`, `MLBOffensiveStats`, `MLBDefensiveStats`, `MLBSchedule`
- **`data/processing/`** - Feature engineering and data transformation
- **`analysis/`** - Jupyter notebooks for experimentation
- **`models/mlb/`** - Trained model storage (.joblib binaries gitignored, metadata tracked)
- **`docs/`** - Sprint diagnostic findings and model analysis reports

### ML Prediction System

- Served via `/analytics/mlb/game?id={game_id}`; models lazy-loaded and memory-cached
- 32 engineered features: momentum (rolling win %, runs), rest days, offense (BA/OBP/SLG), defense (ERA/WHIP/K), head-to-head (last 5), temporal (month/day/weekend), starting pitcher (cumulative pre-game ERA/WHIP/K9 for each side)
- Predictions >55% confidence use ML (`prediction_method: "machine_learning"`), else falls back to rule-based
- Supported: `random_forest` (default), `logistic_regression`, `xgboost`
- Temporal weighting: `--temporal-weighting --half-life N` applies exponential decay so recent games have higher influence
- Hyperparameter search: `--hyperparameter-search` (XGBoost only) runs `RandomizedSearchCV` with `TimeSeriesSplit(n_splits=5)`; `--search-iter N` controls breadth (default 50); best params apply automatically to the trained model; always compare CV accuracy to holdout test accuracy — CV scores on small datasets (< ~1,500 games) are optimistic
- Starting pitcher features: `--with-pitcher-features` adds 6 columns from `mlb_pitcher_stats` (cumulative pre-game ERA/WHIP/K9 per side). Missing starters are median-imputed, never zero-filled — a 0.00 ERA would read as a perfect pitcher. Medians are saved to model metadata as `pitcher_medians` so serving matches training
- At inference, `api/src/pitcher_lookup.py` resolves starters in three tiers: stored `mlb_pitcher_stats` row → announced probable starter from the MLB Stats API → training-time medians. It never raises, so an unannounced starter degrades the prediction instead of failing the request. Results are cached for 15 minutes
- The analytics endpoint is keyed by the `odds.id` hash, which is unrelated to MLB's `gamePk`. `resolve_game_pk()` bridges them via (home_team_id, away_team_id, date) with a one-day window for UTC drift
- Feature list is split in `ml_config.py`: `MLB_BASE_FEATURES` (26) + `MLB_PITCHER_FEATURES` (6) = `MLB_REQUIRED_FEATURES` (32, the serving contract). Column order is positional — keep it stable
- Diagnostic output: `--diagnostics` prints per-month accuracy, learning curve, class balance, full feature importance
- Data freshness gate: before anything is fit, `check_data_freshness()` in `machine_learning/data/processing/data_freshness.py` finds the newest game with status `Final` and both scores recorded, dated on or before the run's `--end-date` (today by default), and compares its age to `--max-staleness-days` (default 3; exactly 3 is fresh, 4 is stale). Stale data logs a warning and training continues; `--fail-on-stale` exits with code 2 instead. Empty data or no completed games is always stale. Future scheduled rows never count. The result is saved to model metadata as `newest_completed_game_date`, `data_age_days`, `max_staleness_days`, `freshness_reference_date`. Scope: game-result recency at training time only. It does not check team or pitcher stats and does not monitor a deployed model. In the offseason, raise `--max-staleness-days` explicitly
- Gini importance overstates continuous features like ERA in Random Forests; use permutation importance on held-out data when judging whether a feature genuinely helps
- Model info endpoint: `/analytics/mlb/model-info`
- Serving latency and blocking: analytics DB queries and feature computation run via `asyncio.to_thread`, with sessions confined to the worker. Live pitcher HTTP runs on the API loop using HTTPX and one cancellable 5s budget across probable-starter and game-log calls (`LIVE_LOOKUP_BUDGET_SECONDS`). Completed pitcher results survive the deadline; missing values use training medians. This is a network budget, not a deadline for DB queries or model inference; cancellation/connection cleanup can add overhead. The synchronous historical collector retains 30s request timeouts. Results remain cached for 15 minutes. Odds API timeout still returns HTTP 504. Singleton creation and model loading are separately locked.


## Environment Setup

Create `api/.env`:
```
ODDS_API_URL=https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={YOUR_API_KEY}&regions=us&markets=h2h&bookmakers=fanduel
DB_URL=postgresql://user:password@localhost:5432/betbot
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Database (local dev): install and start native PostgreSQL via Homebrew — `brew install postgresql@14 && brew services start postgresql@14`. Create the role and database: `psql -d postgres -c "CREATE ROLE \"user\" WITH LOGIN PASSWORD 'password';"` then `psql -d postgres -c "CREATE DATABASE betbot OWNER \"user\";"`. Run `alembic upgrade head` to apply migrations. `alembic.ini` is tracked in git (it was gitignored until Sprint 8, which left CI with no Alembic config) and holds only the default local URL. Alembic uses `DB_URL` from the environment when set and falls back to `alembic.ini` `sqlalchemy.url` otherwise, so do not put a machine-specific URL in the ini file; put it in `api/.env`. Because Alembic imports the API models, `api/.env` is loaded through `api/src/config.py` as a side effect, so a local `DB_URL` there is what Alembic uses; keep it and `alembic.ini` pointing at the same database.

`docker-compose.yml` in `env/` is retained for CI and onboarding — do not remove it.

## Important Patterns

### NgRx Signals (Frontend)

Uses Signals pattern exclusively — do NOT mix with older Redux-style NgRx Store:
- `signalStore()`, `withState()`, `withComputed()`, `withMethods()`, `rxMethod()`
- Access state: `store.property()` (signals, not selectors)
- Update state: `patchState()` (not actions/reducers)

### API Route Pattern

```python
@app.get("/sport/games", response_model=GamesResponse)
async def sport_games(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    date: str = Query(..., description="Date in YYYY-MM-DD format")
):
    return await get_games_for_sport(date, "SPORT", "sport_key")
```

### Database Access

```python
from shared.database import connect_to_db
session = connect_to_db()
# ... use session ...
session.close()
```

## Testing

- **API:** pytest + pytest-mock + pytest-asyncio in `api/tests/`; `pytest.ini` sets `asyncio_mode = auto` (no need to add `@pytest.mark.asyncio` manually); mocks DB and external API calls
- **Frontend:** Jest + jest-preset-angular; `.spec.ts` co-located with components; TypeScript path aliases `@app/`, `@assets/`, `@environments/` configured in `tsconfig.spec.json`
- **ML deps:** Install separately with `pip install -r machine_learning/requirements.txt` (distinct from `api/requirements.txt`)

## CI/CD

`.github/workflows/ci-cd.yml` runs on push/PR to `main`: backend tests (Python 3.9), frontend tests (Node 18), and a `migrations` job in parallel; `all-checks-passed` requires all three. `zizmor.yml` runs security analysis on workflow files.

The `migrations` job runs against a disposable `postgres:14` service container with an explicit `DB_URL` in the workflow (not a secret). Steps, in order: `scripts/ci/assert_single_head.sh` (fails unless `alembic heads` reports exactly one head), `alembic upgrade head`, `alembic downgrade -1`, `alembic upgrade head`, `alembic check` (fails when a model changes without a migration). Rollback coverage is the latest migration only. The job also sets placeholder `ODDS_API_URL` and `SECRET_KEY` because Alembic's import chain runs `api/src/config.py`, which refuses to import without them.

## Gotchas

1. **Virtual Environment:** Activate venv before all Python commands run from project root
2. **PostgreSQL (local):** Native Homebrew PostgreSQL@14 on port 5432 is the local dev database. Start with `brew services start postgresql@14`. Docker is only used for CI.
3. **Port:** PostgreSQL uses port 5432 (standard Homebrew default); CORS expects frontend on localhost:4200
4. **ML Data Updates:** `--skip-stats` for faster runs; full update takes 5-10 minutes; need 100+ completed games before training
5. **Sklearn Versions:** Training and API must use the same scikit-learn version — mismatches cause unpickling errors
6. **ML Models:** `.joblib` files are gitignored; API falls back to rule-based predictions if model unavailable
7. **Frontend Linting:** No `npm run lint` script; ESLint runs on save via editor (`.vscode/settings.json`); use `ng build` for type checking
8. **MLB Scheduler (launchd):** install `com.betbot.mlb-update.plist` as documented in README. The scheduler discovers `pg_isready` on both Homebrew layouts without relying on PATH. Skips append timestamped attempts to `logs/mlb_update_skips.log`. On resumption, strict collection propagates missing team stats and pitcher HTTP failures; a failed run preserves the marker. If the oldest skipped morning's previous day falls outside the normal 30-day window, the scheduler passes `--recover-from YYYY-MM-DD`; schedule coverage expands and team stats are fetched in year-separated ranges, with pitcher collection covering those seasons. Completed dates remain committed and retries skip existing rows. RESUMED is not an audit of existing records. Run only one updater at a time. Env overrides and notification setup are documented in `docs/sprint8_operations_followup.md`.
9. **macOS notifications:** build the local helper with `bash machine_learning/scripts/setup_notifications.sh`, request permission with `bash machine_learning/scripts/notify_macos.sh --authorize`, then run `bash machine_learning/scripts/schedule_updates.sh --check-notification`. The ignored `.local/BetBot Notifier.app` uses the stable identity `com.betbot.notifier`; daily runs never request permission. Without the app, `osascript` remains a best-effort fallback. A successful command is not proof of visible delivery.
10. **Historical team-stat audit:** future team-stat requests use MLB's `byDateRange`, `startDate`, and `endDate`; the old `season` request ignored snake_case date filters. Existing rows and models are untouched. Audit them before retraining (GitHub #52); recovery intentionally skips already-stored rows.


## Sprint Workflow

All development follows a sprint-based Agile/Scrum workflow.

**Startup**: Run `/sprint status` at the start of every session to restore sprint context.

**Branch Policy**:
- Feature branches: `feature/YYYYMMDD_Sprint_N`
- All PRs target **main**
- Never commit directly to main

**Sprint Authority**:
- Once a sprint plan is approved in Phase 3, all tasks are pre-authorized
- Only stop for sprint stopping criteria

**Plan Durability**:
- A sprint plan must never exist only in conversation history. Before asking for Phase 3 approval, write the full draft (goal, cards, tasks, acceptance criteria) into `docs/ALL_SPRINTS_MASTER_PLAN.md` marked PROPOSED, point `.claude/sprint_status.json` at it, and commit both on the feature branch
- Approval flips the section header to Active and creates the GitHub issues; the issues are the second durable copy
- The same rule covers retrospectives and sprint-status changes: commit them as soon as they exist, marked DRAFT until approved. A committed PROPOSED or DRAFT item is not approval and never pre-authorizes work

**Planning Estimates**:
- Do not put per-task hour estimates in sprint plans; they did not predict effort (Sprint 8 retro). Keep relative card sizing, dependencies, and uncertainty. Use observed completion times if forecasting becomes useful

**Commit Discipline**:
- Commit per GitHub issue during development, not one large commit at Phase 6
- This keeps history bisectable — especially important for ML experiments where individual changes need to be revertable independently

**Key Documents**:
- `docs/ALL_SPRINTS_MASTER_PLAN.md` — Authoritative backlog and sprint history
- `docs/retrospectives/` — Per-sprint retrospective files
- `.claude/sprint_status.json` — Current sprint state

**Testing Conventions**:
- Use `data-testid` attributes on elements that tests need to query — prefer over CSS class selectors, which are brittle to style changes
- When writing acceptance criteria for UI states (loading, error, display), specify which component owns the state: container components own loading/error; presentational components own display-only states
