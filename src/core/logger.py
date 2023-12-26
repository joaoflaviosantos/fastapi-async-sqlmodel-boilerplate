# Built-in Dependencies
from logging.handlers import RotatingFileHandler
import logging
import os

# Local Dependencies
from src.core.config import settings

# Constants
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE_PATH = os.path.join(LOG_DIR, 'app.log')

LOGGING_LEVEL = logging.INFO
LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Configuring the basic logging settings
logging.basicConfig(level=LOGGING_LEVEL, format=LOGGING_FORMAT)

# Configuring a rotating file handler for logging
file_handler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=10485760, backupCount=5)
file_handler.setLevel(LOGGING_LEVEL)
file_handler.setFormatter(logging.Formatter(LOGGING_FORMAT))

# Adding the file handler to the root logger
logging.getLogger('').addHandler(file_handler)
