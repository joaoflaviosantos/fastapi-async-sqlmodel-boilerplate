# Built-in Dependencies
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

# Third-Party Dependencies
from sqlalchemy import DateTime
from sqlmodel import SQLModel, Field


# Define a base class for declarative models with support for dataclasses
class Base(SQLModel):
    pass


class UUIDMixin(SQLModel):
    """
    Adds a UUID column as the primary key with a default value generated using uuid4.
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)


class TimestampMixin(SQLModel):
    """
    Adds 'created_at' and 'updated_at' fields with default values for the creation timestamp and update timestamp.
    """

    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: Optional[datetime] = Field(default=None)


class SoftDeleteMixin(SQLModel):
    """
    Adds 'deleted_at' and 'is_deleted' fields for soft deletion functionality.
    """

    deleted_at: Optional[datetime] = Field(default=None)
    is_deleted: bool = Field(default=False, index=True)
