# Built-in Dependencies
from uuid import UUID

# Third-Party Dependencies
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

# Local Dependencies
from src.core.common.repository import RepositoryBase
from src.apps.blog.posts.models import Post
from src.apps.blog.posts_tags_assoc.models import PostTagAssoc
from src.apps.blog.posts_tags_assoc.schemas import (
    PostTagAssocCreateInternal,
    PostTagAssocUpdate,
    PostTagAssocUpdateInternal,
    PostTagAssocDelete,
)


class PostTagAssocRepository(
    RepositoryBase[
        PostTagAssoc,
        PostTagAssocCreateInternal,
        PostTagAssocUpdate,
        PostTagAssocUpdateInternal,
        PostTagAssocDelete,
    ]
):
    async def exists_for_active_post(self, db: AsyncSession, tag_id: UUID) -> bool:
        stmt = (
            select(self._model.post_id)
            .join(Post, Post.id == self._model.post_id)
            .where(self._model.tag_id == tag_id)
            .where(Post.is_deleted.is_(False))
            .limit(1)
        )
        result = await db.exec(stmt)
        return result.first() is not None


post_tag_assoc_repository = PostTagAssocRepository(PostTagAssoc)
