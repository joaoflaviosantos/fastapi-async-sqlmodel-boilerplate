# Third-Party Dependencies
from sqlmodel import Field

# Local Dependencies
from src.core.common.models import TimestampMixin, UUIDMixin, Base


class TierBase(Base):
    """
    SQLModel Base: TierBase
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
    Table: system_tier
    """

    __tablename__ = "system_tier"
