import uuid as uuid_pkg
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db.database import Base

class Post(Base):
    __tablename__ = "post"

    id: Mapped[int] = mapped_column(
        "id", autoincrement=True, nullable=False, unique=True, primary_key=True, init=False
    )
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), index=True)
    title: Mapped[str] = mapped_column(String(30))
    text: Mapped[str] = mapped_column(String(63206))
    uuid: Mapped[uuid_pkg.UUID] = mapped_column(
        default_factory=uuid_pkg.uuid4, primary_key=True, unique=True
    )
    media_url: Mapped[str | None] = mapped_column(String, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default_factory=datetime.utcnow
    )
    updated_at: Mapped[datetime | None] = mapped_column(default=None)
    deleted_at: Mapped[datetime | None] = mapped_column(default=None)
    is_deleted: Mapped[bool] = mapped_column(default=False, index=True)
