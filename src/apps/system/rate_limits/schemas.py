# Built-in Dependencies
from datetime import datetime

# Third-Party Dependencies
from pydantic import ConfigDict, field_validator

# Local Dependencies
from src.apps.system.rate_limits.models import (
    RateLimitConfigBase,
    RateLimitNameBase,
    RateLimitTierBase,
)
from src.core.common.models import Base, UUIDMixin, TimestampMixin
from src.core.utils.rate_limit import sanitize_path
from src.core.utils.partial import optional


class RateLimitBase(RateLimitConfigBase):
    """
    API Schema

    Description:
    ----------
    'RateLimitBase' pydantic class.
    """

    @field_validator("path")
    def validate_and_sanitize_path(cls, v: str) -> str:
        """
        Validate and sanitize the 'path' field.
        """
        return sanitize_path(v)


class RateLimit(TimestampMixin, RateLimitBase, RateLimitNameBase, RateLimitTierBase):
    """
    API Schema

    Description:
    ----------
    'RateLimit' pydantic class.
    """

    pass


class RateLimitRead(UUIDMixin, RateLimitBase, RateLimitNameBase, RateLimitTierBase):
    """
    API Schema

    Description:
    ----------
    'RateLimitRead' schema for reading rate limit data.
    """

    pass


class RateLimitCreate(RateLimitBase, RateLimitNameBase):
    """
    API Schema

    Description:
    ----------
    'RateLimitCreate' schema is used for creating a rate limit entry.
    """

    model_config = ConfigDict(extra="forbid")


class RateLimitCreateInternal(RateLimitCreate, RateLimitTierBase):
    """
    API Schema

    Description:
    ----------
    'RateLimitCreateInternal' schema is used internally for creating a rate limit entry.
    """

    pass


# All these fields are optional
@optional()
class RateLimitUpdate(RateLimitBase, RateLimitNameBase):
    """
    API Schema

    Description:
    ----------
    'RateLimitUpdate' schema is used for updating a rate limit entry.
    """

    pass


class RateLimitUpdateInternal(RateLimitUpdate):
    """
    API Schema

    Description:
    ----------
    'RateLimitUpdateInternal' schema is used internally for updating a rate limit entry.
    """

    updated_at: datetime


class RateLimitDelete(Base):
    """
    API Schema

    Description:
    ----------
    'RateLimitDelete' schema is used for deleting a rate limit entry.
    """

    pass
