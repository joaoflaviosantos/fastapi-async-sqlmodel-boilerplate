# Built-in Dependencies
from typing import Dict, Optional, List, Tuple
from uuid import UUID

# Third-Party Dependencies
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import IntegrityError

# Local Dependencies
from src.apps.example.items.repositories import ItemRepository, item_repository
from src.apps.example.items.schemas import (
    Item,
    ItemCreate,
    ItemUpdate,
    ItemRead,
    ItemCreateInternal,
)
from src.core.exceptions.http_exceptions import (
    NotFoundException,
    ForbiddenException,
    InternalErrorException,
)
from src.core.utils.api_params import compute_offset, paginated_response


class ItemService:
    def __init__(self, item_repo: ItemRepository):
        self.item_repo = item_repo

    async def create_item(self, db: AsyncSession, item: ItemCreate, current_user: dict) -> ItemRead:
        item_internal_dict = item.model_dump()
        item_internal_dict["created_by_user_id"] = current_user["id"]
        item_internal_dict["updated_by_user_id"] = current_user["id"]

        item_internal = ItemCreateInternal(**item_internal_dict)
        new_item = await self.item_repo.create(db=db, object=item_internal)
        return await self.item_repo.get(db=db, schema_to_select=ItemRead, id=new_item.id)

    async def get_items(
        self,
        db: AsyncSession,
        page: int = 1,
        items_per_page: int = 10,
        filters: dict | None = None,
        sort_by: Optional[List[Tuple[str, str]]] = None,
    ) -> dict:
        items_data = await self.item_repo.get_multi_with_main_relations(
            db=db,
            offset=compute_offset(page, items_per_page),
            limit=items_per_page,
            sort_by=sort_by,
            **(filters or {}),
        )
        return paginated_response(data=items_data, page=page, items_per_page=items_per_page)

    async def get_item(self, db: AsyncSession, item_id: UUID) -> dict:
        db_item = await self.item_repo.get_single_with_main_relations(db=db, id=item_id)
        if db_item is None:
            raise NotFoundException(detail="Item not found")

        return db_item

    async def update_item(
        self, db: AsyncSession, item_id: UUID, values: ItemUpdate
    ) -> Dict[str, str]:
        db_item = await self.item_repo.get(
            db=db, schema_to_select=ItemRead, id=item_id, is_deleted=False
        )
        if db_item is None:
            raise NotFoundException(detail="Item not found")

        await self.item_repo.update(db=db, object=values, id=item_id)
        return {"message": "Item updated"}

    async def delete_item(
        self, db: AsyncSession, item_id: UUID, current_user: dict
    ) -> Dict[str, str]:
        db_item = await self.item_repo.get(
            db=db, schema_to_select=Item, id=item_id, is_deleted=False
        )
        if db_item is None or db_item["is_deleted"]:
            if current_user["is_superuser"]:
                raise NotFoundException(detail="Item already deleted (soft delete).")
            raise NotFoundException(detail="Item not found")

        await self.item_repo.delete(db=db, db_row=db_item, id=item_id)
        return {"message": "Item deleted"}

    async def db_delete_item(self, db: AsyncSession, item_id: UUID) -> Dict[str, str]:
        db_item = await self.item_repo.get(db=db, return_is_deleted=True, id=item_id)
        if db_item is None:
            raise NotFoundException(detail="Item not found")

        try:
            await self.item_repo.db_delete(db=db, id=item_id)
        except IntegrityError:
            raise ForbiddenException(detail="Item cannot be deleted")
        except Exception:
            raise InternalErrorException(
                detail="An unexpected error occurred. Please try again later or contact support if the problem persists."
            )

        return {"message": "Item deleted from the database"}


item_service = ItemService(item_repository)
