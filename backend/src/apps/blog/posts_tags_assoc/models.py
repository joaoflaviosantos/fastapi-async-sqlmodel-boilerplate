# Built-in Dependencies
from uuid import UUID

# Third-Party Dependencies
from sqlmodel import Field

# Local Dependencies
from src.core.common.models import Base


class PostTagAssocRelationshipBase(Base):
    post_id: UUID = Field(
        foreign_key="blog_post.id",
        primary_key=True,
        description="Post ID",
    )
    tag_id: UUID = Field(
        foreign_key="blog_tag.id",
        primary_key=True,
        index=True,
        description="Tag ID",
    )


class PostTagAssoc(PostTagAssocRelationshipBase, table=True):
    __tablename__ = "blog_post_tag_assoc"
    __table_args__ = ({"comment": "Association between blog posts and tags"},)
