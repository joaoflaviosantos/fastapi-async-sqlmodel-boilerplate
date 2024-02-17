# Built-in Dependencies
from datetime import datetime
from typing import Any, Dict, Tuple, Optional, List

# Third-Party Dependencies
from pydantic import BaseModel, field_validator

# Local Dependencies
from src.core.common.models import Base


class Job(Base):
    """
    Description:
    ----------
    'Job' response schema.

    Fields:
    ----------
    - 'id' (str): Unique identifier for the job.
    """

    id: str


class JobResult(BaseModel):
    """
    Description:
    ----------
    'JobResult' response schema.

    Fields:
    ----------
    - 'function' (str): Function name.
    - 'args' (list): List of arguments.
    - 'kwargs' (dict): Dictionary of keyword arguments.
    - 'job_try' (int): Number of attempts made.
    - 'enqueue_time' (datetime): Time the job was enqueued.
    - 'score' (int | None): Score of the job.
    - 'success' (bool): Whether the job succeeded or not.
    - 'result' (any): Result of the job.
    - 'start_time' (datetime): Time the job started.
    - 'finish_time' (datetime): Time the job finished.
    - 'queue_name' (str): Name of the queue.
    - 'job_id' (str | None): Unique identifier for the job.
    """

    function: str
    args: List[Any]
    kwargs: Dict[str, Any]
    job_try: int
    enqueue_time: datetime
    score: Optional[int]
    success: bool
    result: Any
    start_time: datetime
    finish_time: datetime
    queue_name: str
    job_id: Optional[str]

    @field_validator("score")
    def adjust_score(cls, v: Optional[int]) -> Optional[int]:
        """
        Convert 'None' to 'null' for 'score' field.
        """
        return None if v is None else v


class JobDef(BaseModel):
    """
    Description:
    ----------
    'JobDef' response schema.

    Fields:
    ----------
    - 'function' (str): Function name.
    - 'args' (list): List of arguments.
    - 'kwargs' (dict): Dictionary of keyword arguments.
    - 'score' (int): Score of the job.
    - 'enqueue_time' (datetime): Time the job was enqueued.
    - 'job_try' (int): Number of attempts made.
    """

    function: str
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]
    job_try: Optional[int]
    enqueue_time: datetime
    score: Optional[int]

    @field_validator("job_try")
    def adjust_job_try(cls, v: str) -> str:
        """
        Adjust the 'job_try' field to 0 if it is None.
        """
        return 0 if v is None else v


class QueueHealth(BaseModel):
    """
    Description:
    ----------
    'QueueHealth' response schema.

    Fields:
    ----------
    - 'date' (datetime): Date and time of the health check.
    - 'job_complete' (int): Number of completed jobs.
    - 'job_failed' (int): Number of failed jobs.
    - 'job_retried' (int): Number of retried jobs.
    - 'job_ongoing' (int): Number of ongoing jobs.
    - 'queued' (int): Number of queued jobs.
    """

    date: datetime
    job_complete: int
    job_failed: int
    job_retried: int
    job_ongoing: int
    queued: int

    @classmethod
    def from_string(cls, data: str) -> Optional["QueueHealth"]:
        """
        Convert 'data' string to 'QueueHealth' object.
        """
        parts = data.split()
        date_string = parts.pop(0)  # Remover e obter a primeira parte como a data
        time_string = parts.pop(0)  # Obter o horário da segunda parte
        current_year = datetime.now().year  # Obter o ano atual
        date_time_string = (
            f"{date_string} {current_year} {time_string}"  # Criar a string completa de data e hora
        )
        date_time = datetime.strptime(
            date_time_string, "%b-%d %Y %H:%M:%S"
        )  # Converter a string em um objeto datetime
        stats = {}
        for part in parts:
            key, value = part.replace("j_", "job_").split("=")
            stats[key] = int(value)
        return cls(date=date_time, **stats)
