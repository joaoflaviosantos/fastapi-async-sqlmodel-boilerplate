# Built-in Dependencies
from typing import Annotated
from datetime import datetime

# Third-Party Dependencies
from pydantic import BaseModel, Field, ConfigDict

# Local Dependencies
from src.core.common.models import UUIDMixin, TimestampMixin, SoftDeleteMixin
from src.core.utils.partial import optional
from src.apps.admin.users.models import (
    UserPersonalInfoBase,
    UserMediaBase,
    UserTierBase,
    UserPermissionBase,
    UserSecurityBase,
)


class UserBase(UserPersonalInfoBase):
    """
    Description:
    ----------
    Base schema for representing a user personal info.

    Fields:
    ----------
    - 'name': User's full name.
    - 'username': User's unique username.
    - 'email': User's unique email address.
    """

    pass


class User(
    UserBase,
    UserMediaBase,
    UserTierBase,
    UserPermissionBase,
    UserSecurityBase,
    UUIDMixin,
    TimestampMixin,
    SoftDeleteMixin,
):
    """
    Description:
    ----------
    Schema representing a user, including media, tier, permission, and security information.

    Fields:
    ----------
    - 'name': User's full name.
    - 'username': User's unique username.
    - 'email': User's unique email address.
    - 'profile_image_url': URL of the user's profile image.
    - 'is_superuser': Indicates whether the user has superuser privileges.
    - 'hashed_password': Hashed password for user authentication.
    - 'tier_id': ID of the tier to which the user belongs.
    - 'id': Unique identifier (UUID) for the user.
    - 'created_at': Timestamp for the creation of the user record.
    - 'updated_at': Timestamp for the last update of the user record.
    - 'deleted_at': Timestamp for the deletion of the user record (soft deletion).
    - 'is_deleted': Flag indicating whether the user record is deleted (soft deletion).
    """

    pass


class UserRead(UserBase, UserMediaBase, UserTierBase, UUIDMixin):
    """
    Description:
    ----------
    Read-only schema for retrieving information about a user, including media and tier details.

    Fields:
    ----------
    - 'name': User's full name.
    - 'username': User's unique username.
    - 'email': User's unique email address.
    - 'profile_image_url': URL of the user's profile image.
    - 'tier_id': ID of the tier to which the user belongs.
    - 'id': Unique identifier (UUID) for the user.
    """

    pass


class UserCreate(UserBase):
    """
    Description:
    ----------
    Schema for creating a new user.

    Fields:
    ----------
    - 'name': User's full name.
    - 'username': User's unique username.
    - 'email': User's unique email address.
    - 'password': User's password.
    """

    model_config = ConfigDict(extra="forbid")

    password: Annotated[
        str,
        Field(
            pattern=r"^.{8,}|[0-9]+|[A-Z]+|[a-z]+|[^a-zA-Z0-9]+$",
            examples=["Str1ngst!"],
        ),
    ]


class UserCreateInternal(UserBase, UserSecurityBase, UserTierBase):
    """
    Description:
    ----------
    Internal schema for creating a new user, including security information and tier information.

    Fields:
    ----------
    - 'name': User's full name.
    - 'username': User's unique username.
    - 'email': User's unique email address.
    - 'hashed_password': Hashed password for user authentication.
    - 'tier_id': ID of the tier to which the user belongs (optional).
    """

    pass


@optional()
class UserUpdate(UserBase, UserMediaBase):
    """
    Description:
    ----------
    Schema for updating an existing user, including media information.

    Optional Fields:
    ----------
    - 'name': User's full name.
    - 'username': User's unique username.
    - 'email': User's unique email address.
    - 'profile_image_url': URL of the user's profile image.
    """

    model_config = ConfigDict(extra="forbid")


class UserUpdateInternal(UserUpdate):
    """
    Description:
    ----------
    Internal schema for updating an existing user, including media information and the last update timestamp.

    Fields:
    ----------
    - 'name': User's full name.
    - 'username': User's unique username.
    - 'email': User's unique email address.
    - 'profile_image_url': URL of the user's profile image.
    - 'updated_at': Timestamp for the last update of the user record.
    """

    updated_at: datetime


class UserTierUpdate(UserTierBase):
    """
    Description:
    ----------
    Schema for updating the tier of a user.

    Fields:
    ----------
    - 'tier_id': ID of the tier to which the user belongs.
    """

    pass


class UserDelete(SoftDeleteMixin):
    """
    Description:
    ----------
    Schema for logically deleting a user.

    Fields:
    ----------
    - 'is_deleted': Flag indicating whether the user record is deleted (soft deletion).
    """

    model_config = ConfigDict(extra="forbid")


class UserRestoreDeleted(BaseModel):
    """
    Description:
    ----------
    Schema for restoring a deleted user.

    Fields:
    ----------
    - 'is_deleted': Flag indicating whether the user record is deleted (soft deletion).
    """

    is_deleted: bool
