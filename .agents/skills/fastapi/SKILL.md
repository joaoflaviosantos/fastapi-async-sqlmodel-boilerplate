---
name: fastapi
description: Create or change routers/v1.py, deps.py, and services.py. Use when adding HTTP endpoints, FastAPI Depends, filters, sort, cache, or service-layer authz. Routers must not call repositories.
---

# Routers, deps, services

Follow `AGENTS.md`. This skill is the recipe for `routers/v1.py`, `deps.py`, and `services.py`.

CRUD template: `.agents/examples/subapp/routers/v1.py`, `deps.py`, `services.py`. Live auth/users: `backend/src/apps/system/users/routers/v1.py`, `src.apps.system.auth.deps`. Session: `src.core.db.session.async_get_db`. Authenticated writes that stamp `updated_by_user_id`: `async_get_user_context_db` from `src.apps.system.auth.deps`.

## Service

- Constructor takes the resource repository; module-level singleton at the bottom of the file. Do not inject `user_repository` unless the resource is actually about users.
- Methods are async. Raise `NotFoundException`, `ForbiddenException`, `DuplicateValueException`, `InternalErrorException` from `src.core.exceptions.http_exceptions`.
- Build `XCreateInternal` in the service (IDs, hashes, `created_by_user_id` / `updated_by_user_id` from `current_user["id"]`), then `repo.create`. Re-read with `get` + `schema_to_select=XRead` (join is for GET responses, not for create).
- List/detail GETs call `get_multi_with_main_relations` / `get_single_with_main_relations`.
- Pagination: `compute_offset` + `paginated_response` from `src.core.utils.api_params`.

```python
class ItemService:
    def __init__(self, item_repo: ItemRepository):
        self.item_repo = item_repo

item_service = ItemService(item_repository)
```

## Deps

```python
async def get_item_service() -> ItemService:
    return item_service

def item_filters(...) -> dict:
    # Query params → dict, drop Nones

def item_sort_order(sort_by: Optional[List[str]] = Query(None)) -> List[Tuple[str, str]] | None:
    return parse_sort_order(sort_by=sort_by, allowed_sort_fields=[...]) or None
```

## Router

- `APIRouter(tags=["Example - Items"])` — no path prefix on the router.
- Put the app prefix on each path: `/example/items/...` (rename to `/billing/invoices/...`).
- Names: `write_*`, `read_*`, `patch_*`, `erase_*`, `erase_db_*`.
- Writes (`write_*`, `patch_*`, `erase_*`): `db: Annotated[AsyncSession, Depends(async_get_user_context_db)]` — that dependency already authenticates. Do **not** also inject `Depends(get_current_user)`. Read the author with `current_user = getattr(db, "current_user", {})` when the service needs the dict. Superuser-only routes use `dependencies=[Depends(get_current_superuser)]`.
- Public GETs and hard delete (`erase_db_*`) keep `async_get_db`.
- Inject `Depends(get_*_service)`.
- Soft delete on `DELETE ...`; hard delete on `DELETE .../db` for superuser only.
- Optional `@cache(...)` from `src.core.utils.cache`. Two namespaces: item `key_prefix="example:item"` + `resource_id_name="item_id"`; list `key_prefix="example:items:...:page"` + `resource_id_name="page"` (the decorator requires a `resource_id`; the list route has no path id, so `page` is the stand-in). On PATCH/DELETE invalidate with `pattern_to_invalidate_extra=["example:items:*"]`. Do not invent prefixes.

```python
@router.post("/example/items", response_model=ItemRead, status_code=201)
async def write_item(
    ...,
    db: Annotated[AsyncSession, Depends(async_get_user_context_db)],
    item_service: ItemService = Depends(get_item_service),
) -> ItemRead:
    current_user = getattr(db, "current_user", {})
    return await item_service.create_item(db=db, item=item, current_user=current_user)
```

Register the router in `backend/src/core/api/v1.py`. Do not register the example tree itself.

To drop tracking (session dep + join GETs), follow `.agents/examples/README.md` (Resource without user tracking).

## Do not

- Import repositories in the router.
- Put SQL or authz in the router (authz belongs in the service).
- Use a `crud_*` module.
