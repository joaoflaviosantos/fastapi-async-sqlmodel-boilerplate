# Built-in Dependencies
from uuid import UUID

# Third-Party Dependencies
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

# Local Dependencies
from src.core.common.models import (
    SoftDeleteMixin, 
    TimestampMixin, 
    UUIDMixin,
    Base
)

class User(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "system_user"

    # Data Columns
    name: Mapped[str] = mapped_column(String(100), nullable=False, default=None)
    username: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False, default=None)
    email: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False, default=None)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False, default=None)
    profile_image_url: Mapped[str] = mapped_column(String, default="https://www.imageurl.com/default_profile_image.jpg")
    is_superuser: Mapped[bool] = mapped_column(default=False)

    # Relationships Columns
    tier_id: Mapped[UUID | None] = mapped_column(ForeignKey('system_tier.id'), index=True, default=None)
