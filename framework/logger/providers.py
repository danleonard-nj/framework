import logging

LOG_FORMAT = '[%(asctime)-8s] [%(name)s]: [%(levelname)-4s]: [%(funcName)s]: %(message)s'


def get_console_handler():
    console = logging.StreamHandler()
    formatter = logging.Formatter(LOG_FORMAT)
    console.setFormatter(formatter)
    return console


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(get_console_handler())
    return logger
