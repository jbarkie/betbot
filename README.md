# BetBot

BetBot is a full-stack sports betting application that allows users to view and analyze the latest odds of games across the NBA, MLB, NFL, and NHL using machine learning. The application consists of a backend API built with Python and FastAPI, a frontend client built with Angular 19, and a machine learning module for data collection and predictive analytics. The project is still in development.

## Features

- View the latest NBA, MLB, NFL, and NHL games and odds
- User authentication with JWT tokens
- Intelligent odds caching system to minimize external API calls
- Machine learning-powered game predictions for MLB (additional sports coming soon)
- Automated daily data updates for MLB team statistics and schedules
- Advanced MLB analytics including team momentum, offensive/defensive stats, and head-to-head matchups
- Trained ML models with 55-60% prediction accuracy using RandomForest and Logistic Regression
- User settings management (email notifications, preferences)
- Responsive UI with dark/light theme support

## Quick Start

This guide assumes you have Python 3.x, Node.js, Docker Desktop, and Git installed.

1. **Clone and setup virtual environment**
   ```bash
   git clone https://github.com/jbarkie/betbot.git
   cd betbot
   virtualenv venv
   source venv/bin/activate
   ```

2. **Install dependencies**
   ```bash
   # Backend
   pip install -r api/requirements.txt

   # Frontend
   cd frontend && npm i && cd ..
   ```

3. **Start PostgreSQL database**
   ```bash
   cd env
   docker-compose up -d
   cd ..
   ```

4. **Configure environment variables**
   - Create `api/.env` file (see Backend Installation section for details)
   - Add your Odds API key, database URL, and JWT secret key

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the application**
   ```bash
   # Terminal 1 - Backend API
   python3 -m api.src.main

   # Terminal 2 - Frontend (in new terminal)
   cd frontend && ng serve -o
   ```

7. **Optional: Update MLB data and train ML model**
   ```bash
   # Update MLB data (takes 5-10 minutes)
   python machine_learning/scripts/update_mlb_data.py --verbose

   # Train ML model (requires 100+ completed games)
   python machine_learning/scripts/train_mlb_model.py --verbose
   ```

The application will be available at `http://localhost:4200` with the API running at `http://localhost:8000`.

## Backend API

The backend API is responsible for user authentication, fetching the latest odds data from an external API, caching the data in a PostgreSQL database, serving the data to the frontend client via RESTful endpoints, and providing machine learning-powered analytics.

### Technologies Used

- Python 3.x
- FastAPI
- Uvicorn
- SQLAlchemy
- Alembic
- PostgreSQL
- Adminer
- Docker & Docker Compose
- pytest & pytest-asyncio
- bcrypt
- JWT (python-jose)
- python-dotenv
- scikit-learn
- pandas
- NumPy

### API Endpoints

#### Authentication
- `POST /login`: Authenticates an existing user and returns a JWT token
- `POST /register`: Register a new user account
- `GET /users/me`: Returns the currently authenticated user

#### Sports Odds
- `GET /nba/games?date={yyyy-mm-dd}`: Returns NBA games and odds for a given date
- `GET /mlb/games?date={yyyy-mm-dd}`: Returns MLB games and odds for a given date
- `GET /nfl/games?date={yyyy-mm-dd}`: Returns NFL games and odds for a given date
- `GET /nhl/games?date={yyyy-mm-dd}`: Returns NHL games and odds for a given date

#### MLB Analytics (Machine Learning)
- `GET /analytics/mlb/game?id={game_id}`: Returns comprehensive analytics and ML prediction for a specific MLB game
- `GET /analytics/mlb/model-info`: Returns information about the currently loaded ML model (version, accuracy, features)

#### User Settings
- `GET /settings`: Returns current user settings
- `PATCH /settings`: Update user settings (e.g., email notifications)

### Database Schema

The PostgreSQL database includes the following key tables:

- **users** - User accounts with authentication credentials
- **odds** - Cached odds data from external API with expiration timestamps
- **mlb_teams** - MLB team information and current season records
- **mlb_offensive_stats** - Team batting statistics (avg, OBP, slugging, etc.)
- **mlb_defensive_stats** - Team pitching statistics (ERA, WHIP, strikeouts, etc.)
- **mlb_schedule** - Complete MLB game schedule with results

### Installation

1. Clone the repository: `git clone https://github.com/jbarkie/betbot.git`
2. Set up a virtual environment:
   - From the root `betbot` directory, create your virtual environment: `virtualenv venv`
   - Activate the virtual environment: `source venv/bin/activate`
   - To deactivate: `deactivate`
3. Navigate to the `api` directory: `cd betbot/api`
4. Install the dependencies: `pip install -r requirements.txt`
5. Set up the database:
   - Install Docker Desktop and Docker Compose.
   - Start Docker Desktop.
   - Navigate to the `env` directory: `cd betbot/env`
   - Update the `docker-compose.yml` file to reflect whatever username and password will be used to access the PostgreSQL database.
   - Start the PostgreSQL database and Adminer: `docker-compose up -d`
   - The PostgreSQL databse should be accessible at `localhost:5439` and Adminer should be accessible at `localhost:9091`
