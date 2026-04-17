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

# Start/stop PostgreSQL (Docker)
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

### ML Prediction System

- Served via `/analytics/mlb/game?id={game_id}`; models lazy-loaded and memory-cached
- 26 engineered features: momentum (rolling win %, runs), rest days, offense (BA/OBP/SLG), defense (ERA/WHIP/K), head-to-head (last 5), temporal (month/day/weekend)
- Predictions >55% confidence use ML (`prediction_method: "machine_learning"`), else falls back to rule-based
- Supported: `random_forest` (default), `logistic_regression`
- Model info endpoint: `/analytics/mlb/model-info`

## Environment Setup

Create `api/.env`:
```
ODDS_API_URL=https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={YOUR_API_KEY}&regions=us&markets=h2h&bookmakers=fanduel
DB_URL=postgresql://user:password@localhost:5439/betbot
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Database: update `env/docker-compose.yml` credentials, ensure `alembic.ini` `sqlalchemy.url` matches `DB_URL`. Adminer UI at localhost:9091.

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
2. **Docker:** Containers must be running before starting API or running migrations
3. **Port:** PostgreSQL uses port 5439 (non-standard, to avoid local conflicts); CORS expects frontend on localhost:4200
4. **ML Data Updates:** `--skip-stats` for faster runs; full update takes 5-10 minutes; need 100+ completed games before training
5. **Sklearn Versions:** Training and API must use the same scikit-learn version — mismatches cause unpickling errors
6. **ML Models:** `.joblib` files are gitignored; API falls back to rule-based predictions if model unavailable
7. **Frontend Linting:** No `npm run lint` script; ESLint runs on save via editor (`.vscode/settings.json`); use `ng build` for type checking
