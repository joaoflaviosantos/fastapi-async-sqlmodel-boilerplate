# Built-in Dependencies
from typing import Annotated, Dict, Any
from uuid import UUID

# Third-Party Dependencies
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import Depends, Request
import fastapi

# Local Dependencies
from src.core.api.dependencies import get_current_user, get_current_superuser
from src.apps.system.rate_limits.crud import crud_rate_limits
from src.apps.system.users.crud import crud_users
from src.apps.system.tiers.crud import crud_tiers
from src.apps.system.tiers.schemas import TierRead
from src.apps.system.tiers.models import Tier
from src.core.db.session import async_get_db
from src.core.exceptions.http_exceptions import (
    DuplicateValueException,
    NotFoundException,
    ForbiddenException,
)
from src.apps.system.users.schemas import (
    UserCreate,
    UserCreateInternal,
    UserUpdate,
    UserRead,
    UserTierUpdate,
)
from src.core.utils.paginated import (
    PaginatedListResponse,
    paginated_response,
    compute_offset,
)
from src.core.security import get_password_hash, blacklist_token, oauth2_scheme
from src.core.config import settings
from src.core.utils import cache

router = fastapi.APIRouter(tags=["System - Users"])


@router.post("/system/users", response_model=UserRead, status_code=201)
async def write_user(
    request: Request,
    user: UserCreate,
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> UserRead:
    email_row = await crud_users.exists(db=db, email=user.email)
    if email_row:
        raise DuplicateValueException("Email is already registered")

    username_row = await crud_users.exists(db=db, username=user.username)
    if username_row:
        raise DuplicateValueException("Username not available")

    user_internal_dict = user.model_dump()
    user_internal_dict["hashed_password"] = get_password_hash(
        password=user_internal_dict["password"]
    )
    del user_internal_dict["password"]

    user_internal = UserCreateInternal(**user_internal_dict)
    return await crud_users.create(db=db, object=user_internal)


@router.get("/system/users", response_model=PaginatedListResponse[UserRead])
async def read_users(
    request: Request,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    page: int = 1,
    items_per_page: int = 10,
) -> dict:
    users_data = await crud_users.get_multi(
        db=db,
        offset=compute_offset(page, items_per_page),
        limit=items_per_page,
        schema_to_select=UserRead,
        is_deleted=False,
    )

    return paginated_response(crud_data=users_data, page=page, items_per_page=items_per_page)


@router.get("/system/users/me/", response_model=UserRead)
async def read_users_me(
    request: Request,
    current_user: Annotated[UserRead, Depends(get_current_user)],
) -> UserRead:
    return current_user


@router.get("/system/users/{id}", response_model=UserRead)
async def read_user(
    request: Request,
    id: UUID,
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict:
    db_user = await crud_users.get(db=db, schema_to_select=UserRead, id=id, is_deleted=False)
    if db_user is None:
        raise NotFoundException("User not found")

    return db_user


@router.patch("/system/users/{id}")
async def patch_user(
    request: Request,
    values: UserUpdate,
    id: UUID,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> Dict[str, str]:
    db_user = await crud_users.get(db=db, schema_to_select=UserRead, id=id)
    if db_user is None:
        raise NotFoundException("User not found")

    if db_user["username"] != current_user["username"] and not current_user["is_superuser"]:
        raise ForbiddenException("detail: You are not allowed to update this user")

    if values.username != db_user["username"]:
        existing_username = await crud_users.exists(db=db, username=values.username)
        if existing_username:
            raise DuplicateValueException("Username not available")

    if values.email != db_user["email"]:
        existing_email = await crud_users.exists(db=db, email=values.email)
        if existing_email:
            raise DuplicateValueException("Email is already registered")

    await crud_users.update(db=db, object=values, id=id)
    return {"message": "User updated"}


@router.delete("/system/users/{id}")
async def erase_user(
    request: Request,
    id: UUID,
    current_user: Annotated[UserRead, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    token: str = Depends(oauth2_scheme),
) -> Dict[str, str]:
    db_user = await crud_users.get(db=db, schema_to_select=UserRead, id=id)
    if not db_user:
        raise NotFoundException("User not found")

    if id != current_user["id"] and not current_user["is_superuser"]:
        raise ForbiddenException("detail: You are not allowed to delete this user")

    await crud_users.delete(db=db, db_row=db_user, id=id)
    if id == current_user["id"]:
        await blacklist_token(token=token, db=db)
    return {"message": "User deleted"}


@router.delete("/system/db_users/{id}", dependencies=[Depends(get_current_superuser)])
async def erase_db_user(
    request: Request,
    id: UUID,
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> Dict[str, str]:
    db_user = await crud_users.get(db=db, schema_to_select=UserRead, id=id)
    if not db_user:
        raise NotFoundException("User not found")

    # Remove user from Redis cache
    if cache.client:
        await cache.client.hdel(
            settings.REDIS_HASH_SYSTEM_AUTH_VALID_USERNAMES, db_user["username"]
        )

    # Delete user from the database
    await crud_users.db_delete(db=db, id=id)
    return {"message": "User deleted from the database"}


@router.get(
    "/system/users/{id}/rate_limits",
    dependencies=[Depends(get_current_superuser)],
)
async def read_user_rate_limits(
    request: Request,
    id: UUID,
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> Dict[str, Any]:
    db_user: dict | None = await crud_users.get(db=db, id=id, schema_to_select=UserRead)
    if db_user is None:
        raise NotFoundException("User not found")

    if db_user["tier_id"] is None:
        db_user["tier_rate_limits"] = []
        return db_user

    db_tier = await crud_tiers.get(db=db, id=db_user["tier_id"])
    if db_tier is None:
        raise NotFoundException("Tier not found")

    db_rate_limits = await crud_rate_limits.get_multi(db=db, tier_id=db_tier["id"])

    db_user["tier_rate_limits"] = db_rate_limits["data"]

    return db_user


@router.get("/system/users/{id}/tiers")
async def read_user_tier(
    request: Request,
    id: UUID,
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> dict | None:
    db_user = await crud_users.get(db=db, id=id, schema_to_select=UserRead)
    if db_user is None:
        raise NotFoundException("User not found")

    db_tier = await crud_tiers.exists(db=db, id=db_user["tier_id"])
    if not db_tier:
        raise NotFoundException("Tier not found")

    joined = await crud_users.get_joined(
        db=db,
        join_model=Tier,
        join_prefix="tier_",
        schema_to_select=UserRead,
        join_schema_to_select=TierRead,
        username=db_user["username"],
    )

    return joined


@router.patch(
    "/system/users/{id}/tiers",
    dependencies=[Depends(get_current_superuser)],
)
async def patch_user_tier(
    request: Request,
    id: UUID,
    values: UserTierUpdate,
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> Dict[str, str]:
    db_user = await crud_users.get(db=db, id=id, schema_to_select=UserRead)
    if db_user is None:
        raise NotFoundException("User not found")

    db_tier = await crud_tiers.get(db=db, id=values.tier_id)
    if db_tier is None:
        raise NotFoundException("Tier not found")

    await crud_users.update(db=db, object=values, id=id)
    return {
        "message": f"User '{db_user['username']}' have been assigned to '{db_tier['name']}' tier."
    }
