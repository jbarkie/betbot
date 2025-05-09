from sqlalchemy import Boolean, Column, String, DateTime, LargeBinary

from shared.database import Base

class Odds(Base):
    __tablename__ = 'odds'

    id = Column(String, primary_key=True)
    sport = Column(String)
    time = Column(DateTime)
    home_odds = Column(String)
    away_odds = Column(String)
    home_team = Column(String)
    away_team = Column(String)
    expires = Column(DateTime)

class Users(Base):
    __tablename__ = 'users'

    username = Column(String, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    password = Column(LargeBinary)
    email_notifications_enabled = Column(Boolean, default=False)
