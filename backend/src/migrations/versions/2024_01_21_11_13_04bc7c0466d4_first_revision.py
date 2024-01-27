"""First Revision

Revision ID: 04bc7c0466d4
Revises: 
Create Date: 2024-01-21 11:13:53.207867

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "04bc7c0466d4"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "system_tier",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_system_tier_id"), "system_tier", ["id"], unique=False)
    op.create_table(
        "system_token_blacklist",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("token", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_system_token_blacklist_id"), "system_token_blacklist", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_system_token_blacklist_token"), "system_token_blacklist", ["token"], unique=False
    )
    op.create_table(
        "system_rate_limit",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("tier_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("path", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("limit", sa.Integer(), nullable=False),
        sa.Column("period", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tier_id"],
            ["system_tier.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_system_rate_limit_id"), "system_rate_limit", ["id"], unique=False)
    op.create_index(
        op.f("ix_system_rate_limit_tier_id"), "system_rate_limit", ["tier_id"], unique=False
    )
    op.create_table(
        "system_user",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("tier_id", sqlmodel.sql.sqltypes.GUID(), nullable=True),
        sa.Column("hashed_password", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column("profile_image_url", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("username", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tier_id"],
            ["system_tier.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_system_user_email"), "system_user", ["email"], unique=True)
    op.create_index(op.f("ix_system_user_id"), "system_user", ["id"], unique=False)
    op.create_index(op.f("ix_system_user_is_deleted"), "system_user", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_system_user_tier_id"), "system_user", ["tier_id"], unique=False)
    op.create_index(op.f("ix_system_user_username"), "system_user", ["username"], unique=True)
    op.create_table(
        "blog_post",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("user_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("media_url", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("text", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["system_user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_blog_post_id"), "blog_post", ["id"], unique=False)
    op.create_index(op.f("ix_blog_post_is_deleted"), "blog_post", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_blog_post_user_id"), "blog_post", ["user_id"], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_blog_post_user_id"), table_name="blog_post")
    op.drop_index(op.f("ix_blog_post_is_deleted"), table_name="blog_post")
    op.drop_index(op.f("ix_blog_post_id"), table_name="blog_post")
    op.drop_table("blog_post")
    op.drop_index(op.f("ix_system_user_username"), table_name="system_user")
    op.drop_index(op.f("ix_system_user_tier_id"), table_name="system_user")
    op.drop_index(op.f("ix_system_user_is_deleted"), table_name="system_user")
    op.drop_index(op.f("ix_system_user_id"), table_name="system_user")
    op.drop_index(op.f("ix_system_user_email"), table_name="system_user")
    op.drop_table("system_user")
    op.drop_index(op.f("ix_system_rate_limit_tier_id"), table_name="system_rate_limit")
    op.drop_index(op.f("ix_system_rate_limit_id"), table_name="system_rate_limit")
    op.drop_table("system_rate_limit")
    op.drop_index(op.f("ix_system_token_blacklist_token"), table_name="system_token_blacklist")
    op.drop_index(op.f("ix_system_token_blacklist_id"), table_name="system_token_blacklist")
    op.drop_table("system_token_blacklist")
    op.drop_index(op.f("ix_system_tier_id"), table_name="system_tier")
    op.drop_table("system_tier")
    # ### end Alembic commands ###
