from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Odds(Base):
    __tablename__ = 'odds'

    id = Column(String, primary_key=True)
    time = Column(DateTime)
    home_odds = Column(String)
    away_odds = Column(String)
    home_team = Column(String)
    away_team = Column(String)
    expires = Column(DateTime)
