# Built-in Dependencies
from typing import Optional, Annotated

# Third-Party Dependencies
from fastapi import APIRouter, Depends, Request, HTTPException, status
from celery.result import AsyncResult
from celery import states
from sqlmodel.ext.asyncio.session import AsyncSession

# Local Dependencies
from src.apps.admin.tasks.tasks import sample_background_task
from src.apps.admin.tasks.crud import crud_tasks
from src.core.api.dependencies import get_current_user, async_get_db
from src.apps.admin.tasks.schemas import Job, TaskRead
from src.apps.admin.users.schemas import UserRead


router = APIRouter(tags=["Worker"])


@router.post(
    "/worker/tasks/sample",
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
    "/worker/tasks/{task_id}",
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
