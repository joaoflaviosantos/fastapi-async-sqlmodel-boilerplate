# Built-in Dependencies
from typing import Optional

# Third-Party Dependencies
from sqlmodel.ext.asyncio.session import AsyncSession

# Local Dependencies
from src.core.common.repository import RepositoryBase
from src.apps.system.tasks.models import Task
from src.apps.system.tasks.schemas import (
    TaskCreateInternal,
    TaskUpdate,
    TaskUpdateInternal,
    TaskDelete,
)


class TaskRepository(
    RepositoryBase[Task, TaskCreateInternal, TaskUpdate, TaskUpdateInternal, TaskDelete]
):
    """
    Extended Repository operations for Task model with Celery-specific methods.
    """

    async def read_by_task_id(self, session: AsyncSession, task_id: str) -> Optional[Task]:
        """
        Fetch a task from database by its Celery task_id.

        Parameters
        ----------
        session : AsyncSession
            The SQLModel async session.
        task_id : str
            The Celery task ID to search for.

        Returns
        -------
        Optional[Task]
            The Task object if found, None otherwise.
        """
        try:
            result = await self.get(session, task_id=task_id)
            if result:
                return Task(**result)
            return None
        except Exception:
            return None


# Create an instance of TaskRepository for the 'Task' model
task_repository = TaskRepository(Task)
