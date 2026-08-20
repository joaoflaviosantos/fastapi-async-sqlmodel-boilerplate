# Built-in Dependencies
from typing import Any, Dict, List, Tuple
from uuid import UUID

# Third-Party Dependencies
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

# Local Dependencies
from src.core.common.repository import RepositoryBase
from src.apps.blog.posts.models import Post
from src.apps.blog.posts.schemas import (
    PostCreateInternal,
    PostRead,
    PostUpdate,
    PostUpdateInternal,
    PostDelete,
)
from src.apps.blog.posts_tags_assoc.models import PostTagAssoc
from src.apps.blog.tags.models import Tag
from src.apps.blog.tags.schemas import TagRead


class PostRepository(
    RepositoryBase[Post, PostCreateInternal, PostUpdate, PostUpdateInternal, PostDelete]
):
    async def _attach_tags(self, db: AsyncSession, posts: List[Dict[str, Any]]) -> None:
        if not posts:
            return

        post_ids = [post["id"] for post in posts]
        stmt = (
            select(PostTagAssoc.post_id, Tag)
            .join(Tag, Tag.id == PostTagAssoc.tag_id)
            .where(PostTagAssoc.post_id.in_(post_ids))
            .where(Tag.is_deleted.is_(False))
        )
        result = await db.exec(stmt)
        tags_by_post: Dict[UUID, List[Dict[str, Any]]] = {}
        for post_id, tag in result.all():
            tag_data = TagRead.model_validate(tag, from_attributes=True).model_dump()
            tags_by_post.setdefault(post_id, []).append(tag_data)

        for post in posts:
            post["tags"] = tags_by_post.get(post["id"], [])

    async def get_single_with_main_relations(
        self, db: AsyncSession, include_tags: bool = True, **kwargs: Any
    ) -> Dict[str, Any] | None:
        data = await self.get(db=db, schema_to_select=PostRead, **kwargs)
        if data is None or not isinstance(data, dict):
            return None
        if include_tags:
            await self._attach_tags(db, [data])
        return data

    async def get_multi_with_main_relations(
        self,
        db: AsyncSession,
        offset: int = 0,
        limit: int = 100,
        sort_by: List[Tuple[str, str]] | None = None,
        include_tags: bool = True,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        tag_id = kwargs.pop("tag_id", None)

        if tag_id is None:
            result = await self.get_multi(
                db=db,
                offset=offset,
                limit=limit,
                sort_by=sort_by,
                schema_to_select=PostRead,
                **kwargs,
            )
        else:
            stmt = (
                select(self._model)
                .join(PostTagAssoc, PostTagAssoc.post_id == self._model.id)
                .where(PostTagAssoc.tag_id == tag_id)
            )
            stmt = self.apply_filtering(stmt, **kwargs)
            stmt_without_pagination = stmt
            stmt = self.apply_sorting(stmt, sort_by)
            stmt = stmt.offset(offset).limit(limit)

            rows = (await db.exec(stmt)).all()
            data = [
                {key: value for key, value in row.__dict__.items() if key != "_sa_instance_state"}
                for row in rows
            ]
            total_count: int = await self.total_count(
                db=db, stmt_without_pagination=stmt_without_pagination
            )
            result = {"data": data, "total_count": total_count}

        if include_tags:
            await self._attach_tags(db, result["data"])
        return result


post_repository = PostRepository(Post)
