# Built-in Dependencies
from typing import Annotated, Dict

# Third-Party Dependencies
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request, Depends
import fastapi

# Local Dependencies
from src.core.api.dependencies import get_current_superuser
from src.core.db.session import async_get_db
from src.apps.system.rate_limits.crud import crud_rate_limits
from src.apps.system.tiers.crud import crud_tiers
from src.core.utils.rate_limit import is_valid_path
from src.core.exceptions.http_exceptions import (
    NotFoundException, 
    DuplicateValueException, 
    RateLimitException
)
from src.apps.system.rate_limits.schemas import (
    RateLimitRead,
    RateLimitCreate,
    RateLimitCreateInternal,
    RateLimitUpdate
)
from src.core.utils.paginated import (
    PaginatedListResponse, 
    paginated_response, 
    compute_offset
)
from src.main import app

router = fastapi.APIRouter(tags=["System - Rate Limits"])

@router.post("/system/tier/{tier_name}/rate_limit", dependencies=[Depends(get_current_superuser)], status_code=201)
async def write_rate_limit(
    request: Request, 
    tier_name: str,
    rate_limit: RateLimitCreate, 
    db: Annotated[AsyncSession, Depends(async_get_db)]
) -> RateLimitRead:
    db_tier = await crud_tiers.get(db=db, name=tier_name)
    if not db_tier:
        raise NotFoundException("Tier not found")

    rate_limit_internal_dict = rate_limit.model_dump()
    rate_limit_internal_dict["tier_id"] = db_tier["id"]

    # Checks if the path is a valid route
    if not is_valid_path(rate_limit.path, app):
        raise NotFoundException("Invalid path")

    db_rate_limit = await crud_rate_limits.exists(db=db, name=rate_limit_internal_dict["name"])
    if db_rate_limit:
        raise DuplicateValueException("Rate Limit Name not available")
    
    rate_limit_internal = RateLimitCreateInternal(**rate_limit_internal_dict)
    return await crud_rate_limits.create(db=db, object=rate_limit_internal)


@router.get("/system/tier/{tier_name}/rate_limits", response_model=PaginatedListResponse[RateLimitRead])
async def read_rate_limits(
    request: Request,
    tier_name: str,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    page: int = 1,
    items_per_page: int = 10
) -> dict:
    db_tier = await crud_tiers.get(db=db, name=tier_name)
    if not db_tier:
        raise NotFoundException("Tier not found")

    rate_limits_data = await crud_rate_limits.get_multi(
        db=db,
        offset=compute_offset(page, items_per_page),
        limit=items_per_page,
        schema_to_select=RateLimitRead,
        tier_id=db_tier["id"]
    )

    return paginated_response(
        crud_data=rate_limits_data, 
        page=page, 
        items_per_page=items_per_page
    )


@router.get("/system/tier/{tier_name}/rate_limit/{id}", response_model=RateLimitRead)
async def read_rate_limit(
    request: Request,
    tier_name: str,
    id: int,
    db: Annotated[AsyncSession, Depends(async_get_db)]
) -> dict:
    db_tier = await crud_tiers.get(db=db, name=tier_name)
    if not db_tier:
        raise NotFoundException("Tier not found")
    
    db_rate_limit = await crud_rate_limits.get(
        db=db, 
        schema_to_select=RateLimitRead, 
        tier_id=db_tier["id"],
        id=id
    )
    if db_rate_limit is None:
        raise NotFoundException("Rate Limit not found")

    return db_rate_limit


@router.patch("/system/tier/{tier_name}/rate_limit/{id}", dependencies=[Depends(get_current_superuser)])
async def patch_rate_limit(
    request: Request,
    tier_name: str,
    id: int,
    values: RateLimitUpdate,
    db: Annotated[AsyncSession, Depends(async_get_db)]
) -> Dict[str, str]:
    db_tier = await crud_tiers.get(db=db, name=tier_name)
    if db_tier is None:
        raise NotFoundException("Tier not found")

    # Checks if the path is a valid route
    if not is_valid_path(values.path, app):
        raise NotFoundException("Invalid path")

    db_rate_limit = await crud_rate_limits.get(
        db=db,
        schema_to_select=RateLimitRead, 
        tier_id=db_tier["id"],
        id=id
    )
    if db_rate_limit is None:
        raise NotFoundException("Rate Limit not found")

    if values.path is not None:
        db_rate_limit_path = await crud_rate_limits.exists(
            db=db,
            tier_id=db_tier["id"],
            path=values.path
        )
        if db_rate_limit_path:
            raise DuplicateValueException("There is already a rate limit for this path")

    if values.name is not None:
        db_rate_limit_name = await crud_rate_limits.exists(
            db=db,
            name=values.name,
            )
        if db_rate_limit_name:
            raise DuplicateValueException("There is already a rate limit with this name")

    await crud_rate_limits.update(db=db, object=values, id=db_rate_limit["id"])
    return {"message": "Rate Limit updated"}


@router.delete("/system/tier/{tier_name}/rate_limit/{id}", dependencies=[Depends(get_current_superuser)])
async def erase_rate_limit(
    request: Request,
    tier_name: str,
    id: int,
    db: Annotated[AsyncSession, Depends(async_get_db)]
) -> Dict[str, str]:
    db_tier = await crud_tiers.get(db=db, name=tier_name)
    if not db_tier:
        raise NotFoundException("Tier not found")
    
    db_rate_limit = await crud_rate_limits.get(
        db=db, 
        schema_to_select=RateLimitRead, 
        tier_id=db_tier["id"],
        id=id
    )
    if db_rate_limit is None:
        raise RateLimitException("Rate Limit not found")
    
    await crud_rate_limits.delete(db=db, db_row=db_rate_limit, id=db_rate_limit["id"])
    return {"message": "Rate Limit deleted"}
