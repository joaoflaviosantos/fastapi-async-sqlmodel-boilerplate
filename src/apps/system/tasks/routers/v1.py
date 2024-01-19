# Built-in Dependencies
from typing import Dict, Optional, Any

# Third-Party Dependencies
from arq.jobs import Job as ArqJob
from fastapi import APIRouter, Depends

# Local Dependencies
from src.core.api.dependencies import rate_limiter
from src.apps.system.tasks.schemas import Job
from src.core.utils import queue

router = APIRouter(prefix="/system/tasks", tags=["System - Tasks"])


@router.post(
    "/task",
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
    -------
    Dict[str, str]
        A dictionary containing the ID of the created task.
    """
    job = await queue.pool.enqueue_job("sample_background_task", message)  # type: ignore
    return {"id": job.job_id}


@router.get("/system/task/{task_id}")
async def get_task(task_id: str) -> Optional[Any]:
    """
    Get information about a specific background task.

    Parameters
    ----------
    task_id: str
        The ID of the task.

    Returns
    -------
    Optional[Dict[str, Any]]
        A dictionary containing information about the task if found, or None otherwise.
    """
    job = ArqJob(job_id=str(task_id), redis=queue.pool)
    job_info: dict = await job.info()
    return job_info
