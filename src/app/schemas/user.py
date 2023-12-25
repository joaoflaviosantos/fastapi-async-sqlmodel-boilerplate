from typing import Annotated, Optional
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from ..core.schemas import UUIDSchema, TimestampSchema, PersistentDeletion

class UserBase(BaseModel):
    name: Annotated[
        str, 
        Field(min_length=2, max_length=30, examples=["User Userson"])
    ]
    username: Annotated[
        str, 
        Field(min_length=2, max_length=20, pattern=r"^[a-z0-9]+$", examples=["userson"])
    ]
    email: Annotated[
        EmailStr, 
        Field(examples=["user.userson@example.com"])
    ]


class User(TimestampSchema, UserBase, UUIDSchema, PersistentDeletion):
    profile_image_url: Annotated[
        str, 
        Field(default="https://www.profileimageurl.com")
    ]
    hashed_password: str
    is_superuser: bool = False
    tier_id: int | None = None


class UserRead(BaseModel):
    id: int
    
    name: Annotated[
        str, 
        Field(min_length=2, max_length=30, examples=["User Userson"])
    ]
    username: Annotated[
        str, 
        Field(min_length=2, max_length=20, pattern=r"^[a-z0-9]+$", examples=["userson"])
    ]
    email: Annotated[
        EmailStr, 
        Field(examples=["user.userson@example.com"])
    ]
    profile_image_url: str
    tier_id: int | None


class UserCreate(UserBase):
    model_config = ConfigDict(extra='forbid')

    password: Annotated[
        str, 
        Field(pattern=r"^.{8,}|[0-9]+|[A-Z]+|[a-z]+|[^a-zA-Z0-9]+$", examples=["Str1ngst!"])
    ]


class UserCreateInternal(UserBase):
    hashed_password: str


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')

    name: Annotated[
        Optional[str], 
        Field(
            min_length=2, 
            max_length=30, 
            examples=["User Userberg"],
            default=None
        )
    ]
    username: Annotated[
        Optional[str], 
        Field(
            min_length=2, 
            max_length=20, 
            pattern=r"^[a-z0-9]+$", 
            examples=["userberg"],
            default=None
        )
    ]
    email: Annotated[
        Optional[EmailStr],
        Field(
            examples=["user.userberg@example.com"],
            default=None
        )
    ]
    profile_image_url: Annotated[
        Optional[str],
        Field(
            pattern=r"^(https?|ftp)://[^\s/$.?#].[^\s]*$",
            examples=["https://www.profileimageurl.com"],
            default=None
        )
    ]


class UserUpdateInternal(UserUpdate):
    updated_at: datetime


class UserTierUpdate(BaseModel):
    tier_id: int


class UserDelete(BaseModel):
    model_config = ConfigDict(extra='forbid')

    is_deleted: bool
    deleted_at: datetime


class UserRestoreDeleted(BaseModel):
    is_deleted: bool
