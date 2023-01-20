import logging
        
def get_console_handler():
    console = logging.StreamHandler()
    formatter = logging.Formatter(
        '[%(asctime)-8s] [%(thread)-4s] [%(name)-12s]: [%(levelname)-4s]: %(message)s')
    console.setFormatter(formatter)
    return console


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(get_console_handler())
    return logger
