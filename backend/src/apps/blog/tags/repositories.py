# Local Dependencies
from src.core.common.repository import RepositoryBase
from src.apps.blog.tags.models import Tag
from src.apps.blog.tags.schemas import (
    TagCreateInternal,
    TagUpdate,
    TagUpdateInternal,
    TagDelete,
)

TagRepository = RepositoryBase[Tag, TagCreateInternal, TagUpdate, TagUpdateInternal, TagDelete]

tag_repository = TagRepository(Tag)
