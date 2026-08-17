# Built-in Dependencies
from typing import Annotated, Dict, Optional, List, Tuple
from uuid import UUID

# Third-Party Dependencies
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Request, Depends
import fastapi

# Local Dependencies
from src.apps.system.auth.deps import get_current_user, get_current_superuser
from src.apps.example.items.deps import get_item_service, item_filters, item_sort_order
from src.apps.example.items.services import ItemService
from src.core.db.session import async_get_db
from src.core.utils.cache import cache
from src.apps.example.items.schemas import ItemCreate, ItemUpdate, ItemRead
from src.core.common.schemas import PaginatedListResponse

router = fastapi.APIRouter(tags=["Example - Items"])


@router.post("/example/items/user/{user_id}", response_model=ItemRead, status_code=201)
async def write_item(
    request: Request,
    user_id: UUID,
    item: ItemCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    item_service: ItemService = Depends(get_item_service),
) -> ItemRead:
    return await item_service.create_item(
        db=db, user_id=user_id, item=item, current_user=current_user
    )


@router.get("/example/items/user/{user_id}", response_model=PaginatedListResponse[ItemRead])
@cache(
    key_prefix="example:items:user:{user_id}:page_{page}:items_per_page:{items_per_page}:filters_{filters}:sort_by_{sort_by}",
    resource_id_name="user_id",
    expiration=60,
)
async def read_items(
    request: Request,
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    item_service: ItemService = Depends(get_item_service),
    filters: dict = Depends(item_filters),
    sort_by: Optional[List[Tuple[str, str]]] = Depends(item_sort_order),
    page: int = 1,
    items_per_page: int = 10,
) -> dict:
    return await item_service.get_items(
        db=db,
        user_id=user_id,
        page=page,
        items_per_page=items_per_page,
        filters=filters,
        sort_by=sort_by,
    )


@router.get("/example/items/{item_id}/user/{user_id}", response_model=ItemRead)
@cache(key_prefix="example:items:user:{user_id}:item_cache", resource_id_name="item_id")
async def read_item(
    request: Request,
    user_id: UUID,
    item_id: UUID,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    item_service: ItemService = Depends(get_item_service),
) -> dict:
    return await item_service.get_item(db=db, user_id=user_id, item_id=item_id)


@router.patch("/example/items/{item_id}/user/{user_id}")
@cache(
    "example:items:user:{user_id}:item_cache",
    resource_id_name="item_id",
    pattern_to_invalidate_extra=["example:items:user:{user_id}:*"],
)
async def patch_item(
    request: Request,
    user_id: UUID,
    item_id: UUID,
    values: ItemUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    item_service: ItemService = Depends(get_item_service),
) -> Dict[str, str]:
    return await item_service.update_item(
        db=db, user_id=user_id, item_id=item_id, values=values, current_user=current_user
    )


@router.delete("/example/items/{item_id}/user/{user_id}")
@cache(
    "example:items:user:{user_id}:item_cache",
    resource_id_name="item_id",
    pattern_to_invalidate_extra=["example:items:user:{user_id}:*"],
)
async def erase_item(
    request: Request,
    user_id: UUID,
    item_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    item_service: ItemService = Depends(get_item_service),
) -> Dict[str, str]:
    return await item_service.delete_item(
        db=db, user_id=user_id, item_id=item_id, current_user=current_user
    )


@router.delete(
    "/example/items/{item_id}/user/{user_id}/db",
    dependencies=[Depends(get_current_superuser)],
)
@cache(
    "example:items:user:{user_id}:item_cache",
    resource_id_name="item_id",
    pattern_to_invalidate_extra=["example:items:user:{user_id}:*"],
)
async def erase_db_item(
    request: Request,
    user_id: UUID,
    item_id: UUID,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    item_service: ItemService = Depends(get_item_service),
) -> Dict[str, str]:
    return await item_service.db_delete_item(db=db, user_id=user_id, item_id=item_id)
