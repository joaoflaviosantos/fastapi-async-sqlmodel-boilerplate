---
name: fastapi
description: Create or change routers/v1.py, deps.py, and services.py. Use when adding HTTP endpoints, FastAPI Depends, filters, sort, cache, or service-layer authz. Routers must not call repositories.
---

# Routers, deps, services

Follow `AGENTS.md`. This skill is the recipe for `routers/v1.py`, `deps.py`, and `services.py`.

CRUD template: `.agents/examples/subapp/routers/v1.py`, `deps.py`, `services.py`. Live auth/users: `backend/src/apps/system/users/routers/v1.py`, `src.apps.system.auth.deps`. Session: `src.core.db.session.async_get_db`.

## Service

- Constructor takes repositories; module-level singleton at the bottom of the file.
- Methods are async. Raise `NotFoundException`, `ForbiddenException`, `DuplicateValueException`, `InternalErrorException` from `src.core.exceptions.http_exceptions`.
- Build `XCreateInternal` in the service (IDs, hashes), then `repo.create`.
- Pagination: `compute_offset` + `paginated_response` from `src.core.utils.api_params`.

```python
class ItemService:
    def __init__(self, item_repo: ItemRepository, user_repo: UserRepository):
        self.item_repo = item_repo
        self.user_repo = user_repo

item_service = ItemService(item_repository, user_repository)
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
- Inject `Depends(get_current_user)` or `dependencies=[Depends(get_current_superuser)]`.
- Inject `db: Annotated[AsyncSession, Depends(async_get_db)]` and `Depends(get_*_service)`.
- Soft delete on `DELETE ...`; hard delete on `DELETE .../db` for superuser only.
- Optional `@cache(...)` from `src.core.utils.cache`. On PATCH/DELETE copy the example: `pattern_to_invalidate_extra=["example:items:user:{user_id}:*"]`. Do not invent prefixes.

```python
@router.post("/example/items/user/{user_id}", response_model=ItemRead, status_code=201)
async def write_item(..., item_service: ItemService = Depends(get_item_service)) -> ItemRead:
    return await item_service.create_item(...)
```

Register the router in `backend/src/core/api/v1.py`. Do not register the example tree itself.

## Do not

- Import repositories in the router.
- Put SQL or authz in the router (authz belongs in the service).
- Use a `crud_*` module.
