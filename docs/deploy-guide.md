# Deployment Guide

This guide describes all available deployment modes for the project. Choose the one that best fits your infrastructure.

For local development setup, see the [Development Guide](development-guide.md).

---

## Overview

```
deploy/
├── compose/
│   ├── full-stack/     → Complete stack on a single VPS (Docker + Caddy HTTPS)
│   └── app-only/       → Application only (external databases, PaaS platforms)
└── native/             → Linux VPS without Docker (Nginx + Supervisor)
```

| Mode | Best For | Docker | HTTPS | DB Included |
|------|----------|--------|-------|-------------|
| [compose/full-stack](#-composefull-stack) | Single VPS, full control | ✅ | ✅ Caddy | ✅ |
| [compose/app-only](#-composeapp-only) | PaaS, managed databases | ✅ | ❌ (platform) | ❌ |
| [native](#-native) | Linux VPS, no Docker | ❌ | ❌ Nginx (manual) | ❌ |

---

## 🐳 compose/full-stack

> Full documentation: [deploy/compose/full-stack/README.md](../deploy/compose/full-stack/README.md)

**When to use:** You want to run the entire stack (databases, API, workers, reverse proxy, TLS) on a **single VPS** with a single `docker compose up` command.

**What's included:**

| Service | Description |
|---|---|
| `caddy` | Reverse proxy with automatic Let's Encrypt HTTPS |
| `postgres` | PostgreSQL 17 with pgvector (internal network only) |
| `redis` | Redis Alpine (internal network only) |
| `migrate` | Runs `alembic upgrade head` once before API starts |
| `api` | FastAPI via Uvicorn |
| `celery_worker` | Celery Worker |
| `celery_beat` | Celery Beat scheduler |
| `celery_flower` | Flower UI (basic auth required, internal) |

**Key features:**
- PostgreSQL and Redis are **not** exposed to the host (no port binding).
- Healthchecks on Postgres and Redis prevent the API from starting before the databases are ready.
- Caddy automatically provisions TLS certificates. Edit `deploy/compose/full-stack/Caddyfile` with your domain to enable HTTPS.

**Prerequisites:**
1. Docker and Docker Compose on the server.
2. `backend/.env` configured from `backend/.env.example`.
3. Ports `80` and `443` open in the firewall.
4. DNS A record pointing to the server's IP.

**Run (from repository root):**

Start main stack (Postgres, Redis, API, Caddy):
```bash
docker compose --env-file backend/.env \
  -f deploy/compose/full-stack/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-boilerplate-prod up -d
```

Run migration:
```bash
docker compose --env-file backend/.env \
  -f deploy/compose/full-stack/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-boilerplate-prod \
  --profile migrate run --rm migrate
```

Start Celery Worker:
```bash
docker compose --env-file backend/.env \
  -f deploy/compose/full-stack/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-boilerplate-prod \
  --profile worker up -d celery_worker
```

Start Celery Beat:
```bash
docker compose --env-file backend/.env \
  -f deploy/compose/full-stack/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-boilerplate-prod \
  --profile scheduler up -d celery_beat
```

Start Flower (Observability):
```bash
docker compose --env-file backend/.env \
  -f deploy/compose/full-stack/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-boilerplate-prod \
  --profile observability up -d celery_flower
```

---

## 🐳 compose/app-only

> Full documentation: [deploy/compose/app-only/README.md](../deploy/compose/app-only/README.md)

**When to use:** Your databases are **managed externally** — by a PaaS platform or a cloud service — and you only want to deploy the application containers.

**Compatible with:**
- Self-managed: Dokploy, Coolify, CapRover, Portainer
- Cloud: AWS ECS, Railway, Render, Fly.io
- Managed databases: AWS RDS + ElastiCache, Supabase, Neon, Upstash

**What's included:**

| Service | Description |
|---|---|
| `migrate` | Runs `alembic upgrade head` once, then exits |
| `api` | FastAPI via Uvicorn |
| `celery_worker` | Celery Worker |
| `celery_beat` | Celery Beat scheduler |
| `celery_flower` | Flower UI (basic auth required) |

**Key features:**
- No Postgres, Redis, or reverse proxy containers.
- Uses an external Docker network (`app-network`). Rename it to match your platform if needed (e.g. `dokploy-network`).
- All connection variables must be set in `backend/.env` or the platform's environment UI.

**Run (from repository root):**

Start main API:
```bash
docker compose --env-file backend/.env \
  -f deploy/compose/app-only/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-boilerplate-prod up -d api
```

Run migration:
```bash
docker compose --env-file backend/.env \
  -f deploy/compose/app-only/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-boilerplate-prod \
  --profile migrate run --rm migrate
```

Start Celery Worker:
```bash
docker compose --env-file backend/.env \
  -f deploy/compose/app-only/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-boilerplate-prod \
  --profile worker up -d celery_worker
```

Start Celery Beat:
```bash
docker compose --env-file backend/.env \
  -f deploy/compose/app-only/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-boilerplate-prod \
  --profile scheduler up -d celery_beat
```

Start Flower (Observability):
```bash
docker compose --env-file backend/.env \
  -f deploy/compose/app-only/docker-compose.yml \
  --project-name fastapi-async-sqlmodel-boilerplate-prod \
  --profile observability up -d celery_flower
```

---

## 🖥️ native

> Full documentation: [deploy/native/README.md](../deploy/native/README.md)

**When to use:** You want to deploy on a **Linux VPS without Docker**, using Nginx as the reverse proxy and Supervisor to manage processes.

Based on: [FastAPI with Nginx and Gunicorn](https://dylancastillo.co/posts/fastapi-nginx-gunicorn.html)

**Directory structure:**

```
deploy/native/
├── logs/           # Log output directory
├── nginx/
│   └── nginx.conf  # Nginx reverse-proxy configuration
├── scripts/        # Bash wrapper scripts for each process
│   ├── backend-api
│   ├── backend-worker
│   └── backend-scheduler
└── supervisor/     # Supervisor program configurations
    ├── backend-api.conf
    ├── backend-worker.conf
    └── backend-scheduler.conf
```

**High-level steps:**

1. Install Nginx, Supervisor, Python 3.11, and Poetry on the server.
2. Clone the repository and run `poetry install` inside `backend/`.
3. Copy `backend/.env.example` → `backend/.env` and fill in production values.
4. Run `alembic upgrade head` to apply migrations.
5. Make the scripts in `deploy/native/scripts/` executable.
6. Symlink Supervisor configs to `/etc/supervisor/conf.d/`.
7. Symlink `deploy/native/nginx/nginx.conf` to `/etc/nginx/sites-enabled/fastapi-app` and remove the default site.

> [!IMPORTANT]
> See the [full native README](../deploy/native/README.md) for the exact commands with paths.

---

## Common: Environment Variables

All deployment modes read from `backend/.env`. This file is never committed to version control.

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your production values
```

Key variables to configure before deploying:

| Variable | Description |
|---|---|
| `SECRET_KEY` | App secret key — generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `POSTGRES_SERVER` | Database host |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Database credentials |
| `REDIS_CACHE_HOST` / `REDIS_CACHE_PASSWORD` | Redis connection |
| `REDIS_BROKER_HOST` / `REDIS_BROKER_PASSWORD` | Celery broker Redis |
| `FLOWER_BASIC_AUTH` | Flower UI auth (`user:password`) |
| `ENVIRONMENT` | Set to `production` for prod deployments |

See [backend/.env.example](../backend/.env.example) for the full list.
