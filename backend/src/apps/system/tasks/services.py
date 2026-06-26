# Built-in Dependencies
from typing import Optional, List

# Third-Party Dependencies
from fastapi import HTTPException, status
from celery.result import AsyncResult
from celery import states
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, func, col, or_
from sqlalchemy import not_ as sa_not

# Local Dependencies
from src.apps.system.tasks.tasks import sample_background_task
from src.apps.system.tasks.repositories import TaskRepository, task_repository
from src.apps.system.tasks.models import Task
from src.apps.system.tasks.schemas import Job, TaskRead
from src.worker import app as celery_app
from src.core.utils.paginated import compute_offset, paginated_response


class TaskService:
    def __init__(self, task_repo: TaskRepository):
        self.task_repo = task_repo

    async def create_sample_shared_task(self, message: str) -> Job:
        job = sample_background_task.apply_async(args=[message])
        return Job(id=job.id)

    async def get_processed_tasks(
        self, session: AsyncSession, page: int = 1, items_per_page: int = 10
    ) -> dict:
        stmt_count = (
            select(func.count()).select_from(Task).where(sa_not(col(Task.status) == states.PENDING))
        )
        count_result = await session.exec(stmt_count)
        total_count = count_result.one()

        stmt = (
            select(Task)
            .where(sa_not(col(Task.status) == states.PENDING))
            .offset(compute_offset(page, items_per_page))
            .limit(items_per_page)
        )
        result = await session.exec(stmt)
        tasks = result.all()
        data = [TaskRead.model_validate(task) for task in tasks]

        return paginated_response(
            data={"data": data, "total_count": total_count},
            page=page,
            items_per_page=items_per_page,
        )

    async def get_pending_tasks(self, session: AsyncSession) -> List[TaskRead]:
        stmt = select(Task).where(
            or_(
                Task.status == states.STARTED,
                Task.status == states.RETRY,
                Task.status == states.PENDING,
                Task.status == states.RECEIVED,
            )
        )
        result = await session.exec(stmt)
        tasks = result.all()
        return [TaskRead.model_validate(task) for task in tasks]

    def get_queue_health(self, queue_name: str) -> dict:
        is_known_queue = queue_name in celery_app.amqp.queues
        try:
            with celery_app.connection_or_acquire() as conn:
                channel = conn.default_channel
                # In Redis (virtual transport), passive=True raises an error if the list is empty.
                # If it's a known Celery queue, we use passive=False to safely get the 0 count.
                # If it's unknown, we use passive=True to return 404 if it truly doesn't exist.
                queue = channel.queue_declare(queue=queue_name, passive=not is_known_queue)

                message_count = queue.message_count
                consumer_count = queue.consumer_count

                # Fallback to calculate real consumer count if the broker reports 0 (e.g. Redis)
                if consumer_count == 0:
                    try:
                        i = celery_app.control.inspect()
                        active_queues = i.active_queues()
                        if active_queues:
                            stats = i.stats() or {}
                            for worker_name, queues in active_queues.items():
                                if any(q.get("name") == queue_name for q in queues):
                                    worker_stats = stats.get(worker_name, {})
                                    pool_stats = worker_stats.get("pool", {})
                                    concurrency = pool_stats.get("max-concurrency", 1)
                                    consumer_count += concurrency
                    except Exception:
                        pass  # Ignore inspect errors so it doesn't break health check

                return {
                    "queue_name": queue_name,
                    "message_count": message_count,
                    "consumer_count": consumer_count,
                }
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Queue with name '{queue_name}' not found on broker.",
            )

    async def get_task(self, session: AsyncSession, task_id: str) -> Optional[TaskRead]:
        # First, check Celery's result backend for the task state
        job_result = AsyncResult(id=task_id)

        # If task is still pending, return minimal info
        try:
            task_state = job_result.state
        except AttributeError:
            # Backend may be disabled or unavailable, try database lookup
            task_state = None

        if task_state == states.PENDING:
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
            task_db = await self.task_repo.read_by_task_id(session=session, task_id=task_id)

            if task_db:
                return TaskRead.model_validate(task_db)
        except Exception:
            # If database lookup fails, fall back to Celery info
            pass

        # Fallback: return info from Celery result backend
        try:
            job_info = TaskRead(
                id=None,
                task_id=task_id,
                status=job_result.status,
                name=job_result.name,
                worker=None,
                queue=None,
                retries=None,
            )
        except AttributeError:
            # Backend may be disabled or unavailable
            job_info = TaskRead(
                id=None,
                task_id=task_id,
                status=states.PENDING,
                name=None,
                worker=None,
                queue=None,
                retries=None,
            )

        return job_info


# Module-level singleton
task_service = TaskService(task_repository)
