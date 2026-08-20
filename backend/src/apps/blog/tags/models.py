# Third-Party Dependencies
from sqlmodel import Field

# Local Dependencies
from src.core.common.models import SoftDeleteMixin, TimestampMixin, UUIDMixin, Base


class TagNameBase(Base):
    name: str = Field(
        min_length=2,
        max_length=50,
        nullable=False,
        unique=True,
        description="Tag name",
        schema_extra={"examples": ["Python"]},
    )


class Tag(
    SoftDeleteMixin,
    TimestampMixin,
    TagNameBase,
    UUIDMixin,
    table=True,
):
    __tablename__ = "blog_tag"
    __table_args__ = ({"comment": "Blog tag information"},)
