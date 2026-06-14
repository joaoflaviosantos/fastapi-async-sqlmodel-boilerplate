# Built-in Dependencies
from datetime import datetime

# Third-Party Dependencies
from pydantic import ConfigDict

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
    pass


class PostCreate(PostBase, PostMediaBase):
    model_config = ConfigDict(extra="forbid")


class PostCreateInternal(PostCreate, PostRelationshipBase):
    pass


@optional()
class PostUpdate(PostContentBase, PostMediaBase):
    model_config = ConfigDict(extra="forbid")


class PostUpdateInternal(PostUpdate):
    updated_at: datetime


class PostDelete(SoftDeleteMixin):
    model_config = ConfigDict(extra="forbid")
