# Built-in Dependencies
from typing import Annotated
from datetime import datetime
from uuid import UUID

# Third-Party Dependencies
from pydantic import BaseModel, Field, ConfigDict, field_validator

# Local Dependencies
from src.core.common.schemas import TimestampSchema
from src.core.utils.rate_limit import sanitize_path

class RateLimitBase(BaseModel):
    path: Annotated[
        str, 
        Field(examples=["users"])
    ]
    limit: Annotated[
        int,
        Field(examples=[5])
    ]
    period: Annotated[
        int,
        Field(examples=[60])
    ]

    @field_validator('path')
    def validate_and_sanitize_path(cls, v: str) -> str:
        return sanitize_path(v)


class RateLimit(TimestampSchema, RateLimitBase):
    tier_id: UUID
    name: Annotated[
        str | None,
        Field(
            default=None,
            examples=["users:5:60"]
        )
    ]


class RateLimitRead(RateLimitBase):
    id: UUID
    tier_id: UUID
    name: str


class RateLimitCreate(RateLimitBase):
    model_config = ConfigDict(extra='forbid')
    
    name: Annotated[
        str | None,
        Field(
            default=None,
            examples=["api_v1_users:5:60"]
        )
    ]


class RateLimitCreateInternal(RateLimitCreate):
    tier_id: UUID


class RateLimitUpdate(BaseModel):
    path: str | None = Field(default=None)
    limit: int | None = None
    period: int | None = None
    name: str | None = None

    @field_validator('path')
    def validate_and_sanitize_path(cls, v: str) -> str:
        return sanitize_path(v) if v is not None else None    


class RateLimitUpdateInternal(RateLimitUpdate):
    updated_at: datetime


class RateLimitDelete(BaseModel):
    pass
