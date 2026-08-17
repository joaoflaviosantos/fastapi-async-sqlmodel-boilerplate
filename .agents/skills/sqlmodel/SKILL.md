---
name: sqlmodel
description: Create or change models.py, schemas.py, and repositories.py for a subapp. Use when adding SQLModel tables, Pydantic schemas, mixins, RepositoryBase, or table names. Do not use crud.py.
---

# SQLModel, schemas, repositories

Follow `AGENTS.md`. This skill is the recipe for `models.py`, `schemas.py`, and `repositories.py`.

CRUD template: `.agents/examples/subapp/models.py`, `schemas.py`, `repositories.py`. Live FK/users table: `backend/src/apps/system/users/models.py`. Mixins: `backend/src/core/common/models.py`. Base repo: `backend/src/core/common/repository.py`.

## Models

- Field groups are small `*Base` classes inheriting `Base` (no `table=True`).
- The table class composes mixins + bases with `table=True`.
- `__tablename__ = "{app}_{resource}"` (e.g. `example_item`, `system_users`).
- Optional: `UserTrackingMixin` for `created_by_user_id` / `updated_by_user_id`.

### Foreign keys: `*RelationshipBase`

Every column with `foreign_key=` lives in its own `Base` class, suffix `RelationshipBase`. Do not mix FKs into `*InfoBase` / `*ContentBase` / mixins.

FKs use the real table name, e.g. `foreign_key="system_users.id"`.

```python
class ItemRelationshipBase(Base):
    user_id: UUID = Field(
        description="User ID associated with the item",
        foreign_key="system_users.id",
        index=True,
    )
```

Same pattern: `UserRelationshipBase.tier_id` → `system_tier.id`; `RateLimitRelationshipBase.tier_id` → `system_tier.id`. See `backend/src/apps/system/users/models.py`, `backend/src/apps/system/rate_limits/models.py`.

### Column order (Alembic)

SQLModel / Alembic `--autogenerate` emits columns in the **reverse** of the `table=True` base list. Write bases reversed vs the desired DB order so `id` is first.

Desired DB order: `id` → domain `*Base` (content, then media) → FKs (`*RelationshipBase`) → timestamps → soft-delete. Generated `op.create_table` may put FKs at the end of the table (as `user_id` / `tier_id` do in current migrations).

Therefore list bases **reversed**: `SoftDeleteMixin`, `TimestampMixin`, `*RelationshipBase`, media/content bases, `UUIDMixin` last.

Wrong: putting `UUIDMixin` first in the class. Autogenerate then puts `id` last and timestamps / soft-delete first.

After generate, glance at `op.create_table` column order. Do not “fix” by listing mixins in reading order.

```python
class Item(
    SoftDeleteMixin,
    TimestampMixin,
    ItemRelationshipBase,
    ItemMediaBase,
    ItemContentBase,
    UUIDMixin,
    table=True,
):
    __tablename__ = "example_item"
    __table_args__ = ({"comment": "Example item information"},)
```

After adding a table class, import it in `backend/src/core/db/__init__.py` and run Alembic (`.agents/skills/alembic/SKILL.md`). Do not import `.agents/examples/subapp/`.

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
class ItemCreate(ItemBase, ItemMediaBase):
    model_config = ConfigDict(extra="forbid")

class ItemCreateInternal(ItemCreate, ItemRelationshipBase):
    pass

@optional()
class ItemUpdate(ItemContentBase, ItemMediaBase):
    model_config = ConfigDict(extra="forbid")
```

## Repositories

No `crud.py`. No `CRUDBase`. Type `RepositoryBase` and export a singleton:

```python
ItemRepository = RepositoryBase[
    Item, ItemCreateInternal, ItemUpdate, ItemUpdateInternal, ItemDelete
]
item_repository = ItemRepository(Item)
```

`RepositoryBase` already provides `get`, `get_multi`, `create`, `update`, `delete` (soft), `db_delete` (hard), filtering, and sorting. Subclass only for custom SQL.

Business rules stay in `services.py`, not here.
