# Built-in Dependencies
from datetime import datetime
from typing import List, Optional
from uuid import UUID

# Third-Party Dependencies
from pydantic import ConfigDict, Field

# Local Dependencies
from src.apps.blog.posts.models import PostContentBase, PostMediaBase, PostRelationshipBase
from src.core.common.models import UUIDMixin, TimestampMixin, SoftDeleteMixin
from src._overrides.pydantic.optional import optional


class PostBase(PostContentBase):
    pass


class Post(
    PostBase, PostMediaBase, PostRelationshipBase, UUIDMixin, TimestampMixin, SoftDeleteMixin
):
    pass


class PostRead(PostBase, PostMediaBase, PostRelationshipBase, UUIDMixin, TimestampMixin):
    tags: Optional[List["TagRead"]] = Field(default=None)


class PostCreate(PostBase, PostMediaBase):
    tag_ids: list[UUID] = Field(
        min_length=1,
        max_length=10,
        description="IDs of tags to attach to the post",
    )
    model_config = ConfigDict(extra="forbid")


class PostCreateInternal(PostBase, PostMediaBase, PostRelationshipBase):
    pass


@optional()
class PostUpdate(PostContentBase, PostMediaBase):
    tag_ids: list[UUID] = Field(
        min_length=1,
        max_length=10,
        description="Replacement set of tag IDs",
    )
    model_config = ConfigDict(extra="forbid")


class PostUpdateInternal(PostUpdate):
    updated_at: datetime


class PostDelete(SoftDeleteMixin):
    model_config = ConfigDict(extra="forbid")


from src.apps.blog.tags.schemas import TagRead  # noqa: E402

PostRead.model_rebuild()
