# Built-in Dependencies
from datetime import datetime

# Third-Party Dependencies
from pydantic import ConfigDict

# Local Dependencies
from src.apps.blog.tags.models import TagNameBase
from src.core.common.models import UUIDMixin, TimestampMixin, SoftDeleteMixin
from src._overrides.pydantic.optional import optional


class TagBase(TagNameBase):
    pass


class Tag(TagBase, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    pass


class TagRead(TagBase, UUIDMixin, TimestampMixin):
    pass


class TagCreate(TagBase):
    model_config = ConfigDict(extra="forbid")


class TagCreateInternal(TagCreate):
    pass


@optional()
class TagUpdate(TagNameBase):
    model_config = ConfigDict(extra="forbid")


class TagUpdateInternal(TagUpdate):
    updated_at: datetime


class TagDelete(SoftDeleteMixin):
    model_config = ConfigDict(extra="forbid")
