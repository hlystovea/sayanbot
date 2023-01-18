import logging
from logging.handlers import RotatingFileHandler


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(funcName)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler('logs/bot.log', maxBytes=5000000, backupCount=2)
    ],
)

logger = logging.getLogger()
