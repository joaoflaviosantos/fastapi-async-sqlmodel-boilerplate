# Built-in Dependencies
from datetime import datetime

# Third-Party Dependencies
from sqlmodel import Field

# Local Dependencies
from src.core.common.models import TimestampMixin, UUIDMixin, Base


class TokenBlacklist(Base, TimestampMixin, UUIDMixin, table=True):
    __tablename__ = "system_token_blacklist"

    # Data Columns
    token: str = Field(index=True, nullable=False, default=None)
    expires_at: datetime = Field(nullable=False, default=None)
