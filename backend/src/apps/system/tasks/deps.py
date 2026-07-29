# Built-in Dependencies
from typing import Optional, List, Tuple

# Third-Party Dependencies
from fastapi import Query

# Local Dependencies
from src.apps.system.tasks.services import TaskService, task_service
from src.core.utils.api_params import parse_sort_order


async def get_task_service() -> TaskService:
    return task_service


def task_filters(
    task_id: Optional[str] = Query(None, description="Task ID"),
    status: Optional[str] = Query(None, description="Task status"),
    name: Optional[str] = Query(None, description="Task name"),
    worker: Optional[str] = Query(None, description="Worker name"),
    queue: Optional[str] = Query(None, description="Queue name"),
    retries: Optional[int] = Query(None, description="Retry count"),
) -> dict:
    filters_dict = {
        "task_id": task_id,
        "status": status,
        "name": name,
        "worker": worker,
        "queue": queue,
        "retries": retries,
    }

    return {key: value for key, value in filters_dict.items() if value is not None}


def task_sort_order(
    sort_by: Optional[List[str]] = Query(None, description="Sort fields"),
) -> List[Tuple[str, str]] | None:
    allowed_sort_fields = [
        "id",
        "task_id",
        "status",
        "name",
        "worker",
        "queue",
        "retries",
        "date_done",
    ]
    sort_order_result = parse_sort_order(
        sort_by=sort_by,
        allowed_sort_fields=allowed_sort_fields,
    )
    return sort_order_result if len(sort_order_result) > 0 else None
