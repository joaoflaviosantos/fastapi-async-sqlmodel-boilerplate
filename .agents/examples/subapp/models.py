# Built-in Dependencies
from uuid import UUID

# Third-Party Dependencies
from sqlmodel import Field

# Local Dependencies
from src.core.common.models import SoftDeleteMixin, TimestampMixin, UUIDMixin, Base


class ItemContentBase(Base):
    title: str = Field(
        min_length=2,
        max_length=50,
        nullable=False,
        description="Item title",
        schema_extra={"examples": ["This is an example item"]},
    )
    text: str = Field(
        min_length=1,
        max_length=63206,
        nullable=False,
        description="Item text",
        schema_extra={"examples": ["This is the content of an example item."]},
    )


class ItemMediaBase(Base):
    media_url: str | None = Field(
        max_length=255,
        nullable=True,
        default=None,
        regex=r"^(https?|ftp)://[^\s/$.?#].[^\s]*$",
        description="URL of the media associated with the item",
        schema_extra={"examples": ["https://www.imageurl.com/example_item.jpg"]},
    )


class ItemRelationshipBase(Base):
    user_id: UUID = Field(
        description="User ID associated with the item",
        foreign_key="system_users.id",
        index=True,
    )


class Item(
    SoftDeleteMixin,
    TimestampMixin,
    ItemRelationshipBase,
    ItemMediaBase,
    ItemContentBase,
    UUIDMixin,
    table=True,
):
    __tablename__ = "example_item"
    __table_args__ = ({"comment": "Example item information"},)
