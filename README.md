# BetBot
BetBot is a sports betting application that allows users to view and analyze the latest NBA odds using machine learning.The application consists of a backend API built with Python and FastAPI, and a frontend client built with Angular. 
## Features
- View the latest NBA games and odds
- Odds analysis and betting suggestions via integration of machine learning algorithms
## Backend API
The backend API is responsible for fetching the latest odds data from an external API, caching the data in a PostgreSQL database, and serving the data to the frontend client via RESTful endpoints.
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
### Endpoints
- `/status`: Returns the status of the API.
- `/nba/games`: Returns a list of today's NBA games with their respective odds.  
### Installation
1. Clone the repository: `git clone https://github.com/jbarkie/betbot.git`
2. Navigate to the `api` directory: `cd betbot/api`
3. Install the dependencies: `pip install -r requirements.txt`
4. Set up the database:
    - Install Docker Desktop and Docker Compose.
    - Start Docker Desktop.
    - Navigate to the `env` directory: `cd betbot/env`
    - Update the `docker-compose.yml` file to reflect whatever username and password will be used to access the PostgreSQL database.
    - Start the PostgreSQL database and Adminer: `docker-compose up -d`
    - The PostgreSQL databse should be accessible at `localhost:5439` and Adminer should be accessible at `localhost:9091`
5. Update the database connection URL:
    - Open `betbot/api/src/config.py`
    - Update the `DB_URL` variable:
    ```python
    DB_URL = 'postgresql://user:password@localhost:5439/betbot'
    ```
6. From the root `betbot` directory, run the API server: `python3 -m api.src.main`
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
