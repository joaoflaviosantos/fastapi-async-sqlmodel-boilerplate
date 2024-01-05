# Built-in Dependencies
from datetime import datetime, UTC
from typing import Optional

# Third-Party Dependencies
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime

# Local Dependencies
from src.core.common.models import Base

class Tier(Base):
    __tablename__ = "tier"

    id: Mapped[int] = mapped_column(
        "id", autoincrement=True, nullable=False, unique=True, primary_key=True, init=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default_factory=lambda:  datetime.now(UTC)
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=None)
