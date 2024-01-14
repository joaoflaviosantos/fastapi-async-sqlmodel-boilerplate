# Built-in Dependencies
from typing import Annotated
from datetime import datetime
from uuid import UUID

# Third-Party Dependencies
from pydantic import BaseModel, Field

# Local Dependencies
from src.core.common.schemas import TimestampSchema

class TierBase(BaseModel):
    name: Annotated[
        str, 
        Field(examples=["free"])
    ]


class Tier(TimestampSchema, TierBase):
    pass


class TierRead(TierBase):
    id: UUID
    created_at: datetime


class TierCreate(TierBase):
    pass


class TierCreateInternal(TierCreate):
    pass


class TierUpdate(BaseModel):
    name: str | None = None


class TierUpdateInternal(TierUpdate):
    updated_at: datetime


class TierDelete(BaseModel):
    pass
