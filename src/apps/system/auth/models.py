# Built-in Dependencies
from datetime import datetime

# Third-Party Dependencies
from sqlmodel import Field

# Local Dependencies
from src.core.common.models import TimestampMixin, UUIDMixin, Base


class TokenBlacklistBase(Base):
    """
    SQLModel Base

    Description:
    ----------
    'TokenBlacklistBase' pydantic class.
    """

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


class TokenBlacklist(TokenBlacklistBase, UUIDMixin, TimestampMixin, table=True):
    """
    SQLModel Table

    Description:
    ----------
    'TokenBlacklist' ORM class that maps the 'system_token_blacklist' database table.
    """

    __tablename__ = "system_token_blacklist"
