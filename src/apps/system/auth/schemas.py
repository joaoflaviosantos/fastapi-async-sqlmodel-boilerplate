# Built-in Dependencies
from datetime import datetime

# Third-Party Dependencies
from pydantic import BaseModel

# Local Dependencies
from src.apps.system.auth.models import TokenBlacklistBase


class Token(BaseModel):
    """
    API Schema

    Description:
    ----------
    'Token' response schema.
    """

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    API Schema

    Description:
    ----------
    'TokenData' response schema.
    """

    username_or_email: str


class TokenBlacklistCreate(TokenBlacklistBase):
    """
    API Schema

    Description:
    ----------
    'TokenBlacklistCreate' schema is used for creating a token blacklist entry.
    """

    pass


class TokenBlacklistUpdate(TokenBlacklistBase):
    """
    API Schema

    Description:
    ----------
    'TokenBlacklistUpdate' schema is used for updating a token blacklist entry.
    """

    pass
