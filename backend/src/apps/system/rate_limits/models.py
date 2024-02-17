# Built-in Dependencies
from uuid import UUID

# Third-Party Dependencies
from sqlmodel import Field

# Local Dependencies
from src.core.common.models import TimestampMixin, UUIDMixin, Base


class RateLimitConfigBase(Base):
    """
    SQLModel Base

    Description:
    ----------
    'RateLimitConfigBase' pydantic class with configuration information for a rate limit.

    Fields:
    ----------
    - 'path': API path for rate limit.
    - 'limit': Number of requests allowed in the specified period.
    - 'period': Time period (in seconds) during which the limit applies.

    Examples:
    ----------
    Example of a valid data:
    - 'path': "users"
    - 'limit': 5
    - 'period': 60
    """

    # Data Columns
    path: str = Field(
        min_length=2,
        max_length=255,
        nullable=False,
        description="API path for rate limit",
        schema_extra={"examples": ["users"]},
    )
    limit: int = Field(
        ge=0,
        description="Number of requests allowed in the specified period",
        schema_extra={"examples": [5]},
    )
    period: int = Field(
        ge=0,
        description="Time period (in seconds) during which the limit applies",
        schema_extra={"examples": [60]},
    )


class RateLimitNameBase(Base):
    """
    SQLModel Base

    Description:
    ----------
    'RateLimitNameBase' pydantic class with name information for a rate limit.

    Fields:
    ----------
    - 'name': Rate limit name.

    Examples:
    ----------
    Example of a valid data:
    - 'name': "users:5:60"
    """

    # Data Columns
    name: str = Field(
        min_length=2,
        max_length=100,
        nullable=False,
        unique=True,
        description="Rate limit name",
        schema_extra={"examples": ["users:5:60"]},
    )


class RateLimitTierBase(Base):
    """
    SQLModel Base

    Description:
    ----------
    'RateLimitTierBase' pydantic class with tier-related information for a rate limit.

    Fields:
    - 'tier_id': ID of the tier to which the rate limit is associated.

    Examples:
    ----------
    Example of a valid data:
    - 'tier_id': UUID("123e4567-e89b-12d3-a456-426614174001")
    """

    # Relationships Columns
    tier_id: UUID = Field(
        description="Tier ID to which the rate limit is associated",
        foreign_key="system_tier.id",
        index=True,
    )


class RateLimit(
    RateLimitConfigBase, RateLimitNameBase, RateLimitTierBase, UUIDMixin, TimestampMixin, table=True
):
    """
    SQLModel Table

    Description:
    ----------
    'RateLimit' ORM class representing the 'system_rate_limit' database table.

    Fields:
    ----------
    - 'path': API path for rate limit.
    - 'limit': Number of requests allowed in the specified period.
    - 'period': Time period (in seconds) during which the limit applies.
    - 'name': Rate limit name.
    - 'tier_id': ID of the tier to which the rate limit is associated.
    - 'id': Unique identifier (UUID) for the rate limit.
    - 'created_at': Timestamp for the creation of the rate limit record.
    - 'updated_at': Timestamp for the last update of the rate limit record.

    Examples:
    ----------
    Example of a valid data:
    - 'path': "users"
    - 'limit': 5
    - 'period': 60
    - 'name': "users:5:60"
    - 'tier_id': UUID("123e4567-e89b-12d3-a456-426614174001")
    - 'id': UUID("123e4567-e89b-12d3-a456-426614174001")
    - 'created_at': datetime.utcnow()
    - 'updated_at': datetime.utcnow()

    Table Name:
    ----------
    'system_rate_limit'
    """

    __tablename__ = "system_rate_limit"
