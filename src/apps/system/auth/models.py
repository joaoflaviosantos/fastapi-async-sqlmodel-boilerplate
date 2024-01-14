# Built-in Dependencies
from datetime import datetime

# Third-Party Dependencies
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

# Local Dependencies
from src.core.common.models import (
    TimestampMixin, 
    UUIDMixin,
    Base
)

class TokenBlacklist(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "system_token_blacklist"

    # Data Columns
    token: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False, default=None)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=None)
