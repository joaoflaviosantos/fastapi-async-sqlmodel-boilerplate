# Built-in Dependencies
from typing import Any, Dict, List, Tuple

# Third-Party Dependencies
from sqlalchemy.engine.row import Row
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

# Local Dependencies
from src.core.common.repository import RepositoryBase
from src.apps.example.items.models import Item
from src.apps.example.items.schemas import (
    ItemCreateInternal,
    ItemUpdate,
    ItemUpdateInternal,
    ItemDelete,
)
from src.apps.system.users.models import User


class ItemRepository(
    RepositoryBase[Item, ItemCreateInternal, ItemUpdate, ItemUpdateInternal, ItemDelete]
):
    async def get_single_with_main_relations(
        self, db: AsyncSession, **kwargs: Any
    ) -> Dict[str, Any] | None:
        item_id = kwargs.get("id")
        if not item_id:
            return None

        stmt = select(
            self._model,
            User.name.label("updated_by_user_name"),
            User.email.label("updated_by_user_email"),
            User.profile_image_url.label("updated_by_user_profile_image_url"),
        ).outerjoin(User, User.id == self._model.updated_by_user_id)

        stmt = stmt.filter(self._model.id == item_id)
        stmt = self.exclude_deleted(stmt)

        db_row = await db.exec(stmt)
        row: Row = db_row.first()
        if not row:
            return None

        model_instance = row[0]
        data = {
            **model_instance.__dict__,
            "updated_by_user_name": row.updated_by_user_name,
            "updated_by_user_email": row.updated_by_user_email,
            "updated_by_user_profile_image_url": row.updated_by_user_profile_image_url,
        }
        data.pop("_sa_instance_state", None)

        return data

    async def get_multi_with_main_relations(
        self,
        db: AsyncSession,
        offset: int = 0,
        limit: int = 100,
        sort_by: List[Tuple[str, str]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        stmt = select(
            self._model,
            User.name.label("updated_by_user_name"),
            User.email.label("updated_by_user_email"),
            User.profile_image_url.label("updated_by_user_profile_image_url"),
        ).outerjoin(User, User.id == self._model.updated_by_user_id)

        stmt = self.apply_filtering(stmt, **kwargs)
        stmt_without_pagination = stmt
        stmt = self.apply_sorting(stmt, sort_by)
        stmt = stmt.offset(offset).limit(limit)

        result = await db.exec(stmt)
        data = [
            {
                **row[self._model].__dict__,
                "updated_by_user_name": row.updated_by_user_name,
                "updated_by_user_email": row.updated_by_user_email,
                "updated_by_user_profile_image_url": row.updated_by_user_profile_image_url,
            }
            for row in result.mappings()
        ]
        for item in data:
            item.pop("_sa_instance_state", None)

        total_count: int = await self.total_count(
            db=db, stmt_without_pagination=stmt_without_pagination
        )
        return {"data": data, "total_count": total_count}


item_repository = ItemRepository(Item)
