# Built-in Dependencies
from uuid import UUID

# Third-Party Dependencies
from sqlmodel import Field

# Local Dependencies
from src.core.common.models import (
    SoftDeleteMixin,
    UserTrackingMixin,
    TimestampMixin,
    UUIDMixin,
    Base,
)


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
    relation_example_id: UUID | None = Field(
        default=None,
        foreign_key="example_relation.id",
        index=True,
        description="ID of the related record",
    )


class Item(
    SoftDeleteMixin,
    UserTrackingMixin,
    TimestampMixin,
    ItemRelationshipBase,
    ItemMediaBase,
    ItemContentBase,
    UUIDMixin,
    table=True,
):
    __tablename__ = "example_item"
    __table_args__ = ({"comment": "Example item information"},)
