# Agent instructions

This is a FastAPI + SQLModel async backend. Apps are Django-inspired. Layers are strict: **router → service → repository**. There is no `crud.py`.

CRUD copy-target (harness, not a running app): `.agents/examples/subapp/` (includes optional `tasks.py`). Copy it to `backend/src/apps/<app>/<subapp>/` and rename `example` / `items` / `Item`. Rename or drop the placeholder `ItemRelationshipBase`. Live runtime for users, auth, and hashing: `backend/src/apps/system/users/`. Sample apps such as `blog` may be absent in this clone — do not use them as a source.

When the task matches, read the skill:

- [create-subapp](.agents/skills/create-subapp/SKILL.md) — new `apps/<app>/<subapp>/`
- [sqlmodel](.agents/skills/sqlmodel/SKILL.md) — `models.py`, `schemas.py`, `repositories.py`
- [fastapi](.agents/skills/fastapi/SKILL.md) — `routers/v1.py`, `deps.py`, `services.py`
- [celery](.agents/skills/celery/SKILL.md) — `tasks.py`, worker `include`
- [alembic](.agents/skills/alembic/SKILL.md) — `core/db/__init__.py` + migrations
- [write-tests](.agents/skills/write-tests/SKILL.md) — `tests/test_v1.py`
- [locust](.agents/skills/locust/SKILL.md) — load tests in `locust/`

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

Shared infrastructure is `backend/src/core/` (config, session, exceptions, mixins, `RepositoryBase`, API mount). Domain code stays in `apps/`.

## Layers

- **Router:** HTTP only. `Depends` + `await service.method(...)`. Never import repositories.
- **Service:** business rules, authz, hashing, cache invalidation, Celery triggers, HTTP exceptions.
- **Repository:** data access via `RepositoryBase[...]`. Keep it thin; add custom SQL only when `get` / `get_multi` / `create` / `update` / `delete` / `db_delete` are not enough. Canonical custom queries for related data: `get_single_with_main_relations` / `get_multi_with_main_relations` (see `.agents/examples/subapp/repositories.py`).

Raise domain errors in the service (`NotFoundException`, `ForbiddenException`, `DuplicateValueException`, … from `src.core.exceptions.http_exceptions`).

## Conventions

- Table name: `{app}_{resource}` (`example_item`, `system_users`). One `table=True` class per `models.py`; a second table means a second subapp.
- Many-to-many: subapp `<a>_<b>_assoc`, table `{app}_{a}_{b}_assoc`. Composed PK in a `*RelationshipBase`. No `UUIDMixin` / `TimestampMixin` / `SoftDeleteMixin` / `UserTrackingMixin`. No HTTP surface (`models.py`, `schemas.py`, `repositories.py`, `services.py` only).
- Imports at the top of each Python file, in three blocks with a blank line between them: `# Built-in Dependencies`, `# Third-Party Dependencies`, `# Local Dependencies`.
- Models: small `*Base` classes composed into one `table=True` class with `UUIDMixin`, `TimestampMixin`, `SoftDeleteMixin`, `UserTrackingMixin` as needed (`src.core.common.models`). List those bases in **reverse** of the desired column order (Alembic `--autogenerate` inverts them). Columns with `foreign_key=` go in a separate `*RelationshipBase`, never mixed into domain `*Base` classes. Exception: `UserTrackingMixin` carries `foreign_key=` itself. Details: [sqlmodel](.agents/skills/sqlmodel/SKILL.md).
- The CRUD example includes tracking. To copy a resource without it, follow [.agents/examples/README.md](.agents/examples/README.md) (Resource without user tracking).
- Schemas reuse those `*Base` classes. Typical set: `XRead`, `XCreate` (`extra="forbid"`), `XCreateInternal`, `XUpdate` with `@optional()` from `src._overrides.pydantic.optional`, `XUpdateInternal`, `XDelete`.
- Endpoints: `write_*`, `read_*`, `patch_*`, `erase_*` (soft delete), `erase_db_*` (hard delete, superuser, path suffix `/db`).
- Deps: `get_<entity>_service`, `<entity>_filters`, `<entity>_sort_order`.
- Singletons: `user_repository`, `user_service` (module-level).
- Auth: `get_current_user` / `get_current_superuser` / `get_optional_user` / `async_get_user_context_db` from `src.apps.system.auth.deps`. DB session: `async_get_db` (public GETs, hard delete) or `async_get_user_context_db` (authenticated writes that stamp `updated_by_user_id`). `async_get_user_context_db` already authenticates — do not also inject `Depends(get_current_user)` on the same handler; read `getattr(db, "current_user", {})`.
- OpenAPI tags: `"System - Users"`, `"System - Auth"`, `"Example - Items"`.
- Paths include the app prefix on the route itself (`/example/items/...`), not on the subapp `APIRouter`.

## Registration checklist (new resource)

1. Include the router in `backend/src/core/api/v1.py`.
2. Import the `table=True` model in `backend/src/core/db/__init__.py` (required for Alembic autogenerate).
3. If Celery: add the module string to `include=[...]` in `backend/src/worker.py`.
4. If seed: add a command under `_management/commands/` and hook it in `backend/src/apps/_management/commands/seed.py`.
5. Generate and apply a migration from `backend/` ([Database Migration Guide](docs/database-migration-guide.md)).
6. Add `tests/test_v1.py` next to the subapp.

Do not register `.agents/examples/subapp/` itself.

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
