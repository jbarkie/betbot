from api.src.config import DB_URL
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def format_american_odds(decimal_odds):
    if decimal_odds == 1:
        return "None"
    elif decimal_odds > 2:
        underdog_odds = round(100 * (decimal_odds - 1))
        return f"+{underdog_odds}"
    else:
        favorite_odds = round(100 / (decimal_odds - 1))
        return f"-{favorite_odds}"

def connect_to_db():
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session