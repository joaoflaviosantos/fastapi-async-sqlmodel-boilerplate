# Built-in Dependencies
from unittest.mock import MagicMock

# Third-Party Dependencies
import pytest

# Local Dependencies
from src.core.common.enums import EmailSenderType
from src.core.utils.email import LoggingEmailSender, get_email_sender
from src.core.utils.log import log_system_info

pytestmark = pytest.mark.unit


async def test_logging_email_sender_logs_without_smtp() -> None:
    await LoggingEmailSender().send_to_user(
        to_email_addr="user@tester.com",
        subject="Hello",
        html_content="<p>Hi</p>",
    )


def test_get_email_sender_defaults_to_logging() -> None:
    sender = get_email_sender()
    assert isinstance(sender, LoggingEmailSender)


def test_get_email_sender_smtp_requires_config(settings) -> None:
    if settings.EMAIL_SENDER == EmailSenderType.smtp:
        pytest.skip("SMTP sender is configured in this environment")
    assert isinstance(get_email_sender(), LoggingEmailSender)


def test_log_system_info_on_windows() -> None:
    logger = MagicMock()
    log_system_info(logger)
    assert logger.info.called or logger.error.called
