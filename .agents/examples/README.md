# Harness examples

These files are **templates for coding agents**, not a running app.

- Do not import them from `backend/`.
- Do not register the router in `core/api/v1.py`.
- Do not import the model in `core/db/__init__.py`.
- Do not add them to pytest, Alembic, Celery `include`, or Locust `locustfile.py`.
- `subapp/tasks.py` is a mold: copy it into `apps/` only if you need background work, then register `src.apps.<app>.<subapp>.tasks` in `worker.py`.

Copy [subapp/](subapp/) to `backend/src/apps/<app>/<subapp>/`, then rename `example` / `items` / `Item` to the real resource. If anything here conflicts with [AGENTS.md](../../AGENTS.md), follow `AGENTS.md`.

Live runtime to copy for auth and hashing: `backend/src/apps/system/users/`.
