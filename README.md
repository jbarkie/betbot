# BetBot

BetBot is a sports betting application that allows users to view and analyze the latest NBA odds using machine learning. The application consists of a backend API built with Python and FastAPI, and a frontend client built with Angular. The project is still in development.

## Features

- View the latest NBA games and odds
- Odds analysis and betting suggestions via integration of machine learning algorithms

## Backend API

The backend API is responsible for user authentcation, fetching the latest odds data from an external API, caching the data in a PostgreSQL database, and serving the data to the frontend client via RESTful endpoints.

### Technologies Used

- Python
- FastAPI
- Uvicorn
- SQLAlchemy
- Alembic
- PostgreSQL
- Adminer
- Docker
- pytest
- bcrypt
- JWT

### Endpoints

- `/users/me`: Returns the user that is currently logged in.
- `/nba/games`: Returns a list of today's NBA games with their respective odds.
- `/login`: Authenticates an existing user.
- `/register`: Register an account.

### Installation

1. Clone the repository: `git clone https://github.com/jbarkie/betbot.git`
2. Navigate to the `api` directory: `cd betbot/api`
3. Install the dependencies: `pip install -r requirements.txt`
4. Set up a virtual environment:
   - From the root `betbot` directory, create your virtual environment: `virtualenv venv`
   - Activate the virtual environment: `source venv/bin/activate`
   - To deactivate: `deactivate`
5. Set up the database:
   - Install Docker Desktop and Docker Compose.
   - Start Docker Desktop.
   - Navigate to the `env` directory: `cd betbot/env`
   - Update the `docker-compose.yml` file to reflect whatever username and password will be used to access the PostgreSQL database.
   - Start the PostgreSQL database and Adminer: `docker-compose up -d`
   - The PostgreSQL databse should be accessible at `localhost:5439` and Adminer should be accessible at `localhost:9091`
6. Update the database connection URL:
   - Create new file `betbot/api/src/config.py`
   - Add the `DB_URL` variable:
   ```python
   DB_URL = 'postgresql://user:password@localhost:5439/betbot'
   ```
7. Update The Odds API URL:
   - Open file `betbot/api/src/config.py`
   - Add the `ODDS_API_URL` variable:
   ```python
   ODDS_API_URL = 'https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey=' + YOUR_API_KEY + '&regions=us&markets=h2h&bookmakers=fanduel'
   ```
8. Configure tokenization:

   - Generate a secret key that will be used to sign JWT tokens:

   ```bash
   openssl rand -hex 32
   ```

   - Open file `betbot/api/src/config.py`
   - Add the `SECRET_KEY` variable:

   ```python
   SECRET_KEY = 'your_secret_key_here'
   ```

   - Add the `ALGORITHM` and `ACCESS_TOKEN_EXPIRE_MINUTES` variables that determine the algorithm used to sign JWT tokens and the number of minutes until a token expires:

   ```python
   ALGORITHM = 'HS256'
   ACCESS_TOKEN_EXPIRE_MINUTES = 30
   ```

9. From the root `betbot` directory, run the API server: `python3 -m api.src.main`

### Running Tests

From the `api/tests` directory, run the API tests and generate a coverage report: `coverage run -m pytest && coverage report -m`

## Frontend Client

The frontend client is built with Angular and provides a user interface for viewing and analyzing the latest NBA odds.

### Technologies Used

- Angular
- TypeScript
- HTML
- daisyUI
- Tailwind CSS
- NgRx

### Installation

1. Navigate to the `frontend` directory: `cd betbot/frontend`
2. Install the dependencies: `npm i`
3. Run the development server: `ng serve -o`

## Contributing

If you find issues or have suggestions, open an issue or submit a pull request.

## License

This project is licensed under the the [BSD-3-Clause license](LICENSE).

Copyright (c) 2024, Joseph Barkie

All rights reserved.
