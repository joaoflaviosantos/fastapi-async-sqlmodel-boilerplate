# Development — Native (No Docker)

Use this when you want to run everything **directly on your host machine** without Docker — the fastest setup for local development with full debugger support.

## Requirements

- Python 3.11+
- [Poetry](https://python-poetry.org/docs/#installation)
- PostgreSQL with pgvector extension
- Redis

> **Tip:** If you don't have Python and Poetry installed, use the helper scripts in `development/native/scripts/`:
> - **Linux**: `bash development/native/scripts/install_python.sh`
> - **Windows**: `development\native\scripts\install_python.bat`

## Quick Start (via `setup.py`)

The fastest way to get started is using the project CLI from the **repository root**:

```bash
python3 setup.py
```

This automates Poetry, `backend/.env` (copy from `.env.example` + `SECRET_KEY`), and process startup. Choose **1 – Local Development**. The Setup wizard appears only when required env values are missing (press ENTER to keep defaults). Equivalent: `python setup.py local`.

## Manual Setup

### 1. Install Python dependencies

```bash
cd backend
poetry install
```

### 2. Configure environment variables

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` and fill in your local database credentials:
- `POSTGRES_SERVER=127.0.0.1`
- `REDIS_CACHE_HOST=127.0.0.1` (Celery broker falls back to cache if `REDIS_BROKER_HOST` is empty)

### 3. Run database migrations

```bash
cd backend
poetry run alembic upgrade head
```

### 4. Start the services

Open separate terminal windows for each process (all commands run from `backend/`):

```bash
# API (terminal 1)
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Celery Worker (terminal 2)
poetry run celery -A src.worker worker --loglevel=info

# Celery Beat / Scheduler (terminal 3)
poetry run celery -A src.worker beat --loglevel=info
```

## Tips

- Use `development/compose/infra-only` to spin up Postgres and Redis in Docker if you don't have them installed locally.
- Use [Honcho](https://honcho.readthedocs.io/) to start all processes in a single terminal if desired.
