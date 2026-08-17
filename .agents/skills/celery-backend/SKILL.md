---
name: celery-backend
description: Create or change Celery tasks.py, register modules on the worker, and use async_task plus local_session. Use when adding background jobs, Beat entries, or email/async work off the request path.
---

# Celery tasks

Reference: `backend/src/apps/system/users/tasks.py`, `backend/src/worker.py`. Decorator: `src._overrides.celery.async_task.async_task`. Session: `src.core.db.session.local_session`.

## Where tasks live

Colocate `tasks.py` in the subapp that owns the work (`src.apps.system.users.tasks`). Shared samples: `src.apps.system.tasks.tasks`, `src.core.common.tasks`.

## Define a task

```python
from src._overrides.celery.async_task import async_task
from src.core.db.session import local_session
from src.worker import app

@async_task(app, name="send_welcome_email", bind=True, max_retries=3)
async def send_welcome_email(self, email: str, username: str) -> dict:
    async with local_session() as session:
        ...
    try:
        ...
        return {"status": "success"}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

- Always `@async_task`, not `@app.task`.
- Give an explicit `name=` for Beat and callers.
- Open the DB with `local_session()`, never `async_get_db` (that is a FastAPI dependency).
- Log with `logger_worker` from `src.core.logger`.

## Register

Add the module to `include=[...]` in `backend/src/worker.py`:

```python
include=[
    "src.apps.system.tasks.tasks",
    "src.apps.system.users.tasks",
    "src.core.common.tasks",
    "src.apps.<app>.<subapp>.tasks",
]
```

Periodic jobs: `app.conf.beat_schedule` in the same file (`task=` is the explicit task name).

## Do not

- Do not introduce tenant orchestrators, `async_shared_task`, or `async_tenant_task` — this project is a single schema.
- Do not forget `include`; autodiscover alone is not enough for a new module.
