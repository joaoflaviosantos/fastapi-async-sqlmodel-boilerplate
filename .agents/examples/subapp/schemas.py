# Built-in Dependencies
from datetime import datetime

# Third-Party Dependencies
from pydantic import ConfigDict

# Local Dependencies
from src.apps.example.items.models import ItemContentBase, ItemMediaBase, ItemRelationshipBase
from src.core.common.models import UUIDMixin, TimestampMixin, SoftDeleteMixin
from src._overrides.pydantic.optional import optional


class ItemBase(ItemContentBase):
    pass


class Item(
    ItemBase, ItemMediaBase, ItemRelationshipBase, UUIDMixin, TimestampMixin, SoftDeleteMixin
):
    pass


class ItemRead(ItemBase, ItemMediaBase, ItemRelationshipBase, UUIDMixin, TimestampMixin):
    pass


class ItemCreate(ItemBase, ItemMediaBase):
    model_config = ConfigDict(extra="forbid")


class ItemCreateInternal(ItemCreate, ItemRelationshipBase):
    pass


@optional()
class ItemUpdate(ItemContentBase, ItemMediaBase):
    model_config = ConfigDict(extra="forbid")


class ItemUpdateInternal(ItemUpdate):
    updated_at: datetime


class ItemDelete(SoftDeleteMixin):
    model_config = ConfigDict(extra="forbid")
