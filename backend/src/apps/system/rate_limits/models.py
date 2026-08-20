# Built-in Dependencies
from uuid import UUID

# Third-Party Dependencies
from sqlmodel import Field
from sqlalchemy import UniqueConstraint

# Local Dependencies
from src.core.common.models import TimestampMixin, UUIDMixin, Base


class RateLimitConfigBase(Base):
    path: str = Field(
        min_length=2,
        max_length=255,
        nullable=False,
        description="API path for rate limit",
        schema_extra={"examples": ["/api/v1/system/tasks"]},
    )
    limit: int = Field(
        ge=0,
        description="Number of requests allowed in the specified period",
        schema_extra={"examples": [5]},
    )
    period: int = Field(
        ge=1,
        description="Time period (in seconds) during which the limit applies",
        schema_extra={"examples": [60]},
    )


class RateLimitNameBase(Base):
    name: str = Field(
        min_length=2,
        max_length=100,
        nullable=False,
        description="Rate limit name",
        schema_extra={"examples": ["users:5:60"]},
    )


class RateLimitRelationshipBase(Base):
    tier_id: UUID = Field(
        description="Tier ID to which the rate limit is associated",
        foreign_key="system_tier.id",
        index=True,
    )


class RateLimit(
    TimestampMixin,
    RateLimitRelationshipBase,
    RateLimitNameBase,
    RateLimitConfigBase,
    UUIDMixin,
    table=True,
):
    __tablename__ = "system_rate_limit"
    __table_args__ = (
        UniqueConstraint("tier_id", "path", name="uq_system_rate_limit_tier_id_path"),
        UniqueConstraint("tier_id", "name", name="uq_system_rate_limit_tier_id_name"),
        {"comment": "Rate limit configuration"},
    )
