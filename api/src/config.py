import os
from dotenv import load_dotenv

load_dotenv()

ODDS_API_URL = os.getenv('ODDS_API_URL')
DB_URL = os.getenv('DB_URL')
SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 30))
# Loopback by default so the dev server is not reachable from the local network.
API_HOST = os.getenv('API_HOST', '127.0.0.1')

if not all([ODDS_API_URL, DB_URL, SECRET_KEY]):
    raise ValueError("Missing required environment variables. Please check your .env file or environment settings.")