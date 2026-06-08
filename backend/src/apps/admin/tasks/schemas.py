# Built-in Dependencies
from typing import Any, Optional
from datetime import datetime

# Third-Party Dependencies
from pydantic import BaseModel, ConfigDict, field_validator
from celery import states

# Local Dependencies
from src.apps.admin.tasks.models import Task
from backend.src._overrides.pydantic.optional import optional


class TaskBase(BaseModel):
    """Base schema for Task with common fields."""

    task_id: str
    status: str = states.PENDING
    name: Optional[str] = None
    worker: Optional[str] = None
    queue: Optional[str] = None
    retries: Optional[int] = None


class Task(TaskBase):
    """Full Task schema with all fields including results."""

    id: Optional[int] = None
    result: Optional[Any] = None
    traceback: Optional[str] = None
    args: Optional[bytes] = None
    kwargs: Optional[bytes] = None
    date_done: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TaskRead(TaskBase):
    """Schema for reading Task from database."""

    id: Optional[int] = None
    result: Optional[Any] = None
    traceback: Optional[str] = None
    date_done: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TaskCreate(TaskBase):
    """Schema for creating a new Task."""

    model_config = ConfigDict(extra="forbid")


class TaskCreateInternal(TaskCreate):
    """Internal schema for Task creation with all fields."""

    pass


@optional()
class TaskUpdate(TaskBase):
    """Schema for updating Task (all fields optional)."""

    model_config = ConfigDict(extra="forbid")


class TaskUpdateInternal(TaskUpdate):
    """Internal schema for Task update with timestamp."""

    date_done: Optional[datetime] = None


class TaskDelete(BaseModel):
    """Schema for soft delete operations."""

    model_config = ConfigDict(extra="forbid")


class Job(BaseModel):
    """Response schema for task creation (Celery job)."""

    id: str
