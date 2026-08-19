# Built-in Dependencies
from typing import Annotated, Dict, Optional, List, Tuple
from uuid import UUID

# Third-Party Dependencies
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Request, Depends
import fastapi

# Local Dependencies
from src.apps.system.auth.deps import get_current_superuser, async_get_user_context_db
from src.apps.example.items.deps import get_item_service, item_filters, item_sort_order
from src.apps.example.items.services import ItemService
from src.core.db.session import async_get_db
from src.core.utils.cache import cache
from src.apps.example.items.schemas import ItemCreate, ItemUpdate, ItemRead
from src.core.common.schemas import PaginatedListResponse

router = fastapi.APIRouter(tags=["Example - Items"])


@router.post("/example/items", response_model=ItemRead, status_code=201)
async def write_item(
    request: Request,
    item: ItemCreate,
    db: Annotated[AsyncSession, Depends(async_get_user_context_db)],
    item_service: ItemService = Depends(get_item_service),
) -> ItemRead:
    current_user = getattr(db, "current_user", {})
    return await item_service.create_item(db=db, item=item, current_user=current_user)


@router.get("/example/items", response_model=PaginatedListResponse[ItemRead])
@cache(
    key_prefix="example:items:items_per_page_{items_per_page}:filters_{filters}:sort_by_{sort_by}:page",
    resource_id_name="page",
    expiration=60,
)
async def read_items(
    request: Request,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    item_service: ItemService = Depends(get_item_service),
    filters: dict = Depends(item_filters),
    sort_by: Optional[List[Tuple[str, str]]] = Depends(item_sort_order),
    page: int = 1,
    items_per_page: int = 10,
) -> dict:
    return await item_service.get_items(
        db=db,
        page=page,
        items_per_page=items_per_page,
        filters=filters,
        sort_by=sort_by,
    )


@router.get("/example/items/{item_id}", response_model=ItemRead)
@cache(key_prefix="example:item", resource_id_name="item_id")
async def read_item(
    request: Request,
    item_id: UUID,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    item_service: ItemService = Depends(get_item_service),
) -> dict:
    return await item_service.get_item(db=db, item_id=item_id)


@router.patch("/example/items/{item_id}")
@cache(
    key_prefix="example:item",
    resource_id_name="item_id",
    pattern_to_invalidate_extra=["example:items:*"],
)
async def patch_item(
    request: Request,
    item_id: UUID,
    values: ItemUpdate,
    db: Annotated[AsyncSession, Depends(async_get_user_context_db)],
    item_service: ItemService = Depends(get_item_service),
) -> Dict[str, str]:
    return await item_service.update_item(db=db, item_id=item_id, values=values)


@router.delete("/example/items/{item_id}")
@cache(
    key_prefix="example:item",
    resource_id_name="item_id",
    pattern_to_invalidate_extra=["example:items:*"],
)
async def erase_item(
    request: Request,
    item_id: UUID,
    db: Annotated[AsyncSession, Depends(async_get_user_context_db)],
    item_service: ItemService = Depends(get_item_service),
) -> Dict[str, str]:
    current_user = getattr(db, "current_user", {})
    return await item_service.delete_item(db=db, item_id=item_id, current_user=current_user)


@router.delete(
    "/example/items/{item_id}/db",
    dependencies=[Depends(get_current_superuser)],
)
@cache(
    key_prefix="example:item",
    resource_id_name="item_id",
    pattern_to_invalidate_extra=["example:items:*"],
)
async def erase_db_item(
    request: Request,
    item_id: UUID,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    item_service: ItemService = Depends(get_item_service),
) -> Dict[str, str]:
    return await item_service.db_delete_item(db=db, item_id=item_id)
