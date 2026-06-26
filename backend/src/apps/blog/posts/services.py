# Built-in Dependencies
from typing import Dict
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
from src.core.exceptions.http_exceptions import (
    NotFoundException,
    ForbiddenException,
    InternalErrorException,
)
from src.core.utils.paginated import compute_offset, paginated_response


class PostService:
    def __init__(self, post_repo: PostRepository, user_repo: UserRepository):
        self.post_repo = post_repo
        self.user_repo = user_repo

    async def create_post(
        self, db: AsyncSession, user_id: UUID, post: PostCreate, current_user: dict
    ) -> PostRead:
        db_user = await self.user_repo.get(
            db=db, schema_to_select=UserRead, id=user_id, is_deleted=False
        )
        if db_user is None:
            raise NotFoundException(detail="User not found")

        if current_user["id"] != db_user["id"]:
            raise ForbiddenException(detail="You are not allowed to create a post for this user")

        # Prepare the post data
        post_internal_dict = post.model_dump()
        post_internal_dict["user_id"] = current_user["id"]

        post_internal = PostCreateInternal(**post_internal_dict)
        return await self.post_repo.create(db=db, object=post_internal)

    async def get_posts(
        self, db: AsyncSession, user_id: UUID, page: int = 1, items_per_page: int = 10
    ) -> dict:
        db_user = await self.user_repo.get(
            db=db, schema_to_select=UserRead, id=user_id, is_deleted=False
        )
        if not db_user:
            raise NotFoundException(detail="User not found")

        posts_data = await self.post_repo.get_multi(
            db=db,
            offset=compute_offset(page, items_per_page),
            limit=items_per_page,
            schema_to_select=PostRead,
            user_id=db_user["id"],
            is_deleted=False,
        )
        return paginated_response(data=posts_data, page=page, items_per_page=items_per_page)

    async def get_post(self, db: AsyncSession, user_id: UUID, post_id: UUID) -> dict:
        db_user = await self.user_repo.get(
            db=db, schema_to_select=UserRead, id=user_id, is_deleted=False
        )
        if db_user is None:
            raise NotFoundException(detail="User not found")

        db_post = await self.post_repo.get(
            db=db,
            schema_to_select=PostRead,
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

        await self.post_repo.update(db=db, object=values, id=post_id)
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

        db_post = await self.post_repo.get(db=db, schema_to_select=PostRead, id=post_id)
        if db_post is None:
            raise NotFoundException(detail="Post not found")

        try:
            await self.post_repo.db_delete(db=db, id=post_id)
        except IntegrityError:
            raise ForbiddenException(detail="Post cannot be deleted")
        except Exception as e:
            raise InternalErrorException(
                detail="An unexpected error occurred. Please try again later or contact support if the problem persists."
            )

        return {"message": "Post deleted from the database"}


# Module-level singleton
post_service = PostService(post_repository, user_repository)