6. Set up environment variables:
   - Create new file `betbot/api/.env`
   - Add the following environment variables:
   ```python
   ODDS_API_URL = 'https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={YOUR_API_KEY}&regions=us&markets=h2h&bookmakers=fanduel'
   DB_URL = 'postgresql://user:password@localhost:5439/betbot'
   ```
   - Replace `user`, `password`, `{YOUR_API_KEY}` accordingly.
7. Configure tokenization:

   - Generate a secret key that will be used to sign JWT tokens:

   ```bash
   openssl rand -hex 32
   ```

   - Open file `betbot/api/.env`
   - Add the `SECRET_KEY` variable:

   ```python
   SECRET_KEY = 'your_secret_key_here'
   ```

   - Add the `ALGORITHM` and `ACCESS_TOKEN_EXPIRE_MINUTES` variables that determine the algorithm used to sign JWT tokens and the number of minutes until a token expires:

   ```python
   ALGORITHM = 'HS256'
   ACCESS_TOKEN_EXPIRE_MINUTES = 30
   ```

9. Run database migrations to create all tables:
   ```bash
   # From the root betbot directory
   alembic upgrade head
   ```

10. From the root `betbot` directory, run the API server: `python3 -m api.src.main`

### Running Tests

From the root `betbot` directory, run the API tests and generate a coverage report:
```bash
cd api/tests
coverage run -m pytest && coverage report -m
```

To run a specific test:
```bash
pytest api/tests/test_specific_file.py::test_specific_function
```

## Frontend Client

The frontend client is built with Angular 19 (standalone components) and provides a responsive user interface for viewing and analyzing sports odds and ML predictions across all supported leagues.

### Technologies Used

- Angular 19 (standalone components, no NgModules)
- TypeScript
- HTML
- Tailwind CSS
- daisyUI
- NgRx Signals (modern state management)
- RxJS
- Jest

### Architecture Highlights

- **State Management**: NgRx Signals with `signalStore()` pattern (not Redux-style NgRx Store)
- **Routing**: Protected routes using `authGuard` for authenticated sections
- **Components**: Feature-based organization (nba, mlb, nfl, nhl components with dedicated stores)
- **Services**: Auth, sports data, analytics, theme management
- **Styling**: Tailwind CSS utility classes with daisyUI component library

### Installation

1. Navigate to the `frontend` directory: `cd betbot/frontend`
2. Install the dependencies: `npm i`
3. Run the development server: `ng serve -o` (or `npm start`)

The application will open at `http://localhost:4200`

### Running Tests

```bash
npm test                  # Run Jest tests
npm run test:coverage     # Generate coverage report
npm run test:verbose      # Verbose output
npm run test:watch        # Watch mode
npm run test:full         # Coverage + verbose
```

### Building for Production

```bash
ng build
```

Build artifacts will be stored in the `dist/` directory.

## Machine Learning Module

The machine learning module is responsible for automated data collection, feature engineering, model training, and production serving of ML predictions. Currently focused on MLB game predictions with 55-60% accuracy, the module includes data collection scripts, training pipelines, and production model serving.

### Technologies Used

- **python-mlb-statsapi** - Python wrapper for MLB's official Stats API
- **SQLAlchemy** - Database ORM for MLB data tables
- **scikit-learn** - ML algorithms (RandomForest, LogisticRegression)
- **pandas & NumPy** - Data manipulation and feature engineering
- **Jupyter** - Experimental notebooks for model development
- **Matplotlib & Seaborn** - Data visualization
- **joblib** - Model serialization
- **colorlog** - Enhanced logging for scripts
- **python-dotenv** - Environment configuration

### ML System Architecture

The production ML system follows this flow:

1. **Data Collection** - Automated daily updates of MLB team stats and schedules
2. **Feature Engineering** - 26 features including momentum, rest days, offense/defense stats, head-to-head history
3. **Model Training** - Offline training with historical game data (minimum 100 games required)
4. **Model Serving** - Models lazy-loaded and cached in API memory for fast predictions
5. **Graceful Fallback** - Automatic fallback to rule-based predictions if ML unavailable

### Supported Models

- **RandomForestClassifier** (default) - 55-60% accuracy, provides feature importance rankings
- **LogisticRegression** - 52-57% accuracy, faster predictions

### Model Features (26 Total)

The ML models use the following engineered features:

- **Momentum**: Rolling win percentage, runs scored/allowed (last 10 games)
- **Rest**: Days since last game for each team
- **Offense**: Batting average, OBP, slugging percentage
- **Defense**: ERA, WHIP, strikeouts per 9 innings
- **Head-to-Head**: Recent matchup history (last 5 games)
- **Temporal**: Month, day of week, weekend indicator

### Data Collection Scripts

#### Update MLB Data

Updates all MLB data tables (teams, offensive stats, defensive stats, schedule):

