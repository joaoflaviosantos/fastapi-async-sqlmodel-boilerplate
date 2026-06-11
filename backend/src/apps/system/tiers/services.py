# Built-in Dependencies
from typing import Dict
from uuid import UUID

# Third-Party Dependencies
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import IntegrityError

# Local Dependencies
from src.apps.system.tiers.repositories import TierRepository
from src.apps.system.tiers.schemas import (
    TierRead,
    TierCreate,
    TierCreateInternal,
    TierUpdate,
)
from src.core.exceptions.http_exceptions import (
    DuplicateValueException,
    InternalErrorException,
    ForbiddenException,
    NotFoundException,
)
from src.core.utils.paginated import compute_offset, paginated_response
from src.core.config import settings


class TierService:
    def __init__(self, tier_repo: TierRepository):
        self.tier_repo = tier_repo

    async def create_tier(self, db: AsyncSession, tier: TierCreate) -> TierRead:
        tier_internal_dict = tier.model_dump()
        db_tier = await self.tier_repo.exists(db=db, name=tier_internal_dict["name"])
        if db_tier:
            raise DuplicateValueException(detail="Tier Name not available")

        tier_internal = TierCreateInternal(**tier_internal_dict)
        return await self.tier_repo.create(db=db, object=tier_internal)

    async def get_tiers(self, db: AsyncSession, page: int = 1, items_per_page: int = 10) -> dict:
        tiers_data = await self.tier_repo.get_multi(
            db=db,
            offset=compute_offset(page, items_per_page),
            limit=items_per_page,
            schema_to_select=TierRead,
        )
        return paginated_response(data=tiers_data, page=page, items_per_page=items_per_page)

    async def get_tier(self, db: AsyncSession, tier_id: UUID) -> dict:
        db_tier = await self.tier_repo.get(db=db, schema_to_select=TierRead, id=tier_id)
        if db_tier is None:
            raise NotFoundException(detail="Tier not found")
        return db_tier

    async def update_tier(
        self, db: AsyncSession, tier_id: UUID, values: TierUpdate
    ) -> Dict[str, str]:
        db_tier = await self.tier_repo.get(db=db, schema_to_select=TierRead, id=tier_id)
        if db_tier is None:
            raise NotFoundException(detail="Tier not found")

        if db_tier["name"] == settings.TIER_NAME_DEFAULT:
            raise ForbiddenException(detail="Default Tier cannot be updated")

        await self.tier_repo.update(db=db, object=values, id=tier_id)
        return {"message": "Tier updated"}

    async def db_delete_tier(self, db: AsyncSession, tier_id: UUID) -> Dict[str, str]:
        db_tier = await self.tier_repo.get(db=db, schema_to_select=TierRead, id=tier_id)
        if db_tier is None:
            raise NotFoundException(detail="Tier not found")

        if db_tier["name"] == settings.TIER_NAME_DEFAULT:
            raise ForbiddenException(detail="Default Tier cannot be deleted")

        try:
            await self.tier_repo.db_delete(db=db, id=tier_id)
        except IntegrityError:
            raise ForbiddenException(detail="Tier cannot be deleted")
        except Exception as e:
            raise InternalErrorException(
                detail="An unexpected error occurred. Please try again later or contact support if the problem persists."
            )

        return {"message": "Tier deleted from the database"}
