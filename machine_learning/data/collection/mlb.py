import mlbstatsapi 
import logging
from datetime import datetime
from colorlog import ColoredFormatter
from shared.database import connect_to_db
from machine_learning.data.models.mlb_models import MLBTeam, MLBOffensiveStats, MLBDefensiveStats, MLBSchedule

def configure_logging():
    logger = logging.getLogger('statsapi')
    logger.setLevel(logging.DEBUG)
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()

    formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s - %(levelname)-8s%(reset)s - %(light_blue)s%(name)s%(reset)s - %(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        }
    )

    ch.setFormatter(formatter)
    rootLogger.addHandler(ch)

def fetch_current_season(mlb):
    current_year = datetime.now().year
    season_data = mlb.get_season(str(current_year))
    return season_data

def fetch_teams(mlb, session):
    teams = mlb.get_teams(sport_id=1)  # 1 is the sport_id for MLB
    for team in teams:
        db_team = session.query(MLBTeam).filter_by(id=team.id).first()
        if not db_team:
            db_team = MLBTeam(
                id=team.id, 
                name=team.name, 
                division=team.division.name
            )
            session.add(db_team)
    session.commit()

def fetch_team_stats(mlb, session, start_date, end_date):
    teams = session.query(MLBTeam).all()
    for team in teams:
        offensive_stats = mlb.get_team_stats(
            team.id, 
            stats=['season'], 
            groups=['hitting'], 
            start_date=start_date, 
            end_date=end_date
        )
        defensive_stats = mlb.get_team_stats(
            team.id, 
            stats=['season'], 
            groups=['pitching'], 
            start_date=start_date, 
            end_date=end_date
        )

        if offensive_stats['hitting']['season'].splits:
            hitting_stats = offensive_stats['hitting']['season'].splits[0].stat
            db_offensive_stats = MLBOffensiveStats(
                team_id=team.id,
                date=end_date,
                team_batting_average=hitting_stats.avg,
                runs_scored=hitting_stats.runs,
                home_runs=hitting_stats.homeruns,
                on_base_percentage=hitting_stats.obp,
                slugging_percentage=hitting_stats.slg
            )
            session.add(db_offensive_stats)

        if defensive_stats['pitching']['season'].splits:
            pitching_stats = defensive_stats['pitching']['season'].splits[0].stat
            db_defensive_stats = MLBDefensiveStats(
                team_id=team.id,
                date=end_date,
                team_era=pitching_stats.era,
                runs_allowed=pitching_stats.runs,
                whip=pitching_stats.whip,
                strikeouts=pitching_stats.strikeouts,
                avg_against=pitching_stats.avg
            )
            session.add(db_defensive_stats)

    session.commit()

def fetch_schedule(mlb, session, start_date, end_date):
    schedule = mlb.get_schedule(start_date=start_date, end_date=end_date, sport_id=1)
    valid_team_ids = set(team.id for team in session.query(MLBTeam).all())
    for date in schedule.dates:
        for game in date.games:
            home_team_id = game.teams.home.team.id
            away_team_id = game.teams.away.team.id

            if home_team_id in valid_team_ids and away_team_id in valid_team_ids:
                db_game = session.query(MLBSchedule).filter_by(game_id=str(game.gamepk)).first()
                if not db_game:
                    db_game = MLBSchedule(
                        game_id=str(game.gamepk),
                        date=date.date,
                        home_team_id=game.teams.home.team.id,
                        away_team_id=game.teams.away.team.id,
                        home_score=game.teams.home.score,
                        away_score=game.teams.away.score,
                        status=game.status.detailedstate
                    )
                    session.add(db_game)
                elif game.status.detailedstate == 'Final':
                    db_game.home_score = game.teams.home.score
                    db_game.away_score = game.teams.away.score
                    db_game.status = game.status.detailedstate
    session.commit()

def main():
    configure_logging()
    logging.info('Starting MLB data collection')

    mlb = mlbstatsapi.Mlb()
    session = connect_to_db()

    season_data = fetch_current_season(mlb)
    logging.info(f'Current season: {season_data.seasonid}')

    fetch_teams(mlb, session)
    logging.info('Teams fetched and stored')

    start_date = season_data.regularseasonstartdate
    end_date = datetime.now().strftime('%Y-%m-%d')

    fetch_team_stats(mlb, session, start_date, end_date)
    logging.info('Team stats fetched and stored')

    fetch_schedule(mlb, session, start_date, end_date)
    logging.info('Schedule fetched and stored')

    logging.info('MLB data collection completed')

if __name__ == '__main__':
    main()