---
name: create-subapp
description: Scaffold a new Django-inspired subapp (models, schemas, repositories, services, deps, routers/v1, tests) and register it. Use when adding a resource such as billing/invoices, catalog/products, or a new apps/<app>/<subapp>/ folder.
---

# Create a subapp

Follow `AGENTS.md`. This skill is the recipe for scaffolding a new `apps/<app>/<subapp>/`.

Copy `.agents/examples/subapp/` to `backend/src/apps/<app>/<subapp>/` and rename `example` / `items` / `Item`. Rename or drop `ItemRelationshipBase` (`relation_example_id` → `example_relation.id` is a placeholder). Do not invent `crud.py` or `app/api/v1/endpoints/`. Copy `backend/src/apps/system/users/` only when the resource is users-like (auth, hashing). For Celery, copy `tasks.py` from the example. Sample apps such as `blog` may be absent — do not use them as a source.

If the resource does not need user tracking, subtract it after the copy: `.agents/examples/README.md` (Resource without user tracking).

**Before generating files**, read the sibling skills: `sqlmodel`, `fastapi`, `write-tests`. Also read `celery` if you need `tasks.py`, and `alembic` before the migration.

## 1. Choose names

- App: `system`, `billing`, `catalog`, …
- Subapp (resource): `invoices`, `products`, …
- Table: `{app}_{resource}` → `billing_invoice`
- Import path: `src.apps.<app>.<subapp>.<module>`
- OpenAPI tag: `"Billing - Invoices"`

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

Add `tasks.py` only if background work is required (copy `.agents/examples/subapp/tasks.py`). Add `_management/commands/` only if a bootstrap seed is required.

Python files use three import blocks: Built-in / Third-Party / Local.

### Association subapp (`_assoc`)

Many-to-many tables are their own subapp named `<a>_<b>_assoc`. Slim tree only:

```
backend/src/apps/<app>/<a>_<b>_assoc/
  __init__.py
  models.py
  schemas.py
  repositories.py
  services.py
```

No `routers/`, `deps.py`, or `tests/`. Register the `table=True` model in `core/db/__init__.py`. Do not include a router. Other services and tasks call this repository. Schema/model pattern: [sqlmodel](../sqlmodel/SKILL.md) (Many-to-many).

## 3. Implement in order

1. `models.py` — `*Base` field groups + `table=True` class with mixins.
2. `schemas.py` — `XRead`, `XCreate`, `XCreateInternal`, `XUpdate` (`@optional()`), `XUpdateInternal`, `XDelete`.
3. `repositories.py` — thin `RepositoryBase[...]` alias, or a subclass with `get_single_with_main_relations` / `get_multi_with_main_relations` when the GET payload includes related data.
4. `services.py` — inject repos, raise HTTP exceptions, module-level singleton.
5. `deps.py` — `get_*_service`, filters, sort.
6. `routers/v1.py` — thin HTTP; `write_*` / `read_*` / `patch_*` / `erase_*`; path includes the app prefix (`/billing/invoices/...`).

## 4. Register

1. `backend/src/core/api/v1.py` — import router, `api_v1_router.include_router(...)`.
2. `backend/src/core/db/__init__.py` — import the `table=True` model.
3. Celery (if `tasks.py`): string in `include=[...]` in `backend/src/worker.py`.
4. Seed (if any): see below, then hook in `backend/src/apps/_management/commands/seed.py`.
5. From `backend/`: `poetry run alembic revision --autogenerate -m "..."` then `poetry run alembic upgrade head`.
6. Tests in `tests/test_v1.py` using fixture `client`.

Do not register `.agents/examples/subapp/` itself.

## 5. Optional seed

Only if bootstrap data is required. Copy `.agents/examples/subapp/_management/commands/create_first_item.py`.

- Command lives under `backend/src/apps/<app>/<subapp>/_management/commands/`.
- Open the DB with `local_session()`, never `async_get_db`.
- Be idempotent: `one_or_none()` and skip if the row exists.
- Tracking IDs on bootstrap rows use `settings.USER_SYSTEM_ID` (system actor), not the first admin.
- Hook `await create_*.main()` in `backend/src/apps/_management/commands/seed.py`.

## 6. Done when

Verify before considering the subapp finished:

- Router never imports a repository.
- Model imported in `core/db/__init__.py` so autogenerate sees the table.
- Review the new Alembic revision, then `poetry run alembic upgrade head` from `backend/`.
- From `backend/`: `poetry run pytest src/apps/<app>/<subapp>/tests/test_v1.py -v`
- `GET/POST/PATCH/DELETE` match `.agents/examples/subapp/`, including soft delete vs `/db` hard delete when applicable.
- If Celery: `tasks.py` copied from the example and the module string is in `worker.py` `include`.
