# Built-in Dependencies
from datetime import datetime, UTC
from uuid import UUID, uuid4

# Third-Party Dependencies
from sqlalchemy import DateTime
from sqlalchemy.orm import (
    DeclarativeBase, 
    MappedAsDataclass, 
    Mapped, 
    mapped_column
)

# Define a base class for declarative models with support for dataclasses
class Base(DeclarativeBase, MappedAsDataclass):
    pass


class UUIDMixin(Base):
    """
    Adds a UUID column as the primary key with a default value generated using uuid4 and server default for PostgreSQL.
    """
    __abstract__ = True
    id: Mapped[UUID] = mapped_column(default_factory=uuid4, primary_key=True, unique=True)


class TimestampMixin(Base):
    """
    Adds 'created_at' and 'updated_at' columns with default values for the creation timestamp and update timestamp.
    """
    __abstract__ = True
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default_factory=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )


class SoftDeleteMixin(Base):
    """
    Adds 'deleted_at' and 'is_deleted' columns for soft deletion functionality.
    """
    __abstract__ = True
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    is_deleted: Mapped[bool] = mapped_column(default=False, index=True)
