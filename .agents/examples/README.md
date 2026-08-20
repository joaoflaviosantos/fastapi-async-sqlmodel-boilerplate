# Harness examples

These files are **templates for coding agents**, not a running app.

- Do not import them from `backend/`.
- Do not register the router in `core/api/v1.py`.
- Do not import the model in `core/db/__init__.py`.
- Do not add them to pytest, Alembic, Celery `include`, or Locust `locustfile.py`.
- `subapp/tasks.py` is a mold: copy it into `apps/` only if you need background work, then register `src.apps.<app>.<subapp>.tasks` in `worker.py`.

Copy [subapp/](subapp/) to `backend/src/apps/<app>/<subapp>/`, then rename `example` / `items` / `Item` to the real resource. If anything here conflicts with [AGENTS.md](../../AGENTS.md), follow `AGENTS.md`.

Live runtime to copy for auth and hashing: `backend/src/apps/system/users/`.

## Copy: rename the placeholder FK

`ItemRelationshipBase.relation_example_id` points at `example_relation.id`, a table that **does not exist**. Rename that field and `foreign_key=` to a real table, or delete `ItemRelationshipBase` entirely. Leaving it as-is will fail Alembic autogenerate.

## Resource without user tracking

The example ships with `UserTrackingMixin` and join queries. To copy a resource that does not need audit fields, subtract these five pieces — nothing else:

1. `models.py` — remove `UserTrackingMixin` from the `Item` base list.
2. `schemas.py` — remove the three `updated_by_user_*` fields from `ItemRead`. Change `ItemCreateInternal(ItemCreate, UserTrackingMixin)` to `ItemCreateInternal(ItemCreate)`.
3. `repositories.py` — delete the `ItemRepository` class body and restore the alias `ItemRepository = RepositoryBase[Item, ItemCreateInternal, ItemUpdate, ItemUpdateInternal, ItemDelete]`.
4. `services.py` — replace `get_multi_with_main_relations` / `get_single_with_main_relations` with `get_multi` / `get` using `schema_to_select=ItemRead`. Remove the two lines that set `created_by_user_id` / `updated_by_user_id` in `create_item`.
5. `routers/v1.py` — switch `write_item`, `patch_item`, and `erase_item` from `async_get_user_context_db` back to `async_get_db`.

## Seeds

Do not hook these into `backend/src/apps/_management/commands/seed.py` until you have copied them into `apps/`.

- **One row:** [subapp/_management/commands/create_first_item.py](subapp/_management/commands/create_first_item.py) — `one_or_none()` on a unique payload, add if missing.
- **Catalog / N rows:** [subapp/_management/commands/create_example_items.py](subapp/_management/commands/create_example_items.py) — one `SELECT` of titles, add only missing rows, one `commit`. Do not query per item in a loop.
