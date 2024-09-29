import statsapi
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

def main():
    configure_logging()
    logging.info('Starting')

if __name__ == '__main__':
    main()