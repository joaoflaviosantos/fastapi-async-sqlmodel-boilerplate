---
name: sqlmodel
description: Create or change models.py, schemas.py, and repositories.py for a subapp. Use when adding SQLModel tables, Pydantic schemas, mixins, RepositoryBase, or table names. Do not use crud.py.
---

# SQLModel, schemas, repositories

Reference: `backend/src/apps/blog/posts/models.py`, `schemas.py`, `repositories.py`. Mixins: `backend/src/core/common/models.py`. Base repo: `backend/src/core/common/repository.py`.

## Models

- Field groups are small `*Base` classes inheriting `Base` (no `table=True`).
- The table class composes mixins + bases with `table=True`.
- `__tablename__ = "{app}_{resource}"` (e.g. `blog_post`, `system_users`).
- Optional: `UserTrackingMixin` for `created_by_user_id` / `updated_by_user_id`.

### Foreign keys: `*RelationshipBase`

Every column with `foreign_key=` lives in its own `Base` class, suffix `RelationshipBase`. Do not mix FKs into `*InfoBase` / `*ContentBase` / mixins.

FKs use the real table name, e.g. `foreign_key="system_users.id"`.

```python
class UserRelationshipBase(Base):
    tier_id: UUID | None = Field(
        default=None,
        foreign_key="system_tier.id",
        index=True,
        description="ID of the tier to which the user belongs",
    )
```

Same pattern: `PostRelationshipBase.user_id` → `system_users.id`; `RateLimitRelationshipBase.tier_id` → `system_tier.id`. See `backend/src/apps/system/users/models.py`, `backend/src/apps/blog/posts/models.py`, `backend/src/apps/system/rate_limits/models.py`.

### Column order (Alembic)

SQLModel / Alembic `--autogenerate` emits columns in the **reverse** of the `table=True` base list. Write bases reversed vs the desired DB order so `id` is first.

Desired DB order: `id` → domain `*Base` (content, then media) → FKs (`*RelationshipBase`) → timestamps → soft-delete. Generated `op.create_table` may put FKs at the end of the table (as `user_id` / `tier_id` do in current migrations).

Therefore list bases **reversed**: `SoftDeleteMixin`, `TimestampMixin`, `*RelationshipBase`, media/content bases, `UUIDMixin` last.

Wrong: putting `UUIDMixin` first in the class. Autogenerate then puts `id` last and timestamps / soft-delete first.

After generate, glance at `op.create_table` column order. Do not “fix” by listing mixins in reading order.

```python
class Post(
    SoftDeleteMixin,
    TimestampMixin,
    PostRelationshipBase,
    PostMediaBase,
    PostContentBase,
    UUIDMixin,
    table=True,
):
    __tablename__ = "blog_post"
```

After adding a table class, import it in `backend/src/core/db/__init__.py` and run Alembic (`.agents/skills/alembic/SKILL.md`).

## Schemas

Reuse the same `*Base` classes from `models.py`. Do not duplicate fields.

| Schema            | Role                                                                       |
| ----------------- | -------------------------------------------------------------------------- |
| `XRead`           | API response (id + timestamps; usually no soft-delete flags)               |
| `XCreate`         | Public body; `ConfigDict(extra="forbid")`                                  |
| `XCreateInternal` | Create + server-set fields (`user_id`, hash, …)                            |
| `XUpdate`         | PATCH; decorate with `@optional()` from `src._overrides.pydantic.optional` |
| `XUpdateInternal` | Update + `updated_at` (or tracking fields)                                 |
| `XDelete`         | Soft-delete payload (`SoftDeleteMixin`)                                    |

```python
class PostCreate(PostBase, PostMediaBase):
    model_config = ConfigDict(extra="forbid")

class PostCreateInternal(PostCreate, PostRelationshipBase):
    pass

@optional()
class PostUpdate(PostContentBase, PostMediaBase):
    model_config = ConfigDict(extra="forbid")
```

## Repositories

No `crud.py`. No `CRUDBase`. Type `RepositoryBase` and export a singleton:

```python
PostRepository = RepositoryBase[
    Post, PostCreateInternal, PostUpdate, PostUpdateInternal, PostDelete
]
post_repository = PostRepository(Post)
```

`RepositoryBase` already provides `get`, `get_multi`, `create`, `update`, `delete` (soft), `db_delete` (hard), filtering, and sorting. Subclass only for custom SQL.

Business rules stay in `services.py`, not here.
