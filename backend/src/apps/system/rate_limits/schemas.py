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
    Base schema for representing rate limit configuration.

    Custom Validation:
    ----------
    - 'path': Validates and sanitizes the path using the 'sanitize_path' function.
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
    Schema for representing rate limit data.

    Fields:
    ----------
    - 'path' (str): API path for rate limit.
    - 'limit' (int): Number of requests allowed in the specified period.
    - 'period' (int): Time period (in seconds) during which the limit applies.
    - 'name' (str): Rate limit name.
    - 'tier_id' (UUID | None): ID of the tier to which the rate limit is associated.
    """

    pass


class RateLimitRead(UUIDMixin, RateLimitBase, RateLimitNameBase, RateLimitTierBase):
    """
    API Schema

    Description:
    ----------
    Read-only schema for retrieving rate limit data.

    Fields:
    ----------
    - 'id' (UUID): Unique identifier for the rate limit.
    - 'created_at' (datetime): Timestamp for the creation of the rate limit record.
    """

    pass


class RateLimitCreate(RateLimitBase, RateLimitNameBase):
    """
    API Schema

    Description:
    ----------
    Schema for creating a rate limit entry.

    Fields:
    ----------
    - 'path' (str): API path for rate limit.
    - 'limit' (int): Number of requests allowed in the specified period.
    - 'period' (int): Time period (in seconds) during which the limit applies.
    - 'name' (str): Rate limit name.
    """

    model_config = ConfigDict(extra="forbid")


class RateLimitCreateInternal(RateLimitCreate, RateLimitTierBase):
    """
    API Schema

    Description:
    ----------
    Internal schema for creating a rate limit entry.

    Fields:
    ----------
    - 'path' (str): API path for rate limit.
    - 'limit' (int): Number of requests allowed in the specified period.
    - 'period' (int): Time period (in seconds) during which the limit applies.
    - 'name' (str): Rate limit name.
    - 'tier_id' (UUID | None): ID of the tier to which the rate limit is associated.
    """

    pass


# All these fields are optional
@optional()
class RateLimitUpdate(RateLimitBase, RateLimitNameBase):
    """
    API Schema

    Description:
    ----------
    Schema for updating a rate limit entry.

    Optional Fields:
    ----------
    - 'path' (str): API path for rate limit (optional).
    - 'limit' (int): Number of requests allowed in the specified period (optional).
    - 'period' (int): Time period (in seconds) during which the limit applies (optional).
    - 'name' (str): Rate limit name (optional).
    """

    pass


class RateLimitUpdateInternal(RateLimitUpdate):
    """
    API Schema

    Description:
    ----------
    Internal schema for updating a rate limit entry.

    Fields:
    ----------
    - 'updated_at' (datetime): Timestamp for the last update of the rate limit record.

    Optional Fields:
    ----------
    - 'path' (str): API path for rate limit (optional).
    - 'limit' (int): Number of requests allowed in the specified period (optional).
    - 'period' (int): Time period (in seconds) during which the limit applies (optional).
    - 'name' (str): Rate limit name (optional).
    """

    updated_at: datetime


class RateLimitDelete(Base):
    """
    API Schema

    Description:
    ----------
    Schema for deleting a rate limit entry.
    """

    pass
