# Third-Party Dependencies
from sqlmodel import Field, text

# Local Dependencies
from src.core.common.models import TimestampMixin, UUIDMixin, Base


class TierBase(Base):
    """
    SQLModel Base

    Description:
    ----------
    'TierBase' pydantic class.

    Fields:
    ----------
    - 'name' (str): Tier name.
    - 'default' (bool): Indicates whether the tier is the default tier.

    Examples:
    ----------
    Example of a valid data:
    - 'name': "Free"
    - 'default': False
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
    default: bool = Field(
        default=False,
        sa_column_kwargs={"server_default": text("false")},
        description="Indicates whether the tier is the default tier",
    )


class Tier(TierBase, UUIDMixin, TimestampMixin, table=True):
    """
    SQLModel Table

    Description:
    ----------
    'Tier' ORM class that maps the 'system_tier' database table.

    Fields:
    ----------
    - 'name' (str): Tier name.
    - 'default' (bool): Indicates whether the tier is the default tier.
    - 'id' (UUID): Unique identifier for the tier.
    - 'created_at' (datetime): Timestamp for the creation of the tier record.
    - 'updated_at' (datetime): Timestamp for the last update of the tier record.

    Examples:
    ----------
    Example of a valid data:
    - 'name': "Free"
    - 'default': True
    - 'id': UUID("123e4567-e89b-12d3-a456-426614174001")
    - 'created_at': datetime.utcnow()
    - 'updated_at': datetime.utcnow()

    Table Name:
    ----------
    'system_tier'
    """

    __tablename__ = "system_tier"