```bash
# From project root with venv activated
python machine_learning/scripts/update_mlb_data.py

# Options
python machine_learning/scripts/update_mlb_data.py --dry-run      # Preview changes without saving
python machine_learning/scripts/update_mlb_data.py --verbose      # Detailed logging
python machine_learning/scripts/update_mlb_data.py --skip-stats   # Update only teams/schedule (faster)
```

**Note**: Full updates with team statistics can take 5-10 minutes due to rate limiting on the MLB Stats API.

#### Train ML Models

Train new prediction models using historical game data:

```bash
# Train RandomForest model (default)
python machine_learning/scripts/train_mlb_model.py

# Train with custom options
python machine_learning/scripts/train_mlb_model.py \
    --model-type random_forest \
    --version 1.0 \
    --test-split 0.2 \
    --verbose

# Train LogisticRegression model
python machine_learning/scripts/train_mlb_model.py \
    --model-type logistic_regression \
    --version 1.1
```

**Requirements**:
- Minimum 100 completed games in the database
- Recent offensive and defensive stats for all teams
- Virtual environment with scikit-learn, pandas, joblib installed

**Output**: Trained models are saved to `machine_learning/models/mlb/` with `.joblib` extension and metadata in `model_metadata.json`

#### Automated Daily Updates

Set up automated daily data updates using cron:

```bash
# Make the script executable
chmod +x machine_learning/scripts/schedule_updates.sh

# Test manual execution
./machine_learning/scripts/schedule_updates.sh

# Add to crontab for daily updates at 6 AM
crontab -e
# Add this line:
# 0 6 * * * /absolute/path/to/betbot/machine_learning/scripts/schedule_updates.sh
```

### Production ML Integration

The API serves ML predictions through the `/analytics/mlb/game?id={game_id}` endpoint:

1. API receives analytics request for a specific game
2. `EnhancedMLBAnalytics` calculates team statistics and features
3. Attempts ML prediction:
   - Loads trained model (cached after first use)
   - Prepares 26 engineered features
   - Generates prediction with confidence score
4. If confidence > 55%, returns ML prediction with feature importance
5. Otherwise, falls back to rule-based statistical comparison
6. Response includes `prediction_method` field ("machine_learning" or "rule_based")

**Key Files**:
- `api/src/ml_model_service.py` - Model loading and serving (singleton pattern)
- `api/src/ml_config.py` - Model paths, versions, feature definitions
- `api/src/enhanced_mlb_analytics.py` - ML integration with analytics

### Jupyter Notebooks

Experimental notebooks for model development and analysis are located in `machine_learning/analysis/`. These notebooks explore feature engineering, model selection, hyperparameter tuning, and visualization before production integration.

### Important Notes

- Model `.joblib` files are gitignored; train locally or obtain from team storage
- Training and API must use the same scikit-learn version to avoid unpickling errors
- Models gracefully degrade to rule-based predictions if unavailable
- Minimum 100 completed games required for reliable model training

## Contributing

If you find issues or have suggestions, open an issue or submit a pull request.

## Project Structure

```
betbot/
├── api/                          # Backend API (FastAPI)
│   ├── src/
│   │   ├── main.py              # API initialization and route definitions
│   │   ├── config.py            # Environment configuration
│   │   ├── models/              # Pydantic and SQLAlchemy models
│   │   ├── login.py             # JWT authentication logic
│   │   ├── register.py          # User registration logic
│   │   ├── games.py             # Odds fetching and caching
│   │   ├── mlb_analytics.py     # MLB analytics endpoint
│   │   ├── enhanced_mlb_analytics.py  # ML-integrated analytics
│   │   ├── ml_model_service.py  # ML model loading and serving
│   │   └── ml_config.py         # ML configuration
│   ├── tests/                   # pytest test suite
│   └── docs/                    # API documentation
├── frontend/                     # Angular 19 frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/      # Feature components (nba, mlb, nfl, nhl)
│   │   │   ├── services/        # Auth, sports, analytics services
│   │   │   ├── guards/          # Route guards
│   │   │   └── stores/          # NgRx Signals state stores
│   │   └── assets/              # Static assets
│   └── dist/                    # Production build output
├── machine_learning/            # ML module
│   ├── data/
│   │   ├── collection/          # MLB Stats API data fetching
│   │   ├── processing/          # Feature engineering
│   │   └── models/              # SQLAlchemy models for MLB tables
│   ├── scripts/
│   │   ├── update_mlb_data.py   # Data update script
│   │   ├── train_mlb_model.py   # Model training script
│   │   └── schedule_updates.sh  # Cron wrapper script
│   ├── analysis/                # Jupyter notebooks
│   └── models/mlb/              # Trained model storage (.joblib files)
├── shared/
│   └── database.py              # Shared database connection
├── env/
│   └── docker-compose.yml       # PostgreSQL + Adminer setup
├── alembic/                     # Database migrations
├── CLAUDE.md                    # Claude Code project instructions
└── README.md                    # This file
```

## License

This project is licensed under the [BSD-3-Clause license](LICENSE).

Copyright (c) 2024-2025, Joseph Barkie

All rights reserved.
