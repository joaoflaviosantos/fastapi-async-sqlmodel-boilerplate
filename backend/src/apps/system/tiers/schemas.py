# Built-in Dependencies
from datetime import datetime
from uuid import UUID

# Third-Party Dependencies
from pydantic import ConfigDict

# Local Dependencies
from src.core.common.models import TimestampMixin
from src.apps.system.tiers.models import Base, TierBase
from src.core.utils.partial import optional


class Tier(TimestampMixin, TierBase):
    pass


class TierRead(TierBase):
    id: UUID
    created_at: datetime


class TierCreate(TierBase):
    model_config = ConfigDict(extra="forbid")


class TierCreateInternal(TierCreate):
    pass


@optional()
class TierUpdate(TierBase):
    model_config = ConfigDict(extra="forbid")


class TierUpdateInternal(TierUpdate):
    updated_at: datetime


class TierDelete(Base):
    pass
