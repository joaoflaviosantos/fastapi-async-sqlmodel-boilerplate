# Built-in Dependencies
from typing import Dict, Optional, List, Optional

# Third-Party Dependencies
from arq.jobs import Job as ArqJob
from fastapi import APIRouter, Depends, Request

# Local Dependencies
from src.apps.system.tasks.schemas import Job, JobResult, JobDef, QueueHealth
from src.core.api.dependencies import rate_limiter
from src.core.exceptions.http_exceptions import (
    NotFoundException,
)
from src.core.utils import queue

router = APIRouter(tags=["System - Tasks"])


@router.post(
    "/system/tasks",
    response_model=Job,
    status_code=201,
    dependencies=[Depends(rate_limiter)],
)
async def create_task(message: str) -> Dict[str, str]:
    """
    Create a new background task.

    Parameters
    ----------
    message: str
        The message or data to be processed by the task.

    Returns
    ----------
    Dict[str, str]
        A dictionary containing the ID of the created task.
    """

    job = await queue.pool.enqueue_job("sample_background_task", message)  # type: ignore
    return {"id": job.job_id}


@router.get("/system/tasks/{task_id}")
async def get_task(task_id: str) -> Optional[JobDef]:
    """
    Get information about a specific background task.

    Parameters
    ----------
    task_id: str
        The ID of the task.

    Returns
    ----------
    Optional[Dict[str, Any]]
        A dictionary containing information about the task if found, or None otherwise.
    """

    job = ArqJob(job_id=str(task_id), redis=queue.pool)
    job_info: dict = await job.info()
    return job_info


@router.get("/system/tasks/processed/")
async def read_processed_tasks() -> List[JobResult]:
    """
    Get results for all background tasks that have been processed.

    Returns
    ----------
    List[Dict[str, Any]]
        A list of dictionaries containing information about each processed task.
    """

    processed_jobs = await queue.pool.all_job_results()
    return processed_jobs


@router.get("/system/tasks/pending/")
async def read_pending_tasks() -> List[JobDef]:
    """
    Get results for all background tasks that have pending processing.

    Returns
    ----------
    List[Dict[str, Any]]
        A list of dictionaries containing information about each pending task.
    """

    pending_jobs = await queue.pool.queued_jobs()
    return pending_jobs


@router.get("/system/tasks/queue-health/")
async def read_queue_health(queue_name: Optional[str] = None) -> QueueHealth:
    """
    Get the number of pending and processed tasks in the queue.

    Returns
    ----------
    Dict[str, int]
        A dictionary containing the number of pending and processed tasks.
    """

    if queue_name is None:
        queue_name = "queue"

    health_queue_from_redis = await queue.pool.get(f"arq:{queue_name}:health-check")

    if not health_queue_from_redis:
        raise NotFoundException("Task queue not found")

    queue_health = QueueHealth.from_string(health_queue_from_redis.decode("utf-8"))
    return queue_health
