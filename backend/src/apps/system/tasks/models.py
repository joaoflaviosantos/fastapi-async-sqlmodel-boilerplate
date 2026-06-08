# Built-in Dependencies
from datetime import datetime, timezone
from typing import Optional, Any

# Third-Party Dependencies
from sqlmodel import Field, Column, Sequence, Integer
from sqlalchemy.types import PickleType
from celery import states

# Local Dependencies
from src.core.common.models import Base

__all__ = ("Task", "TaskSet")

task_id_sequence = Sequence("task_id_sequence", start=1)
taskset_id_sequence = Sequence("taskset_id_sequence", start=1)


class Task(Base, table=True):
    """Shared Task result/status with extended attributes."""

    __tablename__ = "sys_task_meta"
    __table_args__ = {
        "comment": "Celery Task result/status",
    }

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            Integer,
            task_id_sequence,
            primary_key=True,
            server_default=task_id_sequence.next_value(),
        ),
        description="Task id sequence",
        schema_extra={"examples": [0, 1, 2, 3]},
    )
    task_id: str = Field(max_length=155, unique=True)
    status: str = Field(default=states.PENDING, max_length=50)
    result: Optional[Any] = Field(sa_column=Column(PickleType, nullable=True))
    date_done: Optional[datetime] = Field(default=datetime.now(timezone.utc), nullable=True)
    traceback: Optional[str] = Field(nullable=True)

    # Campos estendidos
    name: Optional[str] = Field(default=None, max_length=155)
    args: Optional[bytes] = Field(nullable=True)
    kwargs: Optional[bytes] = Field(nullable=True)
    worker: Optional[str] = Field(default=None, max_length=155)
    retries: Optional[int] = Field(default=None)
    queue: Optional[str] = Field(default=None, max_length=155)

    def __init__(self, task_id: str):
        self.task_id = task_id

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "status": self.status,
            "result": self.result,
            "traceback": self.traceback,
            "date_done": self.date_done,
            "name": self.name,
            "args": self.args,
            "kwargs": self.kwargs,
            "worker": self.worker,
            "retries": self.retries,
            "queue": self.queue,
        }

    def __repr__(self):
        return f"<Task {self.task_id} state: {self.status}>"

    @classmethod
    def configure(cls, schema: Optional[str] = None, name: Optional[str] = None):
        cls.__table__.schema = schema
        cls.id.default.schema = schema
        cls.__table__.name = name or cls.__tablename__


class TaskSet(Base, table=True):
    """Shared TaskSet result."""

    __tablename__ = "sys_taskset_meta"
    __table_args__ = {"comment": "Celery TaskSet result"}

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            Integer,
            taskset_id_sequence,
            primary_key=True,
            server_default=taskset_id_sequence.next_value(),
        ),
        description="Taskset id sequence",
        schema_extra={"examples": [0, 1, 2, 3]},
    )
    taskset_id: str = Field(max_length=155, unique=True)
    result: Optional[Any] = Field(sa_column=Column(PickleType, nullable=True))
    date_done: Optional[datetime] = Field(default=datetime.now(timezone.utc), nullable=True)

    def __init__(self, taskset_id: str, result: Optional[Any] = None):
        self.taskset_id = taskset_id
        self.result = result

    def to_dict(self):
        return {
            "taskset_id": self.taskset_id,
            "result": self.result,
            "date_done": self.date_done,
        }

    def __repr__(self):
        return f"<TaskSet: {self.taskset_id}>"

    @classmethod
    def configure(cls, schema: Optional[str] = None, name: Optional[str] = None):
        cls.__table__.schema = schema
        cls.id.default.schema = schema
        cls.__table__.name = name or cls.__tablename__
