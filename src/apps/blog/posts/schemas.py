# Built-in Dependencies
from datetime import datetime

# Third-Party Dependencies
from pydantic import ConfigDict

# Local Dependencies
from src.apps.blog.posts.models import PostContentBase, PostMediaBase, PostUserBase
from src.core.common.models import UUIDMixin, TimestampMixin, SoftDeleteMixin


class PostBase(PostContentBase):
    """
    API Schema

    Description:
    ----------
    Base schema for representing a blog post.

    Fields:
    ----------
    - 'title': Title of the post.
    - 'text': Text content of the post.
    """

    pass


class Post(PostBase, PostMediaBase, PostUserBase, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """
    API Schema

    Description:
    ----------
    Schema representing a blog post, including media and user information.

    Fields:
    ----------
    - 'title': Title of the post.
    - 'text': Text content of the post.
    - 'media_url': URL of the media associated with the post.
    - 'user_id': ID of the user associated with the post.
    - 'id' (UUID): Unique identifier for the post.
    - 'created_at': Timestamp for the creation of the post record.
    - 'updated_at': Timestamp for the last update of the post record.
    - 'deleted_at': Timestamp for the deletion of the post record (soft deletion).
    - 'is_deleted': Flag indicating whether the post record is deleted (soft deletion).
    """

    pass


class PostRead(PostBase, PostMediaBase, PostUserBase, UUIDMixin, TimestampMixin):
    """
    API Schema

    Description:
    ----------
    Read-only schema for retrieving information about a blog post, including media and user details.

    Fields:
    ----------
    - 'title': Title of the post.
    - 'text': Text content of the post.
    - 'media_url': URL of the media associated with the post.
    - 'user_id': ID of the user associated with the post.
    - 'id' (UUID): Unique identifier for the post.
    - 'created_at': Timestamp for the creation of the post record.
    - 'updated_at': Timestamp for the last update of the post record.
    """

    pass


class PostCreate(PostBase, PostMediaBase):
    """
    API Schema

    Description:
    ----------
    Schema for creating a new blog post, including media information.

    Fields:
    ----------
    - 'title': Title of the post.
    - 'text': Text content of the post.
    - 'media_url': URL of the media associated with the post.
    """

    model_config = ConfigDict(extra="forbid")


class PostCreateInternal(PostCreate, PostUserBase):
    """
    API Schema

    Description:
    ----------
    Internal schema for creating a new blog post, including media and user information.

    Fields:
    ----------
    - 'title': Title of the post.
    - 'text': Text content of the post.
    - 'media_url': URL of the media associated with the post.
    - 'user_id': ID of the user associated with the post.
    """

    pass


class PostUpdate(PostContentBase, PostMediaBase):
    """
    API Schema

    Description:
    ----------
    Schema for updating an existing blog post, including media information.

    Fields:
    ----------
    - 'title': Title of the post.
    - 'text': Text content of the post.
    - 'media_url': URL of the media associated with the post.
    """

    model_config = ConfigDict(extra="forbid")


class PostUpdateInternal(PostUpdate):
    """
    API Schema

    Description:
    ----------
    Internal schema for updating an existing blog post, including media information and the last update timestamp.

    Fields:
    ----------
    - 'title': Title of the post.
    - 'text': Text content of the post.
    - 'media_url': URL of the media associated with the post.
    - 'updated_at': Timestamp for the last update of the post record.
    """

    updated_at: datetime


class PostDelete(SoftDeleteMixin):
    """
    API Schema

    Description:
    ----------
    Schema for logically deleting a blog post.

    Fields:
    ----------
    - 'deleted_at': Timestamp for the deletion of the post (soft deletion).
    - 'is_deleted': Flag indicating whether the post record is deleted (soft deletion).
    """

    model_config = ConfigDict(extra="forbid")
