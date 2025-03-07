# BetBot

BetBot is a sports betting application that allows users to view and analyze the latest odds of games across the NBA, MLB, NFL, and NHL using machine learning. The application consists of a backend API built with Python and FastAPI, and a frontend client built with Angular. The project is still in development.

## Features

- View the latest NBA games and odds
- View the latest MLB games and odds
- View the latest NFL games and odds
- View the latest NHL games and odds
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
- python-dotenv

### Endpoints

- `/users/me`: Returns the user that is currently logged in.
- `/nba/games?date={yyyy-mm-dd}`: Returns a list of NBA games and respective betting odds for a given date.
- `/mlb/games?date={yyyy-mm-dd}`: Returns a list of MLB games and respective betting odds for a given date. 
- `/nfl/games?date={yyyy-mm-dd}`: Returns a list of NFL games and respective betting odds for a given date. 
- `/nhl/games?date={yyyy-mm-dd}`: Returns a list of NHL games and respective betting odds for a given date. 
- `/login`: Authenticates an existing user.
- `/register`: Register an account.

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
- Jest

### Installation

1. Navigate to the `frontend` directory: `cd betbot/frontend`
2. Install the dependencies: `npm i`
3. Run the development server: `ng serve -o`

### Running Tests

To run the frontend client unit tests: `npm test`

## Machine Learning Module

The machine learning module is responsible for data collection, processing, and the analysis of various machine learning models in their ability to predict the outcome of professional sports games. A collection of Jupyter Notebooks explore the improvement of these analyses before their integration with the backend API and frontend client.

### Technologies Used

- python-mlb-statsapi (Python Wrapper for the MLB's Official Stats API)
- SQLAlchemy
- Jupyter 
- pandas
- NumPy
- Matplotlib
- Seaborn
- python-dotenv
- scikit-learn
- colorlog

## Contributing

If you find issues or have suggestions, open an issue or submit a pull request.

## License

This project is licensed under the the [BSD-3-Clause license](LICENSE).

Copyright (c) 2024, Joseph Barkie

All rights reserved.
