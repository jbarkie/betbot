from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, UniqueConstraint
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
    avg_against = Column(Float)

class MLBSchedule(Base):
    __tablename__ = 'mlb_schedule'

    id = Column(Integer, primary_key=True)
    game_id = Column(String, unique=True)
    date = Column(Date)
    home_team_id = Column(Integer, ForeignKey('mlb_teams.id'))
    away_team_id = Column(Integer, ForeignKey('mlb_teams.id'))
    home_team = relationship("MLBTeam", foreign_keys=[home_team_id])
    away_team = relationship("MLBTeam", foreign_keys=[away_team_id])
    home_score = Column(Integer)
    away_score = Column(Integer)
    status = Column(String)

class MLBPitcherStats(Base):
    """
    Cumulative pre-game statistics for the starting pitcher of one team in one game.

    Values are accumulated from the pitcher's prior starts in the same season only,
    so a row never contains information from the game it describes or from any later
    game. Pitchers with no prior start that season (season debut, rookies) have NULL
    era/whip/k9; imputation is handled at feature engineering time.
    """
    __tablename__ = 'mlb_pitcher_stats'
    __table_args__ = (
        UniqueConstraint('game_id', 'team_id', name='uq_pitcher_stats_game_team'),
    )

    id = Column(Integer, primary_key=True)
    game_id = Column(String, ForeignKey('mlb_schedule.game_id'), index=True)
    team_id = Column(Integer, ForeignKey('mlb_teams.id'), index=True)
    pitcher_id = Column(Integer, index=True)
    pitcher_name = Column(String)
    era = Column(Float)
    whip = Column(Float)
    k9 = Column(Float)

MLBTeam.offensive_stats = relationship("MLBOffensiveStats", order_by=MLBOffensiveStats.date, back_populates="team")
MLBTeam.defensive_stats = relationship("MLBDefensiveStats", order_by=MLBDefensiveStats.date, back_populates="team")