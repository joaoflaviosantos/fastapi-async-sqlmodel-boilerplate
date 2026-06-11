# Built-in Dependencies
from typing import Optional, List

# Third-Party Dependencies
from fastapi import HTTPException, status
from celery.result import AsyncResult
from celery import states
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, not_

# Local Dependencies
from src.apps.system.tasks.tasks import sample_background_task
from src.apps.system.tasks.repositories import TaskRepository
from src.apps.system.tasks.models import Task
from src.apps.system.tasks.schemas import Job, TaskRead
from src.worker import app as celery_app


class TaskService:
    def __init__(self, task_repo: TaskRepository):
        self.task_repo = task_repo

    async def create_sample_shared_task(self, message: str) -> Job:
        job = sample_background_task.apply_async(args=[message])
        return Job(id=job.id)

    async def get_processed_tasks(self, session: AsyncSession) -> List[TaskRead]:
        stmt = select(Task).where(not_(Task.status == states.PENDING))
        result = await session.exec(stmt)
        tasks = result.all()
        return [TaskRead.model_validate(task) for task in tasks]

    async def get_pending_tasks(self, session: AsyncSession) -> List[TaskRead]:
        stmt = select(Task).where(Task.status == states.PENDING)
        result = await session.exec(stmt)
        tasks = result.all()
        return [TaskRead.model_validate(task) for task in tasks]

    def get_queue_health(self, queue_name: str) -> dict:
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
