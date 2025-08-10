import logging
import os

log_level = os.getenv("LOG_LEVEL", "DEBUG").upper()

log_level = getattr(logging, log_level, logging.DEBUG)

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(message)s',
)


logger = logging.getLogger()
logger.setLevel(log_level)