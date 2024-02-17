# Built-in Dependencies
from datetime import datetime
from uuid import UUID

# Local Dependencies
from src.core.common.models import TimestampMixin
from src.apps.system.tiers.models import Base, TierBase
from src.core.utils.partial import optional


class Tier(TimestampMixin, TierBase):
    """
    Description:
    ----------
    Schema representing tier data.

    Fields:
    ----------
    - 'name' (str): Tier name.
    - 'created_at' (datetime): Timestamp for the creation of the tier record.
    """

    pass


class TierRead(TierBase):
    """
    Description:
    ----------
    Read-only schema for retrieving tier data.

    Fields:
    ----------
    - 'id' (UUID): Unique identifier for the tier.
    - 'created_at' (datetime): Timestamp for the creation of the tier record.
    """

    id: UUID
    created_at: datetime


class TierCreate(TierBase):
    """
    Description:
    ----------
    Schema for creating a tier entry.

    Fields:
    ----------
    - 'name' (str): Tier name.
    """

    pass


class TierCreateInternal(TierCreate):
    """
    Description:
    ----------
    Internal schema for creating a tier entry.

    Fields:
    ----------
    - 'name' (str): Tier name.
    """

    pass


@optional()
class TierUpdate(TierBase):
    """
    Description:
    ----------
    Schema for updating a tier entry.

    Optional Fields:
    ----------
    - 'name' (str): Tier name (optional).
    """

    name: str | None = None


class TierUpdateInternal(TierUpdate):
    """
    Description:
    ----------
    Internal schema for updating a tier entry.

    Fields:
    ----------
    - 'updated_at' (datetime): Timestamp for the last update of the tier record.
    """

    updated_at: datetime


class TierDelete(Base):
    """
    Description:
    ----------
    Schema for deleting a tier entry.
    """

    pass
