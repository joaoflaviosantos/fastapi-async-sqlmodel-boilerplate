# Built-in Dependencies
from unittest.mock import MagicMock, patch

# Third-Party Dependencies
import pytest

# Local Dependencies
from src.core.common.enums import EmailSenderType
from src.core.utils.email import LoggingEmailSender, get_email_sender
from src.core.utils.log import log_system_info

pytestmark = pytest.mark.unit

_ARM_LSCPU_OUTPUT = """\
Architecture:                         aarch64
CPU op-mode(s):                       32-bit, 64-bit
Byte Order:                           Little Endian
CPU(s):                               4
On-line CPU(s) list:                  0-3
Vendor ID:                            ARM
Model name:                           Cortex-A76
Thread(s) per core:                   1
Core(s) per socket:                   -
Socket(s):                            -
Virtualization:                       -
"""


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


@patch("src.core.utils.log.psutil.cpu_freq", return_value=None)
@patch("src.core.utils.log.subprocess.run")
def test_log_system_info_arm_lscpu_dash_fields(
    mock_run: MagicMock,
    _mock_cpu_freq: MagicMock,
) -> None:
    mock_run.return_value = MagicMock(stdout=_ARM_LSCPU_OUTPUT)
    logger = MagicMock()

    log_system_info(logger)

    assert logger.info.called
    assert not logger.error.called
    message = logger.info.call_args[0][0]
    assert "threads_per_core=1" in message
    assert "cores_per_socket=1" in message
    assert "sockets=1" in message
    assert "CPU_speed=unknown" in message
