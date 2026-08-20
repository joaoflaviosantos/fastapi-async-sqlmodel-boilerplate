# Built-in Dependencies
from logging.handlers import RotatingFileHandler
import json
import logging
import os

# Local Dependencies
from src.core.config import settings

TEXT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class JsonLogFormatter(logging.Formatter):
    """One JSON object per line (timestamp, level, logger, message)."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, str] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def build_formatter(log_format: str) -> logging.Formatter:
    if log_format == "json":
        return JsonLogFormatter()
    return logging.Formatter(TEXT_LOG_FORMAT)


def _log_level(name: str) -> int:
    level = logging.getLevelName(name.upper())
    if isinstance(level, int):
        return level
    return logging.DEBUG


class LoggerConfig:
    """
    Centralized logger configuration class to manage logging settings
    and ensure consistency across the application.
    """

    LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    MAX_BYTES = 10_485_760  # 10MB
    BACKUP_COUNT = 5

    @classmethod
    def get_logger(cls, filename: str) -> logging.Logger:
        """Create and return a configured logger instance."""
        logger = logging.getLogger(filename)
        log_level = _log_level(settings.LOG_LEVEL)
        logger.setLevel(log_level)
        logger.propagate = False

        if not logger.hasHandlers():
            formatter = build_formatter(settings.LOG_FORMAT)

            if settings.LOG_TO_FILE:
                os.makedirs(cls.LOG_DIR, exist_ok=True)
                log_file_path = os.path.join(cls.LOG_DIR, f"{filename}.log")
                file_handler = RotatingFileHandler(
                    log_file_path, maxBytes=cls.MAX_BYTES, backupCount=cls.BACKUP_COUNT
                )
                file_handler.setLevel(log_level)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)

            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        return logger


# Exporting default loggers
logger_postgres = LoggerConfig.get_logger(filename="postgres")
logger_redis = LoggerConfig.get_logger(filename="redis")
logger_api = LoggerConfig.get_logger(filename="api")
logger_api_test = LoggerConfig.get_logger("api_test")
logger_worker = LoggerConfig.get_logger(filename="worker")
logger_httpx = LoggerConfig.get_logger(filename="httpx")

# Other examples
# logger_sse = LoggerConfig.get_logger(filename="sse")
# logger_websocket = LoggerConfig.get_logger(filename="websocket")
# logger_rabbitmq = LoggerConfig.get_logger(filename="rabbitmq")
# logger_mqtt = LoggerConfig.get_logger(filename="mqtt")
