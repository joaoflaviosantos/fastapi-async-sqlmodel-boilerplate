---
name: create-subapp
description: Scaffold a new Django-inspired subapp (models, schemas, repositories, services, deps, routers/v1, tests) and register it. Use when adding a resource such as blog/comments, billing/invoices, or a new apps/<app>/<subapp>/ folder.
---

# Create a subapp

Copy `backend/src/apps/blog/posts/` (CRUD) or `backend/src/apps/system/users/` (users + Celery). Do not invent `crud.py` or `app/api/v1/endpoints/`.

For layer details use: `sqlmodel-backend`, `fastapi-backend`, `celery-backend`, `alembic-backend`, `write-subapp-tests`.

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
4. Seed (if any): hook in `backend/src/apps/_management/commands/seed.py`.
5. From `backend/`: `poetry run alembic revision --autogenerate -m "..."` then `poetry run alembic upgrade head`.
6. Tests in `tests/test_v1.py` using fixture `client`.

## 5. Done when

- Router never imports a repository.
- Autogenerate sees the new table (model imported in `core/db/__init__.py`).
- `GET/POST/PATCH/DELETE` match the posts/users style, including soft delete vs `/db` hard delete when applicable.
