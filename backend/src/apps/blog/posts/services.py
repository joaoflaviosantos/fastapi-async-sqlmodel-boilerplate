# Built-in Dependencies
from typing import Dict, Optional, List, Tuple
from uuid import UUID

# Third-Party Dependencies
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import IntegrityError

# Local Dependencies
from src.apps.system.users.repositories import UserRepository, user_repository
from src.apps.system.users.schemas import UserRead
from src.apps.blog.posts.repositories import PostRepository, post_repository
from src.apps.blog.posts.schemas import (
    Post,
    PostCreate,
    PostUpdate,
    PostRead,
    PostCreateInternal,
)
from src.apps.blog.posts_tags_assoc.repositories import (
    PostTagAssocRepository,
    post_tag_assoc_repository,
)
from src.apps.blog.posts_tags_assoc.schemas import PostTagAssocCreateInternal
from src.apps.blog.tags.repositories import TagRepository, tag_repository
from src.apps.blog.tags.schemas import TagRead
from src.core.exceptions.http_exceptions import (
    NotFoundException,
    ForbiddenException,
    InternalErrorException,
    UnprocessableEntityException,
)
from src.core.utils.api_params import compute_offset, paginated_response


class PostService:
    def __init__(
        self,
        post_repo: PostRepository,
        user_repo: UserRepository,
        tag_repo: TagRepository,
        assoc_repo: PostTagAssocRepository,
    ):
        self.post_repo = post_repo
        self.user_repo = user_repo
        self.tag_repo = tag_repo
        self.assoc_repo = assoc_repo

    async def _validated_tag_ids(self, db: AsyncSession, tag_ids: List[UUID]) -> List[UUID]:
        if not tag_ids:
            raise UnprocessableEntityException(detail="A post must have at least one tag")
        if len(tag_ids) != len(set(tag_ids)):
            raise UnprocessableEntityException(detail="Duplicate tag IDs are not allowed")

        for tag_id in tag_ids:
            db_tag = await self.tag_repo.get(
                db=db, schema_to_select=TagRead, id=tag_id, is_deleted=False
            )
            if db_tag is None:
                raise NotFoundException(detail="Tag not found")

        return tag_ids

    async def _replace_post_tags(
        self, db: AsyncSession, post_id: UUID, tag_ids: List[UUID], with_commit: bool
    ) -> None:
        await self.assoc_repo.db_delete(db=db, with_commit=False, post_id=post_id)
        last_index = len(tag_ids) - 1
        for index, tag_id in enumerate(tag_ids):
            assoc = PostTagAssocCreateInternal(post_id=post_id, tag_id=tag_id)
            await self.assoc_repo.create(
                db=db,
                object=assoc,
                with_commit=with_commit and index == last_index,
            )

    async def create_post(
        self, db: AsyncSession, user_id: UUID, post: PostCreate, current_user: dict
    ) -> dict:
        db_user = await self.user_repo.get(
            db=db, schema_to_select=UserRead, id=user_id, is_deleted=False
        )
        if db_user is None:
            raise NotFoundException(detail="User not found")

        if current_user["id"] != db_user["id"]:
            raise ForbiddenException(detail="You are not allowed to create a post for this user")

        tag_ids = await self._validated_tag_ids(db=db, tag_ids=post.tag_ids)

        post_internal = PostCreateInternal(
            **post.model_dump(exclude={"tag_ids"}),
            user_id=current_user["id"],
        )
        new_post = await self.post_repo.create(db=db, object=post_internal, with_commit=False)
        await self._replace_post_tags(db=db, post_id=new_post.id, tag_ids=tag_ids, with_commit=True)
        created = await self.post_repo.get_single_with_main_relations(
            db=db,
            id=new_post.id,
            user_id=current_user["id"],
            is_deleted=False,
        )
        if created is None:
            raise InternalErrorException(
                detail="An unexpected error occurred. Please try again later or contact support if the problem persists."
            )
        return created

    async def get_posts(
        self,
        db: AsyncSession,
        user_id: UUID,
        page: int = 1,
        items_per_page: int = 10,
        filters: dict | None = None,
        sort_by: Optional[List[Tuple[str, str]]] = None,
    ) -> dict:
        db_user = await self.user_repo.get(
            db=db, schema_to_select=UserRead, id=user_id, is_deleted=False
        )
        if not db_user:
            raise NotFoundException(detail="User not found")

        posts_data = await self.post_repo.get_multi_with_main_relations(
            db=db,
            offset=compute_offset(page, items_per_page),
            limit=items_per_page,
            sort_by=sort_by,
            user_id=db_user["id"],
            is_deleted=False,
            **(filters or {}),
        )
        return paginated_response(data=posts_data, page=page, items_per_page=items_per_page)

    async def get_post(self, db: AsyncSession, user_id: UUID, post_id: UUID) -> dict:
        db_user = await self.user_repo.get(
            db=db, schema_to_select=UserRead, id=user_id, is_deleted=False
        )
        if db_user is None:
            raise NotFoundException(detail="User not found")

        db_post = await self.post_repo.get_single_with_main_relations(
            db=db,
            id=post_id,
            user_id=db_user["id"],
            is_deleted=False,
        )
        if db_post is None:
            raise NotFoundException(detail="Post not found")

        return db_post

    async def update_post(
        self, db: AsyncSession, user_id: UUID, post_id: UUID, values: PostUpdate, current_user: dict
    ) -> Dict[str, str]:
        db_user = await self.user_repo.get(
            db=db, schema_to_select=UserRead, id=user_id, is_deleted=False
        )
        if db_user is None:
            raise NotFoundException(detail="User not found")

        if str(db_user["id"]) != str(current_user["id"]):
            raise ForbiddenException(detail="You are not allowed to update this post")

        db_post = await self.post_repo.get(
            db=db, schema_to_select=PostRead, id=post_id, is_deleted=False
        )
        if db_post is None:
            raise NotFoundException(detail="Post not found")

        update_data = values.model_dump(exclude_unset=True)
        tag_ids = update_data.pop("tag_ids", None)
        if tag_ids is not None:
            validated = await self._validated_tag_ids(db=db, tag_ids=tag_ids)
            await self._replace_post_tags(
                db=db, post_id=post_id, tag_ids=validated, with_commit=False
            )

        await self.post_repo.update(db=db, object=update_data, id=post_id)
        return {"message": "Post updated"}

    async def delete_post(
        self, db: AsyncSession, user_id: UUID, post_id: UUID, current_user: dict
    ) -> Dict[str, str]:
        db_user = await self.user_repo.get(
            db=db, schema_to_select=UserRead, id=user_id, is_deleted=False
        )
        if db_user is None:
            raise NotFoundException(detail="User not found")

        if not current_user["is_superuser"] and str(current_user["id"]) != str(db_user["id"]):
            raise ForbiddenException(detail="You are not allowed to delete this post")

        db_post = await self.post_repo.get(
            db=db, schema_to_select=Post, id=post_id, is_deleted=False
        )
        if db_post is None or db_post["is_deleted"]:
            if current_user["is_superuser"]:
                raise NotFoundException(detail="Post already deleted (soft delete).")
            raise NotFoundException(detail="Post not found")

        await self.post_repo.delete(db=db, db_row=db_post, id=post_id)
        return {"message": "Post deleted"}

    async def db_delete_post(
        self, db: AsyncSession, user_id: UUID, post_id: UUID
    ) -> Dict[str, str]:
        db_user = await self.user_repo.get(
            db=db, schema_to_select=UserRead, id=user_id, is_deleted=False
        )
        if db_user is None:
            raise NotFoundException(detail="User not found")

        db_post = await self.post_repo.get(db=db, return_is_deleted=True, id=post_id)
        if db_post is None:
            raise NotFoundException(detail="Post not found")

        try:
            await self.assoc_repo.db_delete(db=db, with_commit=False, post_id=post_id)
            await self.post_repo.db_delete(db=db, id=post_id)
        except IntegrityError:
            raise ForbiddenException(detail="Post cannot be deleted")
        except Exception:
            raise InternalErrorException(
                detail="An unexpected error occurred. Please try again later or contact support if the problem persists."
            )

        return {"message": "Post deleted from the database"}


post_service = PostService(
    post_repository, user_repository, tag_repository, post_tag_assoc_repository
)
