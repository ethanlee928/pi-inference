import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def hello() -> str:
    logger.info("HELLO WORLD!")
    return "World"
