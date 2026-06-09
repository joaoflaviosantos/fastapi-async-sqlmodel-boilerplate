# Built-in Dependencies
from abc import ABC, abstractmethod
from typing import Optional

# Third-Party Dependencies
from fastapi_mail import (
    MessageSchema,
    MessageType,
)

# Local Dependencies
# Wait for the PR to be merged: https://github.com/sabuhish/fastapi-mail/pull/204
from src._overrides.fastapi_mail._fastmail import (
    FastMail,
)
from src._overrides.fastapi_mail._config import (
    ConnectionConfig,
)
from src.core.common.enums import EmailSenderType
from src.core.logger import logger_worker
from src.core.config import settings


def _get_mail_config() -> Optional[ConnectionConfig]:
    """
    Create ConnectionConfig only when SMTP settings are available.
    Returns None if settings are not configured.
    """
    if (
        settings.SMTP_HOST is None
        or settings.SMTP_USER is None
        or settings.SMTP_PASSWORD is None
        or settings.EMAILS_FROM_EMAIL is None
    ):
        return None

    return ConnectionConfig(
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=False,
        MAIL_STARTTLS=False,
        MAIL_SSL_TLS=False,
        MAIL_SERVER=settings.SMTP_HOST,
        MAIL_PORT=settings.SMTP_PORT or 587,
        MAIL_USERNAME=settings.SMTP_USER,
        MAIL_PASSWORD=settings.SMTP_PASSWORD,
        MAIL_FROM=settings.EMAILS_FROM_EMAIL,
        MAIL_FROM_NAME=settings.EMAILS_FROM_NAME or "",
        LOCAL_HOSTNAME=settings.SMTP_HOST,
    )


class EmailSender(ABC):
    @abstractmethod
    async def send_to_user(
        self,
        *,
        to_email_addr: str,
        subject: str,
        html_content: str,
        from_name: str | None = None,
        from_email_addr: str | None = None,
        email_headers: dict[str, str] = {},
        reply_to_name: str | None = None,
        reply_to_email_addr: str | None = None,
    ) -> None:
        pass


class LoggingEmailSender(EmailSender):
    async def send_to_user(
        self,
        *,
        to_email_addr: str,
        subject: str,
        html_content: str,
        from_name: str | None = None,
        from_email_addr: str | None = None,
        email_headers: dict[str, str] = {},
        reply_to_name: str | None = None,
        reply_to_email_addr: str | None = None,
    ) -> None:
        logger_worker.info(
            f"[LoggingEmailSender] Email would be sent to '{to_email_addr}' with subject '{subject}'."
        )
        logger_worker.info(f"[LoggingEmailSender] Email content:\n{html_content}")


class FastApiMailSender(EmailSender):
    def __init__(self) -> None:
        conf = _get_mail_config()
        if conf is None:
            raise ValueError(
                "SMTP settings are not configured. "
                "Please set SMTP_HOST, SMTP_USER, SMTP_PASSWORD, EMAILS_FROM_EMAIL in .env"
            )
        self.fm = FastMail(conf)

    async def send_to_user(
        self,
        *,
        to_email_addr: str,
        subject: str,
        html_content: str,
        from_name: str | None = None,
        from_email_addr: str | None = None,
        email_headers: dict[str, str] = {},
        reply_to_name: str | None = None,
        reply_to_email_addr: str | None = None,
    ) -> None:
        message = MessageSchema(
            subject=subject,
            recipients=[to_email_addr],
            body=html_content,
            subtype=MessageType.html,
            headers=email_headers,
            reply_to=f"{reply_to_name} <{reply_to_email_addr}>" if reply_to_email_addr else [],
        )

        await self.fm.send_message(message)

        logger_worker.info(
            f"Email sent via FastApiMail to '{to_email_addr}' with subject '{subject}'.",
        )


def get_email_sender() -> EmailSender:
    """
    Get the appropriate email sender based on EMAIL_SENDER setting.
    Returns LoggingEmailSender for development/testing, FastApiMailSender for production.
    """
    if settings.EMAIL_SENDER == EmailSenderType.smtp:
        return FastApiMailSender()

    # Logging in development
    return LoggingEmailSender()
