from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from shared.database import Base

class MLBTeam(Base):
    __tablename__ = 'mlb_teams'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    division = Column(String)
    games_played = Column(Integer)
    wins = Column(Integer)
    losses = Column(Integer)
    winning_percentage = Column(Float)

class MLBOffensiveStats(Base):
    __tablename__ = 'mlb_offensive_stats'

    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('mlb_teams.id'))
    team = relationship("MLBTeam", back_populates="offensive_stats")
    date = Column(Date)
    team_batting_average = Column(Float)
    runs_scored = Column(Integer)
    home_runs = Column(Integer)
    on_base_percentage = Column(Float)
    slugging_percentage = Column(Float)

class MLBDefensiveStats(Base):
    __tablename__ = 'mlb_defensive_stats'

    id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey('mlb_teams.id'))
    team = relationship("MLBTeam", back_populates="defensive_stats")
    date = Column(Date)
    team_era = Column(Float)
    runs_allowed = Column(Integer)
    whip = Column(Float)
    strikeouts = Column(Integer)
    fielding_percentage = Column(Float)

class MLBSchedule(Base):
    __tablename__ = 'mlb_schedule'

    id = Column(Integer, primary_key=True)
    game_id = Column(String, unique=True)
    date = Column(Date)
    home_team_id = Column(Integer, ForeignKey('mlb_teams.id'))
    away_team_id = Column(Integer, ForeignKey('mlb_teams.id'))
    home_team = relationship("MLBTeam", foreign_keys=[home_team_id])
    away_team = relationship("MLBTeam", foreign_keys=[away_team_id])

MLBTeam.offensive_stats = relationship("MLBOffensiveStats", order_by=MLBOffensiveStats.date, back_populates="team")
MLBTeam.defensive_stats = relationship("MLBDefensiveStats", order_by=MLBDefensiveStats.date, back_populates="team")