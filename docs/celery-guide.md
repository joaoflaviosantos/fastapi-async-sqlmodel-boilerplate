# Celery Guide

## Overview

Celery is a distributed task queue system for Python, used in this project for handling background tasks asynchronously. Combined with the `async_task` decorator, it supports full async/await operations, enabling seamless integration with the async database (SQLModel/SQLAlchemy) and Redis connections used throughout the application.

## Introduction to Celery

[Celery](https://docs.celeryq.dev/en/stable/) is a robust, production-ready task queue that supports scheduling, retries, and result backends. In this project, it uses **Redis** as the message broker and **PostgreSQL** as the result backend.

### Key Features

- **Distributed Task Queue:** Celery enables efficient distribution of tasks across multiple workers.
- **Async Task Support:** Through the custom `async_task` decorator (`src/_overrides/celery/async_task.py`), async/await coroutines are fully supported as Celery tasks.
- **Scheduled Tasks (Beat):** Celery Beat provides periodic task scheduling (e.g., health checks every 30 seconds).
- **Result Backend:** Task results are persisted in PostgreSQL for tracking and auditing.
- **Retry Mechanism:** Built-in retry support with configurable backoff strategies.
- **FastAPI Compatibility:** Seamless integration with the FastAPI async ecosystem.

## Architecture

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   FastAPI    │──────▶│    Redis     │◀──────│   Celery    │
│   (Producer) │       │   (Broker)   │       │  (Worker)   │
└─────────────┘       └─────────────┘       └──────┬──────┘
                                                     │
                                              ┌──────▼──────┐
                                              │  PostgreSQL  │
                                              │  (Results)   │
                                              └─────────────┘
```

## Configuration

The Celery application is configured in `src/worker.py`:

- **Broker:** `settings.REDIS_BROKER_URL` (Redis)
- **Result Backend:** `settings.POSTGRES_CELERY_URI` (PostgreSQL, scheme `db+postgresql://`)
- **Timezone:** UTC
- **Default Queue:** `default`
- **Concurrency:** 4 workers

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_BROKER_HOST` | (falls back to `REDIS_CACHE_HOST`) | Redis broker host |
| `REDIS_BROKER_PORT` | `6379` | Redis broker port |
| `REDIS_BROKER_USERNAME` | `` | Redis broker username |
| `REDIS_BROKER_PASSWORD` | `` | Redis broker password |
| `REDIS_BROKER_USE_SSL` | `False` | Enable SSL for broker connection |

The `POSTGRES_CELERY_URI` is automatically derived from the existing PostgreSQL settings (`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_SERVER`, `POSTGRES_PORT`, `POSTGRES_DB`).

## Running the Celery Worker

To start the Celery worker:

```bash
poetry run celery -A src.worker:app worker --loglevel=info
```

## Running Celery Beat (Scheduler)

To start the periodic task scheduler:

```bash
poetry run celery -A src.worker:app beat --loglevel=info
```

## Running Worker + Beat Together (Development)

For development convenience, you can run both in a single process:

```bash
poetry run celery -A src.worker:app worker --beat --loglevel=info
```

## Creating Async Tasks

All tasks in this project use the `@async_task` decorator to support async/await:

```python
from src._overrides.celery.async_task import async_task
from src.worker import app

@async_task(app, name="my_task_name", bind=True, max_retries=3)
async def my_task(self, param1: str, param2: str) -> dict:
    # You can use async DB sessions, async Redis, etc.
    async for db in async_get_db():
        # ... async database operations
        pass

    return {"status": "success"}
```

### How It Works

The `async_task` decorator (in `src/_overrides/celery/async_task.py`) uses `asgiref.sync.AsyncToSync` to bridge async coroutines into Celery's synchronous task execution model. This allows you to:

- Use `async/await` syntax in your tasks
- Access the async database session (`async_get_db()`)
- Use `redis.asyncio` for Redis operations
- Call any async library or function

## Registered Tasks

| Task Name | Module | Type | Description |
|-----------|--------|------|-------------|
| `send_welcome_email` | `src.apps.admin.users.tasks` | On-demand | Sends welcome email when a new user is created (log simulation) |
| `check_database_and_redis_health` | `src.core.common.tasks` | Beat (30s) | Periodic health check for PostgreSQL and Redis connectivity |

## Calling Tasks

### From FastAPI endpoints or services:

```python
from src.apps.admin.users.tasks import send_welcome_email

# Async dispatch (non-blocking)
send_welcome_email.delay("user@example.com", "username")

# With options
send_welcome_email.apply_async(
    args=["user@example.com", "username"],
    countdown=10,  # delay 10 seconds
    queue="default",
)
```

## Monitoring

### Flower (Web UI)

You can use [Flower](https://flower.readthedocs.io/) for real-time monitoring:

```bash
poetry run celery -A src.worker:app flower --port=5555
```

Then access `http://localhost:5555` in your browser.

### CLI Inspection

```bash
# List active tasks
poetry run celery -A src.worker:app inspect active

# List registered tasks
poetry run celery -A src.worker:app inspect registered

# List scheduled tasks
poetry run celery -A src.worker:app inspect scheduled
```

---

[Back to backend README](../backend/README.md)
