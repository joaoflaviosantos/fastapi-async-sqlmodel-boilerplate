# Built-in Dependencies
from typing import Dict, Any
from uuid import UUID

# Third-Party Dependencies
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import IntegrityError

# Local Dependencies
from src.apps.system.users.repositories import UserRepository, user_repository
from src.apps.system.tiers.repositories import TierRepository, tier_repository
from src.apps.system.rate_limits.repositories import RateLimitRepository, rate_limit_repository
from src.apps.system.users.schemas import (
    UserCreate,
    UserCreateInternal,
    UserUpdate,
    UserRead,
    UserTierUpdate,
    User,
)
from src.apps.system.tiers.schemas import TierRead
from src.apps.system.tiers.models import Tier
from src.core.exceptions.http_exceptions import (
    DuplicateValueException,
    InternalErrorException,
    NotFoundException,
    ForbiddenException,
    BadRequestException,
)
from src.core.security import get_password_hash
from src.core.config import settings
from src.core.utils import cache
from src.core.utils.paginated import compute_offset, paginated_response
from src.apps.system.users.tasks import send_welcome_email


class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        tier_repo: TierRepository,
        rate_limit_repo: RateLimitRepository,
    ):
        self.user_repo = user_repo
        self.tier_repo = tier_repo
        self.rate_limit_repo = rate_limit_repo

    async def create_user(self, db: AsyncSession, user: UserCreate) -> UserRead:
        email_row = await self.user_repo.exists(db=db, email=user.email)
        if email_row:
            raise DuplicateValueException(detail="Email is already registered")

        username_row = await self.user_repo.exists(db=db, username=user.username)
        if username_row:
            raise DuplicateValueException(detail="Username not available")

        user_internal_dict = user.model_dump()
        user_internal_dict["hashed_password"] = get_password_hash(
            password=user_internal_dict["password"]
        )
        del user_internal_dict["password"]

        default_tier = await self.tier_repo.get(db=db, schema_to_select=TierRead, default=True)
        if default_tier is None:
            raise BadRequestException(
                detail="No default tier found. Please create a default tier first."
            )

        user_internal_dict["tier_id"] = default_tier["id"]

        user_internal = UserCreateInternal(**user_internal_dict)

        # Create user on the database
        created_user = await self.user_repo.create(db=db, object=user_internal)

        # Send background welcome email to the user (with Celery)
        send_welcome_email.delay(email=created_user.email, username=created_user.username)

        return created_user

    async def get_users(self, db: AsyncSession, page: int = 1, items_per_page: int = 10) -> dict:
        users_data = await self.user_repo.get_multi(
            db=db,
            offset=compute_offset(page, items_per_page),
            limit=items_per_page,
            schema_to_select=UserRead,
            is_deleted=False,
        )
        return paginated_response(data=users_data, page=page, items_per_page=items_per_page)

    async def get_user(self, db: AsyncSession, user_id: UUID) -> dict:
        db_user = await self.user_repo.get(
            db=db, schema_to_select=UserRead, id=user_id, is_deleted=False
        )
        if db_user is None:
            raise NotFoundException(detail="User not found")
        return db_user

    async def update_user(
        self, db: AsyncSession, user_id: UUID, values: UserUpdate, current_user: dict
    ) -> Dict[str, str]:
        db_user = await self.user_repo.get(db=db, schema_to_select=UserRead, id=user_id)
        if db_user is None:
            raise NotFoundException(detail="User not found")

        # Check if the user is not a superuser and is not updating their own user
        if not current_user["is_superuser"] and str(db_user["id"]) != str(current_user["id"]):
            raise ForbiddenException(detail="You are not allowed to update this user")

        if values.username is not None and values.username != db_user["username"]:
            existing_username = await self.user_repo.exists(db=db, username=values.username)
            if existing_username:
                raise DuplicateValueException(detail="Username not available")

        if values.email is not None and values.email != db_user["email"]:
            existing_email = await self.user_repo.exists(db=db, email=values.email)
            if existing_email:
                raise DuplicateValueException(detail="Email is already registered")

        await self.user_repo.update(db=db, object=values, id=user_id)
        return {"message": "User updated"}

    async def delete_user(
        self, db: AsyncSession, user_id: UUID, current_user: dict
    ) -> Dict[str, str]:
        db_user = await self.user_repo.get(db=db, return_is_deleted=True, id=user_id)
        if db_user is None:
            raise NotFoundException(detail="User not found")
        if db_user["is_deleted"]:
            if current_user["is_superuser"]:
                raise NotFoundException(detail="User already deleted (soft delete).")
            raise NotFoundException(detail="User not found")

        # Check if the user is not a superuser and is not deleting their own user
        if not current_user["is_superuser"] and str(db_user["id"]) != str(current_user["id"]):
            raise ForbiddenException(detail="You are not allowed to delete this user")

        # Soft delete user on the database
        await self.user_repo.delete(db=db, db_row=db_user, id=user_id)

        # Remove user from Redis cache
        if cache.client:
            await cache.client.hdel(
                settings.REDIS_HASH_SYSTEM_AUTH_VALID_USERNAMES, db_user["username"]
            )

        return {"message": "User deleted"}

    async def db_delete_user(self, db: AsyncSession, user_id: UUID) -> Dict[str, str]:
        db_user = await self.user_repo.get(db=db, return_is_deleted=True, id=user_id)
        if not db_user:
            raise NotFoundException(detail="User not found")

        # Delete user from the database
        try:
            await self.user_repo.db_delete(db=db, id=user_id)
        except IntegrityError:
            raise ForbiddenException(detail="User cannot be deleted")
        except Exception as e:
            raise InternalErrorException(
                detail="An unexpected error occurred. Please try again later or contact support if the problem persists."
            )

        # Remove user from Redis cache
        if cache.client:
            await cache.client.hdel(
                settings.REDIS_HASH_SYSTEM_AUTH_VALID_USERNAMES, db_user["username"]
            )

        return {"message": "User deleted from the database"}

    async def get_user_rate_limits(self, db: AsyncSession, user_id: UUID) -> Dict[str, Any]:
        db_user = await self.user_repo.get(db=db, id=user_id, schema_to_select=UserRead)
        if db_user is None:
            raise NotFoundException(detail="User not found")

        if db_user["tier_id"] is None:
            db_user["tier_rate_limits"] = []
            return db_user

        db_tier = await self.tier_repo.get(db=db, id=db_user["tier_id"])
        if db_tier is None:
            raise NotFoundException(detail="Tier not found")

        db_rate_limits = await self.rate_limit_repo.get_multi(db=db, tier_id=db_tier["id"])

        db_user["tier_rate_limits"] = db_rate_limits["data"]

        return db_user

    async def get_user_tier(self, db: AsyncSession, user_id: UUID) -> dict | None:
        db_user = await self.user_repo.get(db=db, id=user_id, schema_to_select=UserRead)
        if db_user is None:
            raise NotFoundException(detail="User not found")

        db_tier = await self.tier_repo.exists(db=db, id=db_user["tier_id"])
        if not db_tier:
            raise NotFoundException(
                detail="Current user tier not found. Please update user tier first."
            )

        joined = await self.user_repo.get_joined(
            db=db,
            join_model=Tier,
            join_prefix="tier_",
            schema_to_select=UserRead,
            join_schema_to_select=TierRead,
            username=db_user["username"],
        )

        return joined

    async def update_user_tier(
        self, db: AsyncSession, user_id: UUID, values: UserTierUpdate
    ) -> Dict[str, str]:
        db_user = await self.user_repo.get(db=db, id=user_id, schema_to_select=UserRead)
        if db_user is None:
            raise NotFoundException(detail="User not found")

        db_tier = await self.tier_repo.get(db=db, id=values.tier_id)
        if db_tier is None:
            raise NotFoundException(detail="Tier not found")

        await self.user_repo.update(db=db, object=values, id=user_id)
        return {
            "message": f"User '{db_user['username']}' have been assigned to '{db_tier['name']}' tier."
        }


# Module-level singleton
user_service = UserService(user_repository, tier_repository, rate_limit_repository)
