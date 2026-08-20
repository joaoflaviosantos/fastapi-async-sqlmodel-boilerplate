# Built-in Dependencies
from typing import Annotated, Dict, Optional, List, Tuple
from uuid import UUID

# Third-Party Dependencies
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Request, Depends
import fastapi

# Local Dependencies
from src.apps.system.auth.deps import get_current_user, get_current_superuser
from src.apps.system.rate_limits.deps import rate_limiter
from src.apps.blog.tags.deps import get_tag_service, tag_filters, tag_sort_order
from src.apps.blog.tags.services import TagService
from src.core.db.session import async_get_db
from src.core.utils.cache import cache
from src.apps.blog.tags.schemas import TagCreate, TagUpdate, TagRead
from src.core.common.schemas import PaginatedListResponse

router = fastapi.APIRouter(tags=["Blog - Tags"])


@router.post(
    "/blog/tags",
    response_model=TagRead,
    status_code=201,
    dependencies=[Depends(rate_limiter)],
)
@cache(
    key_prefix="blog:tag",
    pattern_to_invalidate_extra=["blog:tags:*"],
)
async def write_tag(
    request: Request,
    tag: TagCreate,
    _current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    tag_service: TagService = Depends(get_tag_service),
) -> TagRead:
    return await tag_service.create_tag(db=db, tag=tag)


@router.get(
    "/blog/tags",
    response_model=PaginatedListResponse[TagRead],
    dependencies=[Depends(rate_limiter)],
)
@cache(
    key_prefix="blog:tags:items_per_page_{items_per_page}:filters_{filters}:sort_by_{sort_by}:page",
    resource_id_name="page",
    expiration=60,
)
async def read_tags(
    request: Request,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    tag_service: TagService = Depends(get_tag_service),
    filters: dict = Depends(tag_filters),
    sort_by: Optional[List[Tuple[str, str]]] = Depends(tag_sort_order),
    page: int = 1,
    items_per_page: int = 10,
) -> dict:
    return await tag_service.get_tags(
        db=db,
        page=page,
        items_per_page=items_per_page,
        filters=filters,
        sort_by=sort_by,
    )


@router.get(
    "/blog/tags/{tag_id}",
    response_model=TagRead,
    dependencies=[Depends(rate_limiter)],
)
@cache(key_prefix="blog:tag", resource_id_name="tag_id")
async def read_tag(
    request: Request,
    tag_id: UUID,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    tag_service: TagService = Depends(get_tag_service),
) -> dict:
    return await tag_service.get_tag(db=db, tag_id=tag_id)


@router.patch(
    "/blog/tags/{tag_id}",
    dependencies=[Depends(rate_limiter)],
)
@cache(
    key_prefix="blog:tag",
    resource_id_name="tag_id",
    pattern_to_invalidate_extra=["blog:tags:*", "blog:posts:*", "blog:post:*"],
)
async def patch_tag(
    request: Request,
    tag_id: UUID,
    values: TagUpdate,
    _current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    tag_service: TagService = Depends(get_tag_service),
) -> Dict[str, str]:
    return await tag_service.update_tag(db=db, tag_id=tag_id, values=values)


@router.delete(
    "/blog/tags/{tag_id}",
    dependencies=[Depends(rate_limiter)],
)
@cache(
    key_prefix="blog:tag",
    resource_id_name="tag_id",
    pattern_to_invalidate_extra=["blog:tags:*"],
)
async def erase_tag(
    request: Request,
    tag_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    tag_service: TagService = Depends(get_tag_service),
) -> Dict[str, str]:
    return await tag_service.delete_tag(db=db, tag_id=tag_id, current_user=current_user)


@router.delete(
    "/blog/tags/{tag_id}/db",
    dependencies=[Depends(get_current_superuser), Depends(rate_limiter)],
)
@cache(
    key_prefix="blog:tag",
    resource_id_name="tag_id",
    pattern_to_invalidate_extra=["blog:tags:*"],
)
async def erase_db_tag(
    request: Request,
    tag_id: UUID,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    tag_service: TagService = Depends(get_tag_service),
) -> Dict[str, str]:
    return await tag_service.db_delete_tag(db=db, tag_id=tag_id)
