# Built-in Dependencies
from typing import Annotated, Dict
from uuid import UUID

# Third-Party Dependencies
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Request, Depends
import fastapi

# Local Dependencies
from src.core.common.deps import get_current_superuser, get_rate_limit_service
from src.core.db.session import async_get_db
from src.apps.system.rate_limits.services import RateLimitService
from src.apps.system.rate_limits.schemas import RateLimitCreate, RateLimitUpdate, RateLimitRead
from src.core.common.schemas import PaginatedListResponse

router = fastapi.APIRouter(tags=["System - Rate Limits"])


@router.post(
    "/system/rate-limits/tier/{tier_id}",
    dependencies=[Depends(get_current_superuser)],
    status_code=201,
)
async def write_rate_limit(
    request: Request,
    tier_id: UUID,
    rate_limit: RateLimitCreate,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    rate_limit_service: RateLimitService = Depends(get_rate_limit_service),
) -> RateLimitRead:
    return await rate_limit_service.create_rate_limit(
        db=db, tier_id=tier_id, rate_limit=rate_limit, app=request.app
    )


@router.get(
    "/system/rate-limits/tier/{tier_id}",
    dependencies=[Depends(get_current_superuser)],
    response_model=PaginatedListResponse[RateLimitRead],
)
async def read_rate_limits(
    request: Request,
    tier_id: UUID,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    rate_limit_service: RateLimitService = Depends(get_rate_limit_service),
    page: int = 1,
    items_per_page: int = 10,
) -> dict:
    return await rate_limit_service.get_rate_limits(
        db=db, tier_id=tier_id, page=page, items_per_page=items_per_page
    )


@router.get(
    "/system/rate-limits/{rate_limit_id}/tier/{tier_id}",
    dependencies=[Depends(get_current_superuser)],
    response_model=RateLimitRead,
)
async def read_rate_limit(
    request: Request,
    tier_id: UUID,
    rate_limit_id: UUID,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    rate_limit_service: RateLimitService = Depends(get_rate_limit_service),
) -> dict:
    return await rate_limit_service.get_rate_limit(
        db=db, tier_id=tier_id, rate_limit_id=rate_limit_id
    )


@router.patch(
    "/system/rate-limits/{rate_limit_id}/tier/{tier_id}",
    dependencies=[Depends(get_current_superuser)],
)
async def patch_rate_limit(
    request: Request,
    tier_id: UUID,
    rate_limit_id: UUID,
    values: RateLimitUpdate,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    rate_limit_service: RateLimitService = Depends(get_rate_limit_service),
) -> Dict[str, str]:
    return await rate_limit_service.update_rate_limit(
        db=db, tier_id=tier_id, rate_limit_id=rate_limit_id, values=values, app=request.app
    )


@router.delete(
    "/system/rate-limits/{rate_limit_id}/tier/{tier_id}/db",
    dependencies=[Depends(get_current_superuser)],
)
async def erase_rate_limit(
    request: Request,
    tier_id: UUID,
    rate_limit_id: UUID,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    rate_limit_service: RateLimitService = Depends(get_rate_limit_service),
) -> Dict[str, str]:
    return await rate_limit_service.db_delete_rate_limit(
        db=db, tier_id=tier_id, rate_limit_id=rate_limit_id
    )
