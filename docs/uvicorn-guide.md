# Uvicorn Guide

[Uvicorn](https://www.uvicorn.org/) is the **ASGI server** that runs this FastAPI app. It is what actually handles HTTP inside the Python process.

How it is started depends on the mode:

| Mode | Process | Reload |
| ---- | ------- | ------ |
| Local (CLI / Poetry) | Uvicorn | yes (when `WEB_CONCURRENCY=1`) |
| Compose (full-stack / app-only) | Uvicorn in the container | no |
| Native VPS (`deploy/native`) | Gunicorn + `UvicornWorker` behind Nginx | no |

Gunicorn is **not** used in local or Compose. It is the process manager for native deploy only.

VPS install steps live in the [Deployment Guide](deploy-guide.md) and [deploy/native/README.md](../deploy/native/README.md). This page is which server speaks HTTP.

## Local development

From `backend/`:

```bash
poetry run uvicorn src.main:app --reload
```

`--reload` watches Python files and restarts the process. That is for development only: a file watcher, a single process, and no graceful worker restarts.

The root CLI (`python setup.py` → Local Development) does the same when `WEB_CONCURRENCY` is `1` (the default in `backend/.env.example`), plus `--host 0.0.0.0 --port 8000`. If `WEB_CONCURRENCY` is greater than `1`, the CLI starts Uvicorn with `--workers` and **without** `--reload`.

## Compose

Production Compose files run **one** Uvicorn process in the API container, for example:

```text
uvicorn src.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips="*"
```

No `--reload`. Caddy (full-stack) or the PaaS (app-only) sits in front. Docker/Compose already restarts a dead container, so this repo does not put Gunicorn inside those images.

`--proxy-headers` and `--forwarded-allow-ips` matter when a reverse proxy forwards `X-Forwarded-For`. Rate limiting: [Rate Limit Guide](rate-limit-guide.md).

## Native: Gunicorn + UvicornWorker

[deploy/native](../deploy/native/) is a Linux VPS **without Docker**: Supervisor keeps processes up, Nginx is the reverse proxy.

Traffic path:

```text
client → Nginx → unix socket (backend/gunicorn.sock) → Gunicorn → UvicornWorker → FastAPI
```

Supervisor runs [deploy/native/scripts/backend-api](../deploy/native/scripts/backend-api), which `exec`s:

```bash
gunicorn src.main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind unix:.../backend/gunicorn.sock \
  --forwarded-allow-ips '*' \
  --workers 1
```

Nginx ([deploy/native/nginx/nginx.conf](../deploy/native/nginx/nginx.conf)) proxies to that socket. The Python process never binds a public TCP port.

### Why this is the robust native default

- **Gunicorn** manages worker processes: bind a Unix socket, drop privileges (`--user` / `--group`), enforce `--timeout`, and replace a worker that dies. A lone `uvicorn --reload` does none of that.
- **`uvicorn.workers.UvicornWorker`** keeps an ASGI event loop **per worker**. Gunicorn’s default sync workers would block FastAPI’s async paths (DB, Redis, HTTP).
- **Nginx in front of the socket** absorbs slow clients, sets forwarded headers, and can terminate TLS. The app process stays on the private socket.
- Compose/PaaS already supervise a container, so they run Uvicorn directly. Native has no orchestrator for the Python process — **Supervisor + Gunicorn** fills that gap.

`gunicorn` is a runtime dependency in `backend/pyproject.toml`.

The script hardcodes `WORKERS=1`. It does **not** read `WEB_CONCURRENCY` from `.env`. Raise `WORKERS` in the script when you want more native processes, and keep `.env` in sync (below).

## `WEB_CONCURRENCY`

`WEB_CONCURRENCY` (default `1`) is used in two places:

1. **Local CLI** — `1` → Uvicorn `--reload`; `> 1` → Uvicorn `--workers N` (no reload).
2. **Database pool** — [backend/src/core/db/session.py](../backend/src/core/db/session.py) splits `POSTGRES_POOL_SIZE` across this many processes so each worker does not open a full pool.

On native deploy, if you increase `WORKERS` in `backend-api`, set `WEB_CONCURRENCY` in `backend/.env` to the **same number**. Otherwise the pool math assumes one process and you can exhaust Postgres connections. Leaving both at `1` is the safe default.

## Further reading

- [Deployment Guide](deploy-guide.md) — Compose vs native vs PaaS
- [deploy/native/README.md](../deploy/native/README.md) — Supervisor, Nginx, scripts
- [Uvicorn documentation](https://www.uvicorn.org/)

---

[Back to backend README](../backend/README.md)
