# Built-in Dependencies
from datetime import datetime

# Third-Party Dependencies
from pydantic import BaseModel


class Token(BaseModel):
    """
    Token response schema.
    """
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    Token data schema.
    """
    username_or_email: str


class TokenBlacklistBase(BaseModel):
    """
    Base schema for token blacklist.
    """
    token: str
    expires_at: datetime


class TokenBlacklistCreate(TokenBlacklistBase):
    """
    Schema for creating a token blacklist entry.
    """
    pass


class TokenBlacklistUpdate(TokenBlacklistBase):
    """
    Schema for updating a token blacklist entry.
    """
    pass
