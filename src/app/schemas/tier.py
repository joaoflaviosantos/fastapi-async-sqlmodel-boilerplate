from typing import Annotated
from datetime import datetime

from pydantic import BaseModel, Field

from ..core.schemas import TimestampSchema

class TierBase(BaseModel):
    name: Annotated[
        str, 
        Field(examples=["free"])
    ]


class Tier(TimestampSchema, TierBase):
    pass


class TierRead(TierBase):
    id: int
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
