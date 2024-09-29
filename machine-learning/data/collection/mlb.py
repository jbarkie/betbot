import statsapi
import logging

def configure_logging():
    logger = logging.getLogger('statsapi')
    logger.setLevel(logging.DEBUG)
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)8s - %(name)s - %(message)s')
    ch.setFormatter(formatter)
    rootLogger.addHandler(ch)

def main():
    configure_logging()
    logging.info('Starting')

if __name__ == '__main__':
    main()