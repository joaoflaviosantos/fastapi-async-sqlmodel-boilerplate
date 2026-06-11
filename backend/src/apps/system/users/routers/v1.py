# Built-in Dependencies
from typing import Annotated, Dict, Any
from uuid import UUID

# Third-Party Dependencies
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Depends, Request
import fastapi

# Local Dependencies
from src.core.api.dependencies import get_current_user, get_current_superuser, get_user_service
from src.apps.system.users.services import UserService
from src.core.db.session import async_get_db
from src.core.common.schemas import PaginatedListResponse
from src.apps.system.users.schemas import (
    UserCreate,
    UserUpdate,
    UserRead,
    UserTierUpdate,
)

router = fastapi.APIRouter(tags=["System - Users"])


@router.post("/system/users", response_model=UserRead, status_code=201)
async def write_user(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    user: UserCreate,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    user_service: UserService = Depends(get_user_service),
) -> UserRead:
    return await user_service.create_user(db=db, user=user)


@router.get("/system/users", response_model=PaginatedListResponse[UserRead])
async def read_users(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    user_service: UserService = Depends(get_user_service),
    page: int = 1,
    items_per_page: int = 10,
) -> dict:
    return await user_service.get_users(db=db, page=page, items_per_page=items_per_page)


@router.get("/system/users/me/", response_model=UserRead)
async def read_users_me(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    return current_user


@router.get("/system/users/{user_id}", response_model=UserRead)
async def read_user(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    user_service: UserService = Depends(get_user_service),
) -> dict:
    return await user_service.get_user(db=db, user_id=user_id)


@router.patch("/system/users/{user_id}")
async def patch_user(
    request: Request,
    values: UserUpdate,
    user_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    user_service: UserService = Depends(get_user_service),
) -> Dict[str, str]:
    return await user_service.update_user(
        db=db, user_id=user_id, values=values, current_user=current_user
    )


from src.core.security import oauth2_scheme


@router.delete("/system/users/{user_id}")
async def erase_user(
    request: Request,
    user_id: UUID,
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends(get_user_service),
) -> Dict[str, str]:
    return await user_service.delete_user(db=db, user_id=user_id, current_user=current_user)


@router.delete("/system/users/{user_id}/db", dependencies=[Depends(get_current_superuser)])
async def erase_db_user(
    request: Request,
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    user_service: UserService = Depends(get_user_service),
) -> Dict[str, str]:
    return await user_service.db_delete_user(db=db, user_id=user_id)


from src.core.common.schemas import PaginatedListResponse


@router.get(
    "/system/users/{user_id}/rate-limits",
    dependencies=[Depends(get_current_superuser)],
)
async def read_user_rate_limits(
    request: Request,
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    user_service: UserService = Depends(get_user_service),
) -> Dict[str, Any]:
    return await user_service.get_user_rate_limits(db=db, user_id=user_id)


@router.get("/system/users/{user_id}/tier")
async def read_user_tier(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    user_service: UserService = Depends(get_user_service),
) -> dict | None:
    return await user_service.get_user_tier(db=db, user_id=user_id)


@router.patch(
    "/system/users/{user_id}/tier",
    dependencies=[Depends(get_current_superuser)],
)
async def patch_user_tier(
    request: Request,
    user_id: UUID,
    values: UserTierUpdate,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    user_service: UserService = Depends(get_user_service),
) -> Dict[str, str]:
    return await user_service.update_user_tier(db=db, user_id=user_id, values=values)
