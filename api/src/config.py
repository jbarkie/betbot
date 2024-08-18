import os
from dotenv import load_dotenv

load_dotenv()

ODDS_API_URL = os.getenv('ODDS_API_URL')
DB_URL = os.getenv('DB_URL')
SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 30))

if not all([ODDS_API_URL, DB_URL, SECRET_KEY]):
    raise ValueError("Missing required environment variables. Please check your .env file or environment settings.")