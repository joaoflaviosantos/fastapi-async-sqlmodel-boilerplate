# Development — Docker (Infrastructure Only)

Use this when you want to **run only the databases in Docker** while running the API and Celery processes directly on your host machine (e.g. using your IDE's debugger or `uvicorn` from the terminal).

## What's included

| Service    | Description                       |
|------------|-----------------------------------|
| `postgres` | pgvector/pgvector (PostgreSQL 17) |
| `redis`    | Redis Alpine                      |

## How to run

### 1. Start the infrastructure

From the **repository root**:

```bash
docker compose --env-file backend/.env -f development/compose/infra-only/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-boilerplate up -d
```

### 2. Run the backend

**Option A — Quick start via `setup.py` (recommended):**

```bash
python3 setup.py
```

**Option B — Manual (from `backend/`):**

```bash
cd backend

# Run migrations
poetry run alembic upgrade head

# Start the API
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# In another terminal — start the Celery worker
poetry run celery -A src.worker worker --loglevel=info

# In another terminal — start the Celery beat scheduler
poetry run celery -A src.worker beat --loglevel=info
```

## Notes

- Postgres is exposed on the host at `localhost:5432` (or `$POSTGRES_PORT` if set in your shell).
- Redis is exposed on the host at `localhost:6379` with the password set in `REDIS_CACHE_PASSWORD` from your `backend/.env`.
- Make sure your `backend/.env` has `POSTGRES_SERVER=localhost` and `REDIS_*_HOST=localhost`.
