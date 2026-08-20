# Built-in Dependencies
from typing import Dict, Optional, List, Tuple
from uuid import UUID

# Third-Party Dependencies
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import IntegrityError

# Local Dependencies
from src.apps.blog.posts_tags_assoc.repositories import (
    PostTagAssocRepository,
    post_tag_assoc_repository,
)
from src.apps.blog.tags.repositories import TagRepository, tag_repository
from src.apps.blog.tags.schemas import (
    Tag,
    TagCreate,
    TagUpdate,
    TagRead,
    TagCreateInternal,
)
from src.core.exceptions.http_exceptions import (
    NotFoundException,
    ForbiddenException,
    DuplicateValueException,
    InternalErrorException,
)
from src.core.utils.api_params import compute_offset, paginated_response


class TagService:
    def __init__(self, tag_repo: TagRepository, assoc_repo: PostTagAssocRepository):
        self.tag_repo = tag_repo
        self.assoc_repo = assoc_repo

    async def create_tag(self, db: AsyncSession, tag: TagCreate) -> TagRead:
        name_taken = await self.tag_repo.get(
            db=db, schema_to_select=TagRead, name=tag.name, return_is_deleted=True
        )
        if name_taken:
            raise DuplicateValueException(detail="Tag name not available")

        tag_internal = TagCreateInternal(**tag.model_dump())
        new_tag = await self.tag_repo.create(db=db, object=tag_internal)
        return await self.tag_repo.get(db=db, schema_to_select=TagRead, id=new_tag.id)

    async def get_tags(
        self,
        db: AsyncSession,
        page: int = 1,
        items_per_page: int = 10,
        filters: dict | None = None,
        sort_by: Optional[List[Tuple[str, str]]] = None,
    ) -> dict:
        tags_data = await self.tag_repo.get_multi(
            db=db,
            offset=compute_offset(page, items_per_page),
            limit=items_per_page,
            schema_to_select=TagRead,
            sort_by=sort_by,
            **(filters or {}),
        )
        return paginated_response(data=tags_data, page=page, items_per_page=items_per_page)

    async def get_tag(self, db: AsyncSession, tag_id: UUID) -> dict:
        db_tag = await self.tag_repo.get(
            db=db, schema_to_select=TagRead, id=tag_id, is_deleted=False
        )
        if db_tag is None:
            raise NotFoundException(detail="Tag not found")

        return db_tag

    async def update_tag(self, db: AsyncSession, tag_id: UUID, values: TagUpdate) -> Dict[str, str]:
        db_tag = await self.tag_repo.get(
            db=db, schema_to_select=TagRead, id=tag_id, is_deleted=False
        )
        if db_tag is None:
            raise NotFoundException(detail="Tag not found")

        if values.name:
            name_taken = await self.tag_repo.get(
                db=db, schema_to_select=TagRead, name=values.name, return_is_deleted=True
            )
            if name_taken is not None and str(name_taken["id"]) != str(tag_id):
                raise DuplicateValueException(detail="Tag name not available")

        await self.tag_repo.update(db=db, object=values, id=tag_id)
        return {"message": "Tag updated"}

    async def delete_tag(
        self, db: AsyncSession, tag_id: UUID, current_user: dict
    ) -> Dict[str, str]:
        db_tag = await self.tag_repo.get(db=db, schema_to_select=Tag, id=tag_id, is_deleted=False)
        if db_tag is None or db_tag["is_deleted"]:
            if current_user["is_superuser"]:
                raise NotFoundException(detail="Tag already deleted (soft delete).")
            raise NotFoundException(detail="Tag not found")

        if await self.assoc_repo.exists_for_active_post(db=db, tag_id=tag_id):
            raise ForbiddenException(detail="Tag cannot be deleted while it is assigned to a post")

        await self.tag_repo.delete(db=db, db_row=db_tag, id=tag_id)
        return {"message": "Tag deleted"}

    async def db_delete_tag(self, db: AsyncSession, tag_id: UUID) -> Dict[str, str]:
        db_tag = await self.tag_repo.get(db=db, return_is_deleted=True, id=tag_id)
        if db_tag is None:
            raise NotFoundException(detail="Tag not found")

        if await self.assoc_repo.exists_for_active_post(db=db, tag_id=tag_id):
            raise ForbiddenException(detail="Tag cannot be deleted while it is assigned to a post")

        try:
            await self.tag_repo.db_delete(db=db, id=tag_id)
        except IntegrityError:
            raise ForbiddenException(detail="Tag cannot be deleted")
        except Exception:
            raise InternalErrorException(
                detail="An unexpected error occurred. Please try again later or contact support if the problem persists."
            )

        return {"message": "Tag deleted from the database"}


tag_service = TagService(tag_repository, post_tag_assoc_repository)
