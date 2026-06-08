# Built-in Dependencies
from typing import Optional, Annotated, List

# Third-Party Dependencies
from fastapi import APIRouter, Depends, Request, HTTPException, status, Query
from celery.result import AsyncResult
from celery import states
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, not_

# Local Dependencies
from src.apps.system.tasks.tasks import sample_background_task
from src.apps.system.tasks.crud import crud_tasks
from src.apps.system.tasks.models import Task
from src.core.api.dependencies import get_current_user, async_get_db
from src.apps.system.tasks.schemas import Job, TaskRead
from src.apps.system.users.schemas import UserRead
from src.worker import app as celery_app


router = APIRouter(tags=["System - Tasks"])


@router.post(
    "/system/tasks/sample",
    response_model=Job,
    status_code=201,
)
async def create_sample_shared_task(
    request: Request,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    message: str,
) -> Job:
    """
    Create a new background task.

    When a task is created, it's dispatched to Celery and the task ID is returned.
    """
    job = sample_background_task.apply_async(args=[message])
    return Job(id=job.id)


@router.get(
    "/system/tasks/processed",
    response_model=List[TaskRead],
)
async def read_processed_tasks(
    request: Request,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(async_get_db)],
) -> List[TaskRead]:
    """
    Get all processed (non-pending) tasks from the database.

    Returns tasks that have been started, completed, or failed.
    """
    stmt = select(Task).where(not_(Task.status == states.PENDING))
    result = await session.exec(stmt)
    tasks = result.all()
    return [TaskRead.model_validate(task) for task in tasks]


@router.get(
    "/system/tasks/pending",
    response_model=List[TaskRead],
)
async def read_pending_tasks(
    request: Request,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(async_get_db)],
) -> List[TaskRead]:
    """
    Get all pending tasks from the database.

    Returns tasks that are still in PENDING state.
    """
    stmt = select(Task).where(Task.status == states.PENDING)
    result = await session.exec(stmt)
    tasks = result.all()
    return [TaskRead.model_validate(task) for task in tasks]


@router.get(
    "/system/tasks/queue-health/",
    response_model=dict,
)
async def get_queue_health(
    request: Request,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    queue_name: str = Query(default="default"),
) -> dict:
    """
    Check the health of a Celery queue.

    Parameters
    ----------
    queue_name : str
        Name of the queue to check. Defaults to "default".

    Returns
    -------
    dict
        Queue health information including message count.

    Raises
    ------
    HTTPException 404
        If the queue is not found on the broker.
    """
    try:
        with celery_app.connection_or_acquire() as conn:
            channel = conn.default_channel
            # Try to get queue info - will raise if queue doesn't exist
            queue = channel.queue_declare(queue=queue_name, passive=True)
            return {
                "queue_name": queue_name,
                "message_count": queue.message_count,
                "consumer_count": queue.consumer_count,
            }
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Queue with name '{queue_name}' not found on broker.",
        )


@router.get(
    "/system/tasks/{task_id}",
    response_model=Optional[TaskRead],
)
async def get_task(
    request: Request,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    task_id: str,
    session: Annotated[AsyncSession, Depends(async_get_db)],
) -> Optional[TaskRead]:
    """
    Get task status and information.

    - If task is PENDING: returns from Celery
    - If task has been started: returns data from database (if available)
    - If task is completed/failed: returns full information from database
    """
    # First, check Celery's result backend for the task state
    job_result = AsyncResult(id=task_id)

    # If task is still pending, return minimal info
    if job_result.state == states.PENDING:
        return TaskRead(
            id=None,
            task_id=task_id,
            status=states.PENDING,
            name=None,
            worker=None,
            queue=None,
            retries=None,
        )

    # If task has been started or is in any other state, try to fetch from database
    try:
        task_db = await crud_tasks.read_by_task_id(session=session, task_id=task_id)

        if task_db:
            return TaskRead.model_validate(task_db)
    except Exception:
        # If database lookup fails, fall back to Celery info
        pass

    # Fallback: return info from Celery result backend
    job_info = TaskRead(
        id=None,
        task_id=task_id,
        status=job_result.status,
        name=job_result.name,
        worker=None,
        queue=None,
        retries=None,
    )

    return job_info
