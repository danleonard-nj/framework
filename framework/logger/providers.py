import logging

LOGGER_FORMAT = '[%(asctime)-8s]: [%(levelname)-4s]: [%(name)s]: [%(funcName)s]: %(message)s'
LOG_LEVEL = logging.INFO


def get_console_handler():
    console = logging.StreamHandler()
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
