# Built-in Dependencies
from datetime import datetime, UTC
from uuid import UUID, uuid4
from typing import Optional

# Third-Party Dependencies
from sqlmodel import SQLModel, Column, Field, DateTime, func


# Define a base class for declarative models with support for dataclasses
class Base(SQLModel):
    pass


class UUIDMixin(SQLModel):
    """
    Adds a UUID column as the primary key with a default value generated using uuid4.
    """

    # Data Columns
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        description="Unique identifier (UUID) for the record",
    )


class TimestampMixin(SQLModel):
    """
    Adds 'created_at' and 'updated_at' fields with default values for the creation timestamp and update timestamp.
    """

    # Data Columns
    created_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp for the creation of the record",
    )
    updated_at: datetime = Field(
        sa_type=DateTime(timezone=True),
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": datetime.now(UTC)},
        description="Timestamp for the last update of the record",
    )


class SoftDeleteMixin(SQLModel):
    """
    Adds 'deleted_at' and 'is_deleted' fields for soft deletion functionality.
    """

    # Data Columns
    deleted_at: Optional[datetime] = Field(
        sa_type=DateTime(timezone=True),
        default=None,
        description="Timestamp for the deletion of the record (soft deletion)",
    )
    is_deleted: bool = Field(
        default=False,
        index=True,
        description="Flag indicating whether the record is deleted (soft deletion)",
    )
