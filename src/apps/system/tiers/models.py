# Third-Party Dependencies
from sqlmodel import Field

# Local Dependencies
from src.core.common.models import TimestampMixin, UUIDMixin, Base


class TierBase(Base):
    """
    SQLModel Base

    Description:
    ----------
    'TierBase' pydantic class.
    """

    # Data Columns
    name: str = Field(
        min_length=2,
        max_length=25,
        nullable=False,
        unique=True,
        description="Tier name",
        schema_extra={"examples": ["Free"]},
    )


class Tier(TierBase, UUIDMixin, TimestampMixin, table=True):
    """
    SQLModel Table

    Description:
    ----------
    'Tier' ORM class that maps the 'system_tier' database table.
    """

    __tablename__ = "system_tier"
