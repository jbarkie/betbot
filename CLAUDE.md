# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BetBot is a full-stack sports betting application that displays and analyzes odds for NBA, MLB, NFL, and NHL games using machine learning. The project consists of three main components:

1. **Backend API** (`api/`) - FastAPI-based REST API with PostgreSQL database
2. **Frontend Client** (`frontend/`) - Angular 19 application with NgRx signals
3. **Machine Learning Module** (`machine_learning/`) - Data collection, processing, and ML model analysis

## Development Commands

### Backend API

**Run the API server:**
```bash
# From project root with virtual environment activated
python3 -m api.src.main
```

**Run tests with coverage:**
```bash
# From project root
cd api/tests
coverage run -m pytest && coverage report -m
```

**Run specific test:**
```bash
# From project root
pytest api/tests/test_specific_file.py::test_specific_function
```

**Database migrations (Alembic):**
```bash
# Create a new migration
alembic revision --autogenerate -m "migration description"

# Apply migrations
alembic upgrade head

# Revert migration
alembic downgrade -1
```

**Start PostgreSQL database (Docker):**
```bash
cd env
docker-compose up -d

# Stop database
docker-compose down
```

### Frontend Client

**Run development server:**
```bash
cd frontend
ng serve -o
# Or using npm
npm start
```

**Build for production:**
```bash
cd frontend
ng build
```

**Run tests:**
```bash
cd frontend
npm test                  # Run Jest tests
npm run test:coverage     # With coverage report
npm run test:verbose      # Verbose output
npm run test:watch        # Watch mode
npm run test:full         # Coverage + verbose
```

### Machine Learning Module

**Update MLB data manually:**
```bash
# From project root with venv activated
python machine_learning/scripts/update_mlb_data.py

# Dry run (no changes)
python machine_learning/scripts/update_mlb_data.py --dry-run

# Verbose output
python machine_learning/scripts/update_mlb_data.py --verbose

# Skip team stats (faster, only teams/records/schedule)
python machine_learning/scripts/update_mlb_data.py --skip-stats
```

**Train ML prediction models:**
```bash
# Train RandomForest model (default)
python machine_learning/scripts/train_mlb_model.py

# Train with options
python machine_learning/scripts/train_mlb_model.py \
    --model-type random_forest \
    --version 1.0 \
    --test-split 0.2 \
    --verbose

# Train LogisticRegression model
python machine_learning/scripts/train_mlb_model.py \
    --model-type logistic_regression \
    --version 1.1

# Requires: at least 100 completed games in database
```

**Schedule automated updates:**
```bash
# Make script executable
chmod +x machine_learning/scripts/schedule_updates.sh

# Run manually
./machine_learning/scripts/schedule_updates.sh

# Add to crontab for daily updates at 6 AM
crontab -e
# Add: 0 6 * * * /path/to/betbot/machine_learning/scripts/schedule_updates.sh
```

## Architecture

### Backend API Structure

- **`api/src/main.py`** - FastAPI app initialization, CORS middleware, and all route definitions
- **`api/src/config.py`** - Environment variable configuration (ODDS_API_URL, DB_URL, SECRET_KEY, etc.)
- **`api/src/models/`** - Pydantic models for request/response validation AND SQLAlchemy table definitions
  - `tables.py` - Database table models (Odds, Users)
  - `auth.py` - Authentication models
  - `games.py` - Game/odds response models
  - `mlb_analytics.py` - MLB analytics models
- **`api/src/login.py`** - JWT authentication logic (create_access_token, authenticate_user, get_current_user)
- **`api/src/register.py`** - User registration logic with bcrypt password hashing
- **`api/src/games.py`** - Core function `get_games_for_sport()` that fetches odds from external API or database cache
- **`api/src/mlb_analytics.py`** - MLB game analytics endpoint logic
- **`api/src/settings.py`** - User settings (email notifications, etc.)
- **`shared/database.py`** - Shared SQLAlchemy Base and `connect_to_db()` function used across API and ML modules

### Frontend Architecture

