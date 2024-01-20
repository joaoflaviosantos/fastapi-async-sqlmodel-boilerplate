# Built-in Dependencies
from uuid import UUID

# Third-Party Dependencies
from sqlmodel import Field

# Local Dependencies
from src.core.common.models import SoftDeleteMixin, TimestampMixin, UUIDMixin, Base


class PostBase(Base):
    """
    SQLModel Base: PostBase
    """

    # Data Columns
    title: str = Field(
        min_length=2,
        max_length=50,
        nullable=False,
        description="Post title",
        schema_extra={"examples": ["This is an example post"]},
    )
    text: str = Field(
        min_length=1,
        max_length=63206,
        nullable=False,
        description="Post text",
        schema_extra={"examples": ["This is the content of example post."]},
    )
    media_url: str | None = Field(
        max_length=255,
        nullable=True,
        default=None,
        regex=r"^(https?|ftp)://[^\s/$.?#].[^\s]*$",
        description="URL of the media associated with the post",
        schema_extra={"examples": ["https://www.imageurl.com/example_post.jpg"]},
    )

    # Relationships Columns
    user_id: UUID = Field(
        description="User ID associated with the post",
        foreign_key="system_user.id",
        index=True,
    )


class Post(PostBase, UUIDMixin, TimestampMixin, SoftDeleteMixin, table=True):
    """
    Table: blog_post
    """

    __tablename__ = "blog_post"
