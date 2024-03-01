# Built-in Dependencies
from uuid import UUID

# Third-Party Dependencies
from sqlmodel import Field

# Local Dependencies
from src.core.common.models import (
    SoftDeleteMixin,
    TimestampMixin,
    UUIDMixin,
    Base,
)


class UserPersonalInfoBase(Base):
    """
    SQLModel Base

    Description:
    ----------
    'UserPersonalInfoBase' pydantic class with personal information for a user.

    Fields:
    ----------
    - 'name': User's full name.
    - 'username': User's unique username.
    - 'email': User's unique email address.

    Examples:
    ----------
    Example of a valid data:
    - 'name': "User Userson"
    - 'username': "userson"
    - 'email': "user.userson@example.com"
    """

    # Data Columns
    name: str = Field(
        min_length=2,
        max_length=100,
        nullable=False,
        description="User's full name",
        schema_extra={"examples": ["User Userson"]},
    )
    username: str = Field(
        min_length=2,
        max_length=20,
        unique=True,
        index=True,
        nullable=False,
        regex=r"^[a-z0-9]+$",
        description="User's username",
        schema_extra={"examples": ["userson"]},
    )
    email: str = Field(
        max_length=50,
        unique=True,
        index=True,
        nullable=False,
        regex=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
        description="User's email address",
        schema_extra={"examples": ["user.userson@example.com"]},
    )  # Todo: Use EmailStr when it's supported by SQLModel (https://github.com/tiangolo/sqlmodel/pull/762)


class UserMediaBase(Base):
    """
    SQLModel Base

    Description:
    ----------
    'UserMediaBase' pydantic class with media-related information for a user.

    Fields:
    ----------
    - 'profile_image_url': URL of the user's profile image.

    Examples:
    ----------
    Example of a valid data:
    - 'profile_image_url': "https://www.imageurl.com/profile_image.jpg"
    """

    # Data Columns
    profile_image_url: str = Field(
        default="https://www.imageurl.com/default_profile_image.jpg",
        description="URL of the user's profile image",
        schema_extra={"examples": ["https://www.imageurl.com/profile_image.jpg"]},
    )


class UserPermissionBase(Base):
    """
    SQLModel Base

    Description:
    ----------
    'UserPermissionBase' pydantic class with permission-related information for a user.

    Fields:
    ----------
    - 'is_superuser': Indicates whether the user has superuser privileges.

    Examples:
    ----------
    Example of a valid data:
    - 'is_superuser': False
    """

    # Data Columns
    is_superuser: bool = Field(
        default=False, description="Indicates whether the user has superuser privileges"
    )


class UserSecurityBase(Base):
    """
    SQLModel Base

    Description:
    ----------
    'UserSecurityBase' pydantic class with security-related information for a user.

    Fields:
    ----------
    - 'hashed_password': Hashed password for user authentication.

    Examples:
    ----------
    Example of a valid data:
    - 'hashed_password': "hashed_password_value"
    """

    # Data Columns
    hashed_password: str = Field(
        nullable=False, description="Hashed password for user authentication"
    )


class UserTierBase(Base):
    """
    SQLModel Base

    Description:
    ----------
    'UserTierBase' pydantic class with tier-related information for a user.

    Fields:
    ----------
    - 'tier_id': ID of the tier to which the user belongs.

    Examples:
    ----------
    Example of a valid data:
    - 'tier_id': UUID("123e4567-e89b-12d3-a456-426614174001")
    """

    # Relationships Columns
    tier_id: UUID | None = Field(
        default=None,
        foreign_key="system_tier.id",
        index=True,
        description="ID of the tier to which the user belongs",
    )


class User(
    UserPersonalInfoBase,
    UserMediaBase,
    UserPermissionBase,
    UserSecurityBase,
    UserTierBase,
    UUIDMixin,
    TimestampMixin,
    SoftDeleteMixin,
    table=True,
):
    """
    SQLModel Table: User

    Description:
    ----------
    'User' ORM class representing the 'system_user' database table.

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

    Relationships:
    ----------
    - 'system_tier': Relationship with the 'system_tier' table.

    Examples:
    ----------
    - Example of a valid data:
    - 'name': "John Doe"
    - 'username': "johndoe"
    - 'email': "userson@example.com"
    - 'profile_image_url': "https://www.imageurl.com/profile_image.jpg"
    - 'is_superuser': False
    - 'hashed_password': "hashed_password_value"
    - 'tier_id': UUID("123e4567-e89b-12d3-a456-426614174001")
    - 'id': UUID("123e4567-e89b-12d3-a456-426614174001")
    - 'created_at': datetime.utcnow()
    - 'updated_at': datetime.utcnow()
    - 'deleted_at': None
    - 'is_deleted': False

    Table Name:
    ----------
    'system_user'
    """

    __tablename__ = "admin_user"
