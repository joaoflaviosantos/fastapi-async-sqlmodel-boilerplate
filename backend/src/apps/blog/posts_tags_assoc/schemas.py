# Third-Party Dependencies
from pydantic import ConfigDict

# Local Dependencies
from src.apps.blog.posts_tags_assoc.models import PostTagAssocRelationshipBase
from src.core.common.models import Base


class PostTagAssocCreate(PostTagAssocRelationshipBase):
    model_config = ConfigDict(extra="forbid")


class PostTagAssocCreateInternal(PostTagAssocCreate):
    pass


class PostTagAssocUpdate(Base):
    model_config = ConfigDict(extra="forbid")


class PostTagAssocUpdateInternal(PostTagAssocUpdate):
    pass


class PostTagAssocDelete(Base):
    model_config = ConfigDict(extra="forbid")
