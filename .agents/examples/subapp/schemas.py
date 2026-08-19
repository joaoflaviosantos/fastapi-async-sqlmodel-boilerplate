# Built-in Dependencies
from datetime import datetime
from typing import Annotated, Optional

# Third-Party Dependencies
from pydantic import ConfigDict, Field

# Local Dependencies
from src.apps.example.items.models import ItemContentBase, ItemMediaBase, ItemRelationshipBase
from src.core.common.models import UUIDMixin, TimestampMixin, SoftDeleteMixin, UserTrackingMixin
from src._overrides.pydantic.optional import optional


class ItemBase(ItemContentBase):
    pass


class Item(
    ItemBase,
    ItemMediaBase,
    ItemRelationshipBase,
    UUIDMixin,
    TimestampMixin,
    UserTrackingMixin,
    SoftDeleteMixin,
):
    pass


class ItemRead(ItemBase, ItemMediaBase, ItemRelationshipBase, UUIDMixin, TimestampMixin):
    updated_by_user_name: Annotated[
        Optional[str], Field(default=None, description="Updated by user name")
    ]
    updated_by_user_email: Annotated[
        Optional[str], Field(default=None, description="Updated by user email")
    ]
    updated_by_user_profile_image_url: Annotated[
        Optional[str], Field(default=None, description="Updated by user profile image URL")
    ]


class ItemCreate(ItemBase, ItemMediaBase, ItemRelationshipBase):
    model_config = ConfigDict(extra="forbid")


class ItemCreateInternal(ItemCreate, UserTrackingMixin):
    pass


@optional()
class ItemUpdate(ItemContentBase, ItemMediaBase):
    model_config = ConfigDict(extra="forbid")


class ItemUpdateInternal(ItemUpdate):
    updated_at: datetime


class ItemDelete(SoftDeleteMixin):
    model_config = ConfigDict(extra="forbid")