- **Angular 19** with standalone components (no NgModules)
- **State Management:** NgRx Signals (not the older NgRx Store pattern)
  - `auth.store.ts` - Authentication state (token, isAuthenticated)
  - `sports.store.ts` - Sports data state with `createSportsStore(sport)` factory pattern
  - `settings.store.ts` - User settings state
  - Stores use `signalStore()`, `withState()`, `withComputed()`, `withMethods()`, and `rxMethod()` from @ngrx/signals
- **Routing:** `app.routes.ts` defines all routes with `authGuard` protecting authenticated routes
- **Components:** Organized by feature in `frontend/src/app/components/`
  - Each sport (nba, mlb, nfl, nhl) has dedicated component with corresponding store provider
  - Shared components: alert-message, toast, nav-bar, page-header, game, games-list
- **Services:** Located in `frontend/src/app/services/`
  - `auth/` - Authentication service and guard
  - `sports/` - Sports data service and store factory
  - `analytics/` - MLB analytics service
  - `theme/` - Theme switching service
- **Styling:** Tailwind CSS + daisyUI component library

### Machine Learning Module Structure

- **`machine_learning/data/collection/`** - Data fetching from MLB Stats API
  - Uses `python-mlb-statsapi` library
  - Direct HTTP API implementation for team statistics (bypasses library for reliability)
- **`machine_learning/data/models/`** - SQLAlchemy models for MLB data tables
  - MLBTeam, MLBOffensiveStats, MLBDefensiveStats, MLBSchedule
- **`machine_learning/data/processing/`** - Data transformation and feature engineering
- **`machine_learning/analysis/`** - Jupyter notebooks for ML model experimentation
- **`machine_learning/scripts/`** - Production scripts
  - `update_mlb_data.py` - Main data update script (updates all 4 MLB tables)
  - `schedule_updates.sh` - Bash wrapper for cron scheduling

### Database Schema

**Key Tables:**
- `odds` - Cached odds data from external API (id, sport, time, home_team, away_team, home_odds, away_odds, expires)
- `users` - User accounts (username PK, first_name, last_name, email, password hash, email_notifications_enabled)
- `mlb_teams` - MLB team information and current records
- `mlb_offensive_stats` - Team batting statistics
- `mlb_defensive_stats` - Team pitching statistics
- `mlb_schedule` - Game schedule and results

**Database Connection:** PostgreSQL running in Docker on port 5439 (mapped from container port 5432)

### Authentication Flow

1. User registers via `/register` endpoint → password hashed with bcrypt → JWT token created
2. User logs in via `/login` endpoint → credentials validated → JWT token returned
3. Protected endpoints require JWT token via `Depends(get_current_user)` dependency
4. Frontend stores token in AuthStore, includes in Authorization header for API requests
5. Token expires after `ACCESS_TOKEN_EXPIRE_MINUTES` (default 30 minutes)

### Odds Data Flow

1. Frontend requests games for specific date and sport
2. API checks database cache in `get_games_for_sport()` function
3. If cached data exists and not expired, return from database
4. If no cache or expired, fetch from external Odds API (the-odds-api.com)
5. Store new data in database with expiration timestamp
6. Return formatted data to frontend
7. Frontend displays odds in sport-specific component using games-list/game components

### Machine Learning Integration

**Production ML System:**
- Trained models served via `/analytics/mlb/game?id={game_id}` endpoint
- Models lazy-loaded and cached in memory for performance
- Automatic fallback to rule-based predictions if ML unavailable
- Model metadata available via `/analytics/mlb/model-info` endpoint

**ML Prediction Flow:**
1. API receives game analytics request
2. `EnhancedMLBAnalytics` calculates team statistics (rolling wins, momentum, etc.)
3. Attempts ML prediction:
   - Prepares 26 engineered features
   - Loads trained model (cached after first use)
   - Gets prediction with confidence score
4. If ML prediction confident (>55% probability):
   - Returns ML prediction with feature importance
   - Sets `prediction_method: "machine_learning"`
5. Else fallback to rule-based:
   - Uses statistical comparison
   - Sets `prediction_method: "rule_based"`

