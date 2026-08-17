# Built-in Dependencies
from typing import Annotated, Dict, Optional, List, Tuple
from uuid import UUID

# Third-Party Dependencies
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Request, Depends
import fastapi

# Local Dependencies
from src.apps.system.auth.deps import get_current_user, get_current_superuser
from src.apps.system.tiers.deps import get_tier_service, tier_filters, tier_sort_order
from src.apps.system.tiers.services import TierService
from src.core.db.session import async_get_db
from src.apps.system.tiers.schemas import TierRead, TierCreate, TierUpdate
from src.core.common.schemas import PaginatedListResponse

router = fastapi.APIRouter(tags=["System - Tiers"])


@router.post(
    "/system/tiers",
    dependencies=[Depends(get_current_superuser)],
    status_code=201,
)
async def write_tier(
    request: Request,
    tier: TierCreate,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    tier_service: TierService = Depends(get_tier_service),
) -> TierRead:
    return await tier_service.create_tier(db=db, tier=tier)


@router.get(
    "/system/tiers",
    response_model=PaginatedListResponse[TierRead],
    dependencies=[Depends(get_current_user)],
)
async def read_tiers(
    request: Request,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    tier_service: TierService = Depends(get_tier_service),
    filters: dict = Depends(tier_filters),
    sort_by: Optional[List[Tuple[str, str]]] = Depends(tier_sort_order),
    page: int = 1,
    items_per_page: int = 10,
) -> dict:
    return await tier_service.get_tiers(
        db=db,
        page=page,
        items_per_page=items_per_page,
        filters=filters,
        sort_by=sort_by,
    )


@router.get(
    "/system/tiers/{tier_id}",
    response_model=TierRead,
    dependencies=[Depends(get_current_user)],
)
async def read_tier(
    request: Request,
    tier_id: UUID,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    tier_service: TierService = Depends(get_tier_service),
) -> dict:
    return await tier_service.get_tier(db=db, tier_id=tier_id)


@router.patch("/system/tiers/{tier_id}", dependencies=[Depends(get_current_superuser)])
async def patch_tier(
    request: Request,
    tier_id: UUID,
    values: TierUpdate,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    tier_service: TierService = Depends(get_tier_service),
) -> Dict[str, str]:
    return await tier_service.update_tier(db=db, tier_id=tier_id, values=values)


@router.delete("/system/tiers/{tier_id}/db", dependencies=[Depends(get_current_superuser)])
async def erase_db_tier(
    request: Request,
    tier_id: UUID,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    tier_service: TierService = Depends(get_tier_service),
) -> Dict[str, str]:
    return await tier_service.db_delete_tier(db=db, tier_id=tier_id)
