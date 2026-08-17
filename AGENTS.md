# Agent instructions

This is a FastAPI + SQLModel async backend. Apps are Django-inspired. Layers are strict: **router → service → repository**. There is no `crud.py`.

Canonical examples: `backend/src/apps/blog/posts/` (full CRUD) and `backend/src/apps/system/users/` (users + Celery). Copy those instead of inventing a new layout.

When the task matches, read the skill:

- [create-subapp](.agents/skills/create-subapp/SKILL.md) — new `apps/<app>/<subapp>/`
- [sqlmodel-backend](.agents/skills/sqlmodel-backend/SKILL.md) — `models.py`, `schemas.py`, `repositories.py`
- [fastapi-backend](.agents/skills/fastapi-backend/SKILL.md) — `routers/v1.py`, `deps.py`, `services.py`
- [celery-backend](.agents/skills/celery-backend/SKILL.md) — `tasks.py`, worker `include`
- [alembic-backend](.agents/skills/alembic-backend/SKILL.md) — `core/db/__init__.py` + migrations
- [write-subapp-tests](.agents/skills/write-subapp-tests/SKILL.md) — `tests/test_v1.py`

Human setup and extra-skill CLI notes: [Coding Agents](docs/ai-coding-guide.md).

## Layout

```
backend/src/apps/<app>/<subapp>/
  models.py
  schemas.py
  repositories.py
  services.py
  deps.py
  routers/v1.py
  tests/test_v1.py
  tasks.py                    # only if Celery is needed
  _management/commands/       # only if a seed is needed
```

`auth` is a top-level app without a subfolder (`backend/src/apps/auth/`). Routes still live under `/api/v1/system/auth/...`.

Shared infrastructure is `backend/src/core/` (config, session, exceptions, mixins, `RepositoryBase`, API mount). Domain code stays in `apps/`.

## Layers

- **Router:** HTTP only. `Depends` + `await service.method(...)`. Never import repositories.
- **Service:** business rules, authz, hashing, cache invalidation, Celery triggers, HTTP exceptions.
- **Repository:** data access via `RepositoryBase[...]`. Keep it thin; add custom SQL only when `get` / `get_multi` / `create` / `update` / `delete` / `db_delete` are not enough.

Raise domain errors in the service (`NotFoundException`, `ForbiddenException`, `DuplicateValueException`, … from `src.core.exceptions.http_exceptions`).

## Conventions

- Table name: `{app}_{resource}` (`blog_post`, `system_users`).
- Imports at the top of each Python file, in three blocks with a blank line between them: `# Built-in Dependencies`, `# Third-Party Dependencies`, `# Local Dependencies`.
- Models: small `*Base` classes composed into one `table=True` class with `UUIDMixin`, `TimestampMixin`, `SoftDeleteMixin` as needed (`src.core.common.models`). List those bases in **reverse** of the desired column order (Alembic `--autogenerate` inverts them). Columns with `foreign_key=` go in a separate `*RelationshipBase`, never mixed into domain `*Base` classes. Details: [sqlmodel-backend](.agents/skills/sqlmodel-backend/SKILL.md).
- Schemas reuse those `*Base` classes. Typical set: `XRead`, `XCreate` (`extra="forbid"`), `XCreateInternal`, `XUpdate` with `@optional()` from `src._overrides.pydantic.optional`, `XUpdateInternal`, `XDelete`.
- Endpoints: `write_*`, `read_*`, `patch_*`, `erase_*` (soft delete), `erase_db_*` (hard delete, superuser, path suffix `/db`).
- Deps: `get_<entity>_service`, `<entity>_filters`, `<entity>_sort_order`.
- Singletons: `user_repository`, `user_service` (module-level).
- Auth: `get_current_user` / `get_current_superuser` / `get_optional_user` from `src.apps.auth.deps`. DB session: `async_get_db`.
- OpenAPI tags: `"System - Users"`, `"Blog - Posts"`, `"Authentication"`.
- Paths include the app prefix on the route itself (`/blog/posts/...`), not on the subapp `APIRouter`.

## Registration checklist (new resource)

1. Include the router in `backend/src/core/api/v1.py`.
2. Import the `table=True` model in `backend/src/core/db/__init__.py` (required for Alembic autogenerate).
3. If Celery: add the module string to `include=[...]` in `backend/src/worker.py`.
4. If seed: add a command under `_management/commands/` and hook it in `backend/src/apps/_management/commands/seed.py`.
5. Generate and apply a migration from `backend/` ([Database Migration Guide](docs/database-migration-guide.md)).
6. Add `tests/test_v1.py` next to the subapp.

## Commands (from `backend/`)

```bash
poetry run pytest -v
poetry run alembic revision --autogenerate -m "description"
poetry run alembic upgrade head
```

Do not permanently mutate core seed data in tests (default tier, first admin, etc.).

## Do not

- Do not add `crud.py` or call repositories from routers.
- Do not skip the model import in `core/db/__init__.py`.
- Do not use `async_get_db` inside Celery tasks; use `local_session()`.
- Do not invent `app/api/v1/endpoints/` or a flat `models/` / `services/` tree at the project root.