**Key Components:**
- `api/src/ml_model_service.py` - Model loading and serving (singleton pattern)
- `api/src/ml_config.py` - Model paths, versions, feature definitions
- `api/src/enhanced_mlb_analytics.py` - Integrates ML predictions with analytics
- `machine_learning/scripts/train_mlb_model.py` - Model training script
- `machine_learning/models/mlb/` - Model storage (binaries gitignored, metadata tracked)

**Model Features (26 total):**
- Momentum: rolling win %, runs scored/allowed (last 10 games)
- Rest: days since last game for each team
- Offense: batting avg, OBP, slugging %
- Defense: ERA, WHIP, strikeouts
- Head-to-head: recent matchup history (last 5 games)
- Temporal: month, day of week, weekend flag

**Supported Models:**
- RandomForestClassifier (default) - 55-60% accuracy, provides feature importance
- LogisticRegression - 52-57% accuracy, faster predictions

**Model Training Requirements:**
- Minimum 100 completed games in database
- Recent offensive/defensive stats for all teams
- Virtual environment with scikit-learn, pandas, joblib installed

## Environment Setup

### Required Environment Variables

Create `api/.env` with:
```
ODDS_API_URL=https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={YOUR_API_KEY}&regions=us&markets=h2h&bookmakers=fanduel
DB_URL=postgresql://user:password@localhost:5439/betbot
SECRET_KEY=your_secret_key_here  # Generate with: openssl rand -hex 32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Database Configuration

1. Update `env/docker-compose.yml` with desired PostgreSQL credentials
2. Ensure `alembic.ini` sqlalchemy.url matches your DB_URL
3. Database accessible at localhost:5439, Adminer UI at localhost:9091

## Important Patterns

### NgRx Signals Pattern (Frontend)

The frontend uses NgRx Signals (modern pattern), NOT the older Redux-style NgRx Store:
- Use `signalStore()` to create stores
- Access state with `store.property()` (signals, not selectors)
- Update state with `patchState()` (not actions/reducers)
- Use `rxMethod()` for observable-based side effects
- Use `withComputed()` for derived state (not selectors)

### API Route Pattern

All API routes in `main.py` follow this pattern:
```python
@app.get("/sport/games", response_model=GamesResponse)
async def sport_games(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    date: str = Query(..., description="Date in YYYY-MM-DD format")
):
    return await get_games_for_sport(date, "SPORT", "sport_key")
```

### Database Access Pattern

Both API and ML modules use the shared database connection:
```python
from shared.database import connect_to_db
session = connect_to_db()
# ... use session ...
session.close()
```

### Error Handling

- API uses FastAPI's HTTPException for error responses
- Frontend services handle errors in rxMethod() with tapResponse()
- ML scripts use try/except with detailed logging

## Testing Notes

- **API Tests:** Use pytest with pytest-mock and pytest-asyncio, located in `api/tests/`
- **Frontend Tests:** Use Jest with jest-preset-angular, test files co-located with components (*.spec.ts)
- Always run coverage reports to ensure adequate test coverage
- API tests mock database connections and external API calls

## Common Gotchas

1. **Virtual Environment:** Always activate venv before running Python commands from project root
2. **Database Connection:** Ensure Docker containers are running before starting API or running migrations
3. **CORS:** Frontend must run on localhost:4200 (configured in main.py middleware)
4. **JWT Secret:** Never commit .env files; each environment needs unique SECRET_KEY
5. **ML Data Updates:** Team statistics updates can take 5-10 minutes; use --skip-stats for faster testing
6. **Port Conflicts:** PostgreSQL uses non-standard port 5439 to avoid conflicts with local installations
7. **Module Imports:** Python imports use absolute paths from project root (e.g., `from api.src.config import ...`)
8. **NgRx Signals:** Don't mix old NgRx Store patterns with new Signals pattern - this codebase uses Signals exclusively
9. **ML Models:** Model .joblib files are gitignored; train locally or download from team storage; API gracefully falls back to rule-based if model unavailable
10. **Model Training:** Need minimum 100 completed games in database to train; run data update script first if insufficient data
11. **Sklearn Versions:** Training and API must use same scikit-learn version; mismatches cause unpickling errors
