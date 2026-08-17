---
name: create-subapp
description: Scaffold a new Django-inspired subapp (models, schemas, repositories, services, deps, routers/v1, tests) and register it. Use when adding a resource such as blog/comments, billing/invoices, or a new apps/<app>/<subapp>/ folder.
---

# Create a subapp

Follow `AGENTS.md`. This skill is the recipe for scaffolding a new `apps/<app>/<subapp>/`.

Copy `backend/src/apps/blog/posts/` (CRUD) or `backend/src/apps/system/users/` (users + Celery). Do not invent `crud.py` or `app/api/v1/endpoints/`.

**Before generating files**, read the sibling skills: `sqlmodel`, `fastapi`, `write-tests`. Also read `celery` if you need `tasks.py`, and `alembic` before the migration.

## 1. Choose names

- App: `blog`, `system`, `billing`, …
- Subapp (resource): `comments`, `invoices`, …
- Table: `{app}_{resource}` → `blog_comment`
- Import path: `src.apps.<app>.<subapp>.<module>`
- OpenAPI tag: `"Blog - Comments"`

## 2. Create files

```
backend/src/apps/<app>/<subapp>/
  __init__.py
  models.py
  schemas.py
  repositories.py
  services.py
  deps.py
  routers/v1.py
  tests/test_v1.py
```

Add `tasks.py` only if background work is required. Add `_management/commands/` only if a bootstrap seed is required.

Python files use three import blocks: Built-in / Third-Party / Local.

## 3. Implement in order

1. `models.py` — `*Base` field groups + `table=True` class with mixins.
2. `schemas.py` — `XRead`, `XCreate`, `XCreateInternal`, `XUpdate` (`@optional()`), `XUpdateInternal`, `XDelete`.
3. `repositories.py` — `RepositoryBase[...]` + singleton.
4. `services.py` — inject repos, raise HTTP exceptions, module-level singleton.
5. `deps.py` — `get_*_service`, filters, sort.
6. `routers/v1.py` — thin HTTP; `write_*` / `read_*` / `patch_*` / `erase_*`; path includes the app prefix (`/blog/comments/...`).

## 4. Register

1. `backend/src/core/api/v1.py` — import router, `api_v1_router.include_router(...)`.
2. `backend/src/core/db/__init__.py` — import the `table=True` model.
3. Celery (if `tasks.py`): string in `include=[...]` in `backend/src/worker.py`.
4. Seed (if any): see below, then hook in `backend/src/apps/_management/commands/seed.py`.
5. From `backend/`: `poetry run alembic revision --autogenerate -m "..."` then `poetry run alembic upgrade head`.
6. Tests in `tests/test_v1.py` using fixture `client`.

## 5. Optional seed

Only if bootstrap data is required. Copy `backend/src/apps/blog/posts/_management/commands/create_first_post.py`.

- Command lives under `backend/src/apps/<app>/<subapp>/_management/commands/`.
- Open the DB with `local_session()`, never `async_get_db`.
- Be idempotent: `one_or_none()` and skip if the row exists.
- Hook `await create_*.main()` in `backend/src/apps/_management/commands/seed.py`.

## 6. Done when

Verify before considering the subapp finished:

- Router never imports a repository.
- Model imported in `core/db/__init__.py` so autogenerate sees the table.
- Review the new Alembic revision, then `poetry run alembic upgrade head` from `backend/`.
- From `backend/`: `poetry run pytest src/apps/<app>/<subapp>/tests/test_v1.py -v`
- `GET/POST/PATCH/DELETE` match the posts/users style, including soft delete vs `/db` hard delete when applicable.
