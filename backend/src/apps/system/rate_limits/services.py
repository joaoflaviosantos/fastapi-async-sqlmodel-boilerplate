# Built-in Dependencies
from typing import Dict
from uuid import UUID

# Third-Party Dependencies
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import FastAPI

# Local Dependencies
from src.apps.system.rate_limits.repositories import RateLimitRepository, rate_limit_repository
from src.apps.system.tiers.repositories import TierRepository, tier_repository
from src.core.utils.rate_limit import is_valid_path
from src.core.exceptions.http_exceptions import (
    UnprocessableEntityException,
    DuplicateValueException,
    InternalErrorException,
    RateLimitException,
    ForbiddenException,
    NotFoundException,
)
from src.apps.system.rate_limits.schemas import (
    RateLimitCreateInternal,
    RateLimitCreate,
    RateLimitUpdate,
    RateLimitRead,
)
from src.core.utils.paginated import compute_offset, paginated_response


class RateLimitService:
    def __init__(self, rate_limit_repo: RateLimitRepository, tier_repo: TierRepository):
        self.rate_limit_repo = rate_limit_repo
        self.tier_repo = tier_repo

    async def create_rate_limit(
        self, db: AsyncSession, tier_id: UUID, rate_limit: RateLimitCreate, app: FastAPI
    ) -> RateLimitRead:
        db_tier = await self.tier_repo.get(db=db, id=tier_id)
        if not db_tier:
            raise NotFoundException(detail="Tier not found")

        rate_limit_internal_dict = rate_limit.model_dump()
        rate_limit_internal_dict["tier_id"] = db_tier["id"]

        # Checks if the path is a valid route
        if not is_valid_path(path=rate_limit.path, app=app):
            raise UnprocessableEntityException(detail="Invalid path")

        db_rate_limit = await self.rate_limit_repo.exists(
            db=db, name=rate_limit_internal_dict["name"]
        )
        if db_rate_limit:
            raise DuplicateValueException(detail="Rate Limit Name not available")

        rate_limit_internal = RateLimitCreateInternal(**rate_limit_internal_dict)
        return await self.rate_limit_repo.create(db=db, object=rate_limit_internal)

    async def get_rate_limits(
        self, db: AsyncSession, tier_id: UUID, page: int = 1, items_per_page: int = 10
    ) -> dict:
        db_tier = await self.tier_repo.get(db=db, id=tier_id)
        if not db_tier:
            raise NotFoundException(detail="Tier not found")

        rate_limits_data = await self.rate_limit_repo.get_multi(
            db=db,
            offset=compute_offset(page, items_per_page),
            limit=items_per_page,
            schema_to_select=RateLimitRead,
            tier_id=tier_id,
        )
        return paginated_response(data=rate_limits_data, page=page, items_per_page=items_per_page)

    async def get_rate_limit(self, db: AsyncSession, tier_id: UUID, rate_limit_id: UUID) -> dict:
        db_tier = await self.tier_repo.get(db=db, id=tier_id)
        if not db_tier:
            raise NotFoundException(detail="Tier not found")

        db_rate_limit = await self.rate_limit_repo.get(
            db=db, schema_to_select=RateLimitRead, tier_id=tier_id, id=rate_limit_id
        )
        if db_rate_limit is None:
            raise NotFoundException(detail="Rate Limit not found")

        return db_rate_limit

    async def update_rate_limit(
        self,
        db: AsyncSession,
        tier_id: UUID,
        rate_limit_id: UUID,
        values: RateLimitUpdate,
        app: FastAPI,
    ) -> Dict[str, str]:
        db_tier = await self.tier_repo.get(db=db, id=tier_id)
        if db_tier is None:
            raise NotFoundException(detail="Tier not found")

        db_rate_limit = await self.rate_limit_repo.get(
            db=db, schema_to_select=RateLimitRead, tier_id=tier_id, id=rate_limit_id
        )
        if db_rate_limit is None:
            raise NotFoundException(detail="Rate Limit not found")

        if values.path is not None:
            # Checks if the path is a valid route
            if not is_valid_path(path=values.path, app=app):
                raise NotFoundException(detail="Invalid path")

            # Checks if there is already a rate limit for this path
            db_rate_limit_path = await self.rate_limit_repo.exists(
                db=db, tier_id=tier_id, path=values.path
            )
            if db_rate_limit_path:
                raise DuplicateValueException(detail="There is already a rate limit for this path")

        if values.name is not None:
            db_rate_limit_name = await self.rate_limit_repo.exists(
                db=db,
                name=values.name,
            )
            if db_rate_limit_name:
                raise DuplicateValueException(detail="There is already a rate limit with this name")

        await self.rate_limit_repo.update(db=db, object=values, id=rate_limit_id)
        return {"message": "Rate Limit updated"}

    async def db_delete_rate_limit(
        self, db: AsyncSession, tier_id: UUID, rate_limit_id: UUID
    ) -> Dict[str, str]:
        db_tier = await self.tier_repo.get(db=db, id=tier_id)
        if not db_tier:
            raise NotFoundException(detail="Tier not found")

        db_rate_limit = await self.rate_limit_repo.get(
            db=db, schema_to_select=RateLimitRead, tier_id=tier_id, id=rate_limit_id
        )
        if db_rate_limit is None:
            raise RateLimitException(detail="Rate Limit not found")

        try:
            await self.rate_limit_repo.db_delete(db=db, id=rate_limit_id)
        except IntegrityError:
            raise ForbiddenException(detail="Rate Limit cannot be deleted")
        except Exception as e:
            raise InternalErrorException(
                detail="An unexpected error occurred. Please try again later or contact support if the problem persists."
            )

        return {"message": "Rate Limit deleted from the database"}


# Module-level singleton
rate_limit_service = RateLimitService(rate_limit_repository, tier_repository)
