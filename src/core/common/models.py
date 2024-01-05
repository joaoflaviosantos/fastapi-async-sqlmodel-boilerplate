# Built-in Dependencies
from datetime import datetime, UTC
import uuid as uuid_pkg

# Third-Party Dependencies
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass
from sqlalchemy import Column, DateTime, Boolean, text
from sqlalchemy.dialects.postgresql import UUID

# Define a base class for declarative models with support for dataclasses
class Base(DeclarativeBase, MappedAsDataclass):
    pass


class UUIDMixin:
    """
    Adds a UUID column as the primary key with a default value generated using uuid4 and server default for PostgreSQL.
    """
    uuid: uuid_pkg.UUID = Column(
        UUID, primary_key=True, default=uuid_pkg.uuid4, server_default=text("gen_random_uuid()")
    )


class TimestampMixin:
    """
    Adds 'created_at' and 'updated_at' columns with default values for the creation timestamp and update timestamp.
    """
    created_at: datetime = Column(
        DateTime(timezone=True), default=datetime.now(UTC), server_default=text("current_timestamp(0)")
    )
    updated_at: datetime = Column(
        DateTime(timezone=True), nullable=True, onupdate=datetime.now(UTC), server_default=text("current_timestamp(0)")
    )


class SoftDeleteMixin:
    """
    Adds 'deleted_at' and 'is_deleted' columns for soft deletion functionality.
    """
    deleted_at: datetime = Column(DateTime(timezone=True), nullable=True)
    is_deleted: bool = Column(Boolean, default=False)
