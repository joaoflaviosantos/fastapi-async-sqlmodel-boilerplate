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

class Post(UUIDMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "blog_post"

    # Data Columns
    title: Mapped[str] = mapped_column(String(100), nullable=False, default=None)
    text: Mapped[str] = mapped_column(String(63206), nullable=False, default=None)
    media_url: Mapped[str | None] = mapped_column(String, default=None)

    # Relationships Columns
    user_id: Mapped[UUID] = mapped_column(ForeignKey("system_user.id"), index=True, nullable=False, default=None)
