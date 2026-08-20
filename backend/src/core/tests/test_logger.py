# Built-in Dependencies
import json
import logging
from io import StringIO

# Third-Party Dependencies
import pytest

# Local Dependencies
from src.core.logger import JsonLogFormatter, TEXT_LOG_FORMAT, build_formatter

pytestmark = pytest.mark.unit


def _record(message: str = "hello") -> logging.LogRecord:
    return logging.LogRecord(
        name="api",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=(),
        exc_info=None,
    )


def test_text_formatter_keeps_human_line() -> None:
    record = _record()
    formatted = build_formatter("text").format(record)
    assert "hello" in formatted
    assert "INFO" in formatted
    assert formatted == logging.Formatter(TEXT_LOG_FORMAT).format(record)


def test_json_formatter_is_one_object_per_line() -> None:
    formatted = build_formatter("json").format(_record("ready"))
    payload = json.loads(formatted)
    assert payload["level"] == "INFO"
    assert payload["logger"] == "api"
    assert payload["message"] == "ready"
    assert "timestamp" in payload


def test_json_formatter_includes_exception() -> None:
    record = _record()
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        record.exc_info = sys.exc_info()
    payload = json.loads(JsonLogFormatter().format(record))
    assert "ValueError" in payload["exception"]


def test_text_and_json_formatters_write_to_stream() -> None:
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(build_formatter("json"))
    logger = logging.getLogger("test_log_format_stream")
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.info("ping")
    line = stream.getvalue().strip()
    assert json.loads(line)["message"] == "ping"
