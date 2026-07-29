# Built-in Dependencies
from typing import Optional, List, Tuple

# Third-Party Dependencies
from fastapi import APIRouter, Depends, Request, Query
from sqlmodel.ext.asyncio.session import AsyncSession

# Local Dependencies
from src.apps.auth.deps import get_current_superuser
from src.core.db.session import async_get_db
from src.apps.system.rate_limits.deps import rate_limiter
from src.apps.system.tasks.deps import get_task_service, task_filters, task_sort_order
from src.apps.system.tasks.schemas import Job, TaskRead
from src.apps.system.tasks.services import TaskService
from src.core.common.schemas import PaginatedListResponse

router = APIRouter(tags=["System - Tasks"])


@router.post(
    "/system/tasks/sample",
    response_model=Job,
    status_code=201,
    dependencies=[Depends(get_current_superuser)],
)
async def create_sample_task(
    request: Request,
    message: str = Query(...),
    task_service: TaskService = Depends(get_task_service),
) -> Job:
    """
    Create a new background task.

    When a task is created, it's dispatched to Celery and the task ID is returned.
    """
    return await task_service.create_sample_shared_task(message=message)


@router.get(
    "/system/tasks/processed",
    response_model=PaginatedListResponse[TaskRead],
    dependencies=[Depends(get_current_superuser), Depends(rate_limiter)],
)
async def list_processed_tasks(
    request: Request,
    session: AsyncSession = Depends(async_get_db),
    task_service: TaskService = Depends(get_task_service),
    filters: dict = Depends(task_filters),
    sort_by: Optional[List[Tuple[str, str]]] = Depends(task_sort_order),
    page: int = 1,
    items_per_page: int = 10,
) -> dict:
    """
    Get all processed (non-pending) tasks from the database (paginated).

    Returns tasks that have been started, completed, or failed.
    """
    return await task_service.get_processed_tasks(
        session=session,
        page=page,
        items_per_page=items_per_page,
        filters=filters,
        sort_by=sort_by,
    )


@router.get(
    "/system/tasks/pending",
    response_model=List[TaskRead],
    dependencies=[Depends(get_current_superuser), Depends(rate_limiter)],
)
async def read_pending_tasks(
    request: Request,
    session: AsyncSession = Depends(async_get_db),
    task_service: TaskService = Depends(get_task_service),
) -> List[TaskRead]:
    """
    Get all pending tasks from the database.

    Returns tasks that are still in PENDING state.
    """
    return await task_service.get_pending_tasks(session=session)


@router.get(
    "/system/tasks/queue-health",
    response_model=dict,
    dependencies=[Depends(get_current_superuser), Depends(rate_limiter)],
)
async def get_queue_health(
    request: Request,
    queue_name: str = "default",
    task_service: TaskService = Depends(get_task_service),
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
    """
    return task_service.get_queue_health(queue_name=queue_name)


@router.get(
    "/system/tasks/{task_id}",
    response_model=Optional[TaskRead],
    dependencies=[Depends(get_current_superuser), Depends(rate_limiter)],
)
async def read_task(
    request: Request,
    task_id: str,
    session: AsyncSession = Depends(async_get_db),
    task_service: TaskService = Depends(get_task_service),
) -> Optional[TaskRead]:
    """
    Get task status and information.

    - If task is PENDING: returns from Celery
    - If task has been started: returns data from database (if available)
    - If task is completed/failed: returns full information from database
    """
    return await task_service.get_task(session=session, task_id=task_id)
