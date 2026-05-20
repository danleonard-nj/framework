import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

LOGGER_FORMAT = '[%(asctime)-8s]: [%(levelname)-4s]: [%(name)s]: [%(funcName)s]: %(message)s'
LOG_LEVEL = logging.INFO


class EasternTimeFormatter(logging.Formatter):
    """Custom formatter that converts timestamps to Eastern Time."""

    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=ZoneInfo('America/New_York'))
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()


def get_console_handler():
    console = logging.StreamHandler()

    # Use Eastern Time formatter if LOG_EST environment variable is set to true
    use_eastern_time = os.getenv('LOG_EST', '').lower() in ('true', '1', 'yes')

    if use_eastern_time:
        formatter = EasternTimeFormatter(LOGGER_FORMAT)
    else:
        formatter = logging.Formatter(LOGGER_FORMAT)

    console.setFormatter(formatter)
    return console


def get_logger(
    name: str,
    level: int = LOG_LEVEL
) -> logging.Logger:
    '''
    Get a console logger with the specified name.

    `name`: the name of the logger.
    `level`: the logging level for the logger.
    '''

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(get_console_handler())

    return logger
