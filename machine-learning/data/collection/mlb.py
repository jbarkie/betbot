import statsapi
import logging
import pprint
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

def fetch_current_season():
    season_data = statsapi.latest_season()
    season_start = season_data['regularSeasonStartDate']
    is_season_started = season_start < datetime.today().strftime('%Y-%m-%d')

    if is_season_started:
        fetch_data_within_range(season_start, datetime.today().strftime('%Y-%m-%d'))
    else:
        logging.error('Current season has not started yet.')

    return season_data

def fetch_data_within_range(start_date, end_date):
    try:
        schedule = statsapi.schedule(start_date=start_date, end_date=end_date)
        logging.debug('Games between %s and %s: %s', start_date, end_date, pprint.pformat(schedule))
    except Exception as e:
        logging.error('Error fetching data: %s', e)

def main():
    configure_logging()
    logging.info('Starting')
    season_data = fetch_current_season()
    logging.info('Season data fetched for %s', season_data['seasonId'])

if __name__ == '__main__':
    main()