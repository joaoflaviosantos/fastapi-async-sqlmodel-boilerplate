# Built-in Dependencies
from uuid import UUID

# Third-Party Dependencies
from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

# Local Dependencies
from src.core.common.models import (
    TimestampMixin, 
    UUIDMixin,
    Base
)

class RateLimit(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "system_rate_limit"

    # Data Columns
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False, default=None)
    path: Mapped[str] = mapped_column(String, nullable=False, default=None)
    limit: Mapped[int] = mapped_column(Integer, nullable=False, default=None)
    period: Mapped[int] = mapped_column(Integer, nullable=False, default=None)

    # Relationships Columns
    tier_id: Mapped[UUID] = mapped_column(ForeignKey("system_tier.id"), index=True, nullable=False, default=None)
