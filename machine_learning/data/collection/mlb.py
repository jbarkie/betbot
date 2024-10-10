import mlbstatsapi 
import logging
from datetime import datetime
from colorlog import ColoredFormatter

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
    current_season_data = mlb.get_season(str(datetime.today().year))
    regular_season_start_date = current_season_data.regularseasonstartdate

    is_season_started = regular_season_start_date < datetime.today().strftime('%Y-%m-%d')

    if is_season_started:
        fetch_data_within_range(regular_season_start_date, datetime.today().strftime('%Y-%m-%d'))
    else:
        logging.error('Current season has not started yet.')

    return current_season_data

def fetch_data_within_range(start_date, end_date):
    try:
        logging.info('Fetching data from %s to %s', start_date, end_date)
    except Exception as e:
        logging.error('Error fetching data: %s', e)

def main():
    configure_logging()
    logging.info('Starting')
    mlb = mlbstatsapi.Mlb()
    season_data = fetch_current_season(mlb)
    logging.debug('Current season: %s', season_data)

if __name__ == '__main__':
    main()