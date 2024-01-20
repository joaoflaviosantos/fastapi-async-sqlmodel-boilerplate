# Built-in Dependencies
from datetime import datetime
from uuid import UUID

# Local Dependencies
from src.core.common.models import TimestampMixin
from src.apps.system.tiers.models import Base, TierBase
from src.core.utils.partial import optional


class Tier(TimestampMixin, TierBase):
    """
    API Schema

    Description:
    ----------
    'Tier' ORM class that maps the 'system_tier' database table.
    """

    pass


class TierRead(TierBase):
    """
    API Schema

    Description:
    ----------
    'TierRead' schema for reading tier data.
    """

    id: UUID
    created_at: datetime


class TierCreate(TierBase):
    """
    API Schema

    Description:
    ----------
    'TierCreate' schema is used for creating a tier entry.
    """

    pass


class TierCreateInternal(TierCreate):
    """
    API Schema

    Description:
    ----------
    'TierCreateInternal' schema is used internally for creating a tier entry.
    """

    pass


# All these fields are optional
@optional()
class TierUpdate(TierBase):
    """
    API Schema

    Description:
    ----------
    'TierUpdate' schema is used for updating a tier entry.
    """

    name: str | None = None


class TierUpdateInternal(TierUpdate):
    """
    API Schema

    Description:
    ----------
    'TierUpdateInternal' schema is used internally for updating a tier entry.
    """

    updated_at: datetime


class TierDelete(Base):
    """
    API Schema

    Description:
    ----------
    'TierDelete' schema is used for deleting a tier entry.
    """

    pass
