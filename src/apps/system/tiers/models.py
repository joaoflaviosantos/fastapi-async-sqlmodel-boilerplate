# Third-Party Dependencies
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String

# Local Dependencies
from src.core.common.models import (
    TimestampMixin, 
    UUIDMixin,
    Base
)

class Tier(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "system_tier"

    # Data Columns
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False, default=None)
