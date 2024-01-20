# Built-in Dependencies
from uuid import UUID

# Third-Party Dependencies
from sqlmodel import Field

# Local Dependencies
from src.core.common.models import SoftDeleteMixin, TimestampMixin, UUIDMixin, Base


class PostContentBase(Base):
    """
    SQLModel Base

    Description:
    ----------
    'PostContentBase' pydantic class with content information for a post.

    Fields:
    ----------
    - 'title': Title of the post.
    - 'text': Text content of the post.

    Examples:
    ----------
    Examples of valid data for each field:
    - 'title': "This is an example post"
    - 'text': "This is the content of an example post."
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
        schema_extra={"examples": ["This is the content of an example post."]},
    )


class PostMediaBase(Base):
    """
    SQLModel Base

    Description:
    ----------
    'PostMediaBase' pydantic class with media-related information for a post.

    Fields:
    ----------
    - 'media_url': URL of the media associated with the post.

    Examples:
    ----------
    Example of valid data:
    - 'media_url': "https://www.imageurl.com/example_post.jpg"
    """

    # Data Columns
    media_url: str | None = Field(
        max_length=255,
        nullable=True,
        default=None,
        regex=r"^(https?|ftp)://[^\s/$.?#].[^\s]*$",
        description="URL of the media associated with the post",
        schema_extra={"examples": ["https://www.imageurl.com/example_post.jpg"]},
    )


class PostUserBase(Base):
    """
    SQLModel Base

    Description:
    ----------
    'PostUserBase' pydantic class with user-related information for a post.

    Fields:
    ----------
    - 'user_id': ID of the user associated with the post.

    Examples:
    ----------
    Example of a valid data:
    - 'user_id': UUID("123e4567-e89b-12d3-a456-426614174001")
    """

    # Relationships Columns
    user_id: UUID = Field(
        description="User ID associated with the post",
        foreign_key="system_user.id",
        index=True,
    )


class Post(
    PostContentBase,
    PostMediaBase,
    PostUserBase,
    UUIDMixin,
    TimestampMixin,
    SoftDeleteMixin,
    table=True,
):
    """
    SQLModel Table

    Description:
    ----------
    'Post' ORM class representing the 'blog_post' database table.

    Fields:
    ----------
    - 'title': Title of the post.
    - 'text': Text content of the post.
    - 'media_url': URL of the media associated with the post.
    - 'user_id': ID of the user associated with the post.
    - 'id': Unique identifier (UUID) for the post.
    - 'created_at': Timestamp for the creation of the post record.
    - 'updated_at': Timestamp for the last update of the post record.
    - 'deleted_at': Timestamp for the deletion of the post record (soft deletion).
    - 'is_deleted': Flag indicating whether the post record is deleted (soft deletion).

    Table Name:
    ----------
    'blog_post'
    """

    __tablename__ = "blog_post"
