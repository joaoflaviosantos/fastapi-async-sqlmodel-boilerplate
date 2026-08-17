---
name: fastapi
description: Create or change routers/v1.py, deps.py, and services.py. Use when adding HTTP endpoints, FastAPI Depends, filters, sort, cache, or service-layer authz. Routers must not call repositories.
---

# Routers, deps, services

Reference: `backend/src/apps/blog/posts/routers/v1.py`, `deps.py`, `services.py`. Auth: `src.apps.system.auth.deps`. Session: `src.core.db.session.async_get_db`.

## Service

- Constructor takes repositories; module-level singleton at the bottom of the file.
- Methods are async. Raise `NotFoundException`, `ForbiddenException`, `DuplicateValueException`, `InternalErrorException` from `src.core.exceptions.http_exceptions`.
- Build `XCreateInternal` in the service (IDs, hashes), then `repo.create`.
- Pagination: `compute_offset` + `paginated_response` from `src.core.utils.api_params`.

```python
class PostService:
    def __init__(self, post_repo: PostRepository, user_repo: UserRepository):
        self.post_repo = post_repo
        self.user_repo = user_repo

post_service = PostService(post_repository, user_repository)
```

## Deps

```python
async def get_post_service() -> PostService:
    return post_service

def post_filters(...) -> dict:
    # Query params → dict, drop Nones

def post_sort_order(sort_by: Optional[List[str]] = Query(None)) -> List[Tuple[str, str]] | None:
    return parse_sort_order(sort_by=sort_by, allowed_sort_fields=[...]) or None
```

## Router

- `APIRouter(tags=["Blog - Posts"])` — no path prefix on the router.
- Put the app prefix on each path: `/blog/posts/...`.
- Names: `write_*`, `read_*`, `patch_*`, `erase_*`, `erase_db_*`.
- Inject `Depends(get_current_user)` or `dependencies=[Depends(get_current_superuser)]`.
- Inject `db: Annotated[AsyncSession, Depends(async_get_db)]` and `Depends(get_*_service)`.
- Soft delete on `DELETE ...`; hard delete on `DELETE .../db` for superuser only.
- Optional `@cache(...)` from `src.core.utils.cache` (see posts). Invalidate on write.

```python
@router.post("/blog/posts/user/{user_id}", response_model=PostRead, status_code=201)
async def write_post(..., post_service: PostService = Depends(get_post_service)) -> PostRead:
    return await post_service.create_post(...)
```

Register the router in `backend/src/core/api/v1.py`.

## Do not

- Import repositories in the router.
- Put SQL or authz in the router (authz belongs in the service).
- Use a `crud_*` module.
