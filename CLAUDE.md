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

# Run tests with coverage
cd api/tests && coverage run -m pytest && coverage report -m

# Run specific test
pytest api/tests/test_specific_file.py::test_specific_function

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
python machine_learning/scripts/train_mlb_model.py --model-type xgboost --version 3.0-xgb
python machine_learning/scripts/train_mlb_model.py --temporal-weighting --half-life 365 --version 3.0
python machine_learning/scripts/train_mlb_model.py --diagnostics --verbose  # full diagnostic output

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
- 26 engineered features: momentum (rolling win %, runs), rest days, offense (BA/OBP/SLG), defense (ERA/WHIP/K), head-to-head (last 5), temporal (month/day/weekend)
- Predictions >55% confidence use ML (`prediction_method: "machine_learning"`), else falls back to rule-based
- Supported: `random_forest` (default), `logistic_regression`, `xgboost`
- Temporal weighting: `--temporal-weighting --half-life N` applies exponential decay so recent games have higher influence
- Diagnostic output: `--diagnostics` prints per-month accuracy, learning curve, class balance, full feature importance
- Model info endpoint: `/analytics/mlb/model-info`

## Environment Setup

Create `api/.env`:
```
ODDS_API_URL=https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={YOUR_API_KEY}&regions=us&markets=h2h&bookmakers=fanduel
DB_URL=postgresql://user:password@localhost:5432/betbot
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Database (local dev): install and start native PostgreSQL via Homebrew — `brew install postgresql@14 && brew services start postgresql@14`. Create the role and database: `psql -d postgres -c "CREATE ROLE \"user\" WITH LOGIN PASSWORD 'password';"` then `psql -d postgres -c "CREATE DATABASE betbot OWNER \"user\";"`. Run `alembic upgrade head` to apply migrations. Ensure `alembic.ini` `sqlalchemy.url` matches `DB_URL`.

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

`.github/workflows/ci-cd.yml` runs on push/PR to `main`: backend tests (Python 3.9) and frontend tests (Node 18) in parallel. `zizmor.yml` runs security analysis on workflow files.

## Gotchas

1. **Virtual Environment:** Activate venv before all Python commands run from project root
2. **PostgreSQL (local):** Native Homebrew PostgreSQL@14 on port 5432 is the local dev database. Start with `brew services start postgresql@14`. Docker is only used for CI.
3. **Port:** PostgreSQL uses port 5432 (standard Homebrew default); CORS expects frontend on localhost:4200
4. **ML Data Updates:** `--skip-stats` for faster runs; full update takes 5-10 minutes; need 100+ completed games before training
5. **Sklearn Versions:** Training and API must use the same scikit-learn version — mismatches cause unpickling errors
6. **ML Models:** `.joblib` files are gitignored; API falls back to rule-based predictions if model unavailable
7. **Frontend Linting:** No `npm run lint` script; ESLint runs on save via editor (`.vscode/settings.json`); use `ng build` for type checking
8. **MLB Scheduler (launchd):** `com.betbot.mlb-update.plist` must be copied to `~/Library/LaunchAgents/` and loaded with `launchctl load` after a fresh clone — it is not active automatically. The scheduler requires Homebrew PostgreSQL to be accepting connections on port 5432; if it is not ready it logs a SKIP message and exits immediately.

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
