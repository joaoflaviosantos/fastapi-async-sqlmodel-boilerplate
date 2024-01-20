# Built-in Dependencies
from datetime import datetime

# Third-Party Dependencies
from sqlmodel import Field

# Local Dependencies
from src.core.common.models import TimestampMixin, UUIDMixin, Base


class TokenBlacklist(Base, UUIDMixin, TimestampMixin, table=True):
    """
    Table: system_token_blacklist
    """

    __tablename__ = "system_token_blacklist"

    # Data Columns
    token: str = Field(
        index=True,
        nullable=False,
        default=None,
        description="Token value for authentication",
    )
    expires_at: datetime = Field(
        nullable=False,
        default=None,
        description="Timestamp indicating the expiration date and time of the token",
    )
