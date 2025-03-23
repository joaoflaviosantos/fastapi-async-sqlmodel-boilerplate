# Built-in Dependencies
from logging.handlers import RotatingFileHandler
import logging
import os


class LoggerConfig:
    """
    Centralized logger configuration class to manage logging settings
    and ensure consistency across the application.
    """

    LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(LOG_DIR, exist_ok=True)  # Ensure the log directory exists

    LOGGING_LEVEL = logging.INFO
    LOGGING_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    MAX_BYTES = 10_485_760  # 10MB
    BACKUP_COUNT = 5

    @classmethod
    def get_logger(cls, filename: str) -> logging.Logger:
        """Create and return a configured logger instance."""
        logger = logging.getLogger(filename)
        logger.setLevel(cls.LOGGING_LEVEL)
        logger.propagate = False  # Prevent logs from propagating to the root logger

        # Avoid duplicate handlers
        if not logger.hasHandlers():
            log_file_path = os.path.join(cls.LOG_DIR, f"{filename}.log")

            # File handler with log rotation
            file_handler = RotatingFileHandler(
                log_file_path, maxBytes=cls.MAX_BYTES, backupCount=cls.BACKUP_COUNT
            )
            file_handler.setLevel(cls.LOGGING_LEVEL)
            file_handler.setFormatter(logging.Formatter(cls.LOGGING_FORMAT))
            logger.addHandler(file_handler)

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(cls.LOGGING_LEVEL)
            console_handler.setFormatter(logging.Formatter(cls.LOGGING_FORMAT))
            logger.addHandler(console_handler)

        return logger


# Exporting default loggers
logger_db = LoggerConfig.get_logger(filename="postgres")
# logger_db_test = LoggerConfig.get_logger("db_test")

logger_redis = LoggerConfig.get_logger(filename="redis")
# logger_redis_test = LoggerConfig.get_logger("redis_test")

logger_api = LoggerConfig.get_logger(filename="api")
logger_api_test = LoggerConfig.get_logger("api_test")

logger_worker = LoggerConfig.get_logger(filename="worker")
# logger_worker_test = LoggerConfig.get_logger("worker_test")


# Other examples
# logger_sse = LoggerConfig.get_logger(filename="sse")
# logger_sse_test = LoggerConfig.get_logger("sse_test")

# logger_rabbitmq = LoggerConfig.get_logger(filename="rabbitmq")
# logger_rabbitmq_test = LoggerConfig.get_logger("rabbitmq_test")

# logger_mqtt = LoggerConfig.get_logger(filename="mqtt")
# logger_mqtt_test = LoggerConfig.get_logger("mqtt_test")
