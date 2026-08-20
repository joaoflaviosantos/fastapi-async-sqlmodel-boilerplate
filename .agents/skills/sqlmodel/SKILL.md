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
- **One** `table=True` class per `models.py`. A second table means a second subapp.
- The example includes `UserTrackingMixin` (`created_by_user_id` / `updated_by_user_id`). It is the exception that carries `foreign_key=` outside a `*RelationshipBase`. To omit tracking, follow `.agents/examples/README.md` (Resource without user tracking).

### Foreign keys: `*RelationshipBase`

Every column with `foreign_key=` lives in its own `Base` class, suffix `RelationshipBase`. Do not mix FKs into `*InfoBase` / `*ContentBase` / mixins (except `UserTrackingMixin`, above).

FKs use the real table name, e.g. `foreign_key="system_tier.id"`. The example's `relation_example_id` → `example_relation.id` is a **placeholder**: rename it or drop `ItemRelationshipBase` when copying (see `.agents/examples/README.md`).

```python
class ItemRelationshipBase(Base):
    relation_example_id: UUID | None = Field(
        default=None,
        foreign_key="example_relation.id",
        index=True,
        description="ID of the related record",
    )
```

Same live pattern: `UserRelationshipBase.tier_id` → `system_tier.id`; `RateLimitRelationshipBase.tier_id` → `system_tier.id`. See `backend/src/apps/system/users/models.py`, `backend/src/apps/system/rate_limits/models.py`.

### Many-to-many (`_assoc`)

M2M lives in its own subapp named `<a>_<b>_assoc`, with `__tablename__ = "{app}_{a}_{b}_assoc"`. Both FKs sit in one `*RelationshipBase` as a composed primary key. Do **not** add `UUIDMixin`, `TimestampMixin`, `SoftDeleteMixin`, or `UserTrackingMixin`.

```python
class ItemTagAssocRelationshipBase(Base):
    item_id: UUID = Field(foreign_key="example_item.id", primary_key=True)
    tag_id: UUID = Field(foreign_key="example_tag.id", primary_key=True)


class ItemTagAssoc(ItemTagAssocRelationshipBase, table=True):
    __tablename__ = "example_item_tag_assoc"
```

No HTTP surface: `models.py`, `schemas.py`, `repositories.py`, `services.py`, `__init__.py` only — no `routers/`, `deps.py`, or `tests/`. Other services and tasks drive it. Still import the `table=True` class in `backend/src/core/db/__init__.py`. Extra composite indexes go in `__table_args__` when a query needs them.

### Column order (Alembic)

SQLModel / Alembic `--autogenerate` emits columns in the **reverse** of the `table=True` base list. Write bases reversed vs the desired DB order so `id` is first.

Desired DB order: `id` → domain `*Base` (content, then media) → FKs (`*RelationshipBase`) → timestamps → tracking → soft-delete. Generated `op.create_table` may put FKs at the end of the table (as `tier_id` does in current migrations).

Therefore list bases **reversed**: `SoftDeleteMixin`, `UserTrackingMixin`, `TimestampMixin`, `*RelationshipBase`, media/content bases, `UUIDMixin` last.

Wrong: putting `UUIDMixin` first in the class. Autogenerate then puts `id` last and timestamps / soft-delete first.

After generate, glance at `op.create_table` column order. Do not “fix” by listing mixins in reading order.

```python
class Item(
    SoftDeleteMixin,
    UserTrackingMixin,
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
| `XCreateInternal` | Create + server-set fields (`UserTrackingMixin`, hash, …)                  |
| `XUpdate`         | PATCH; decorate with `@optional()` from `src._overrides.pydantic.optional` |
| `XUpdateInternal` | Update + `updated_at` (author comes from the session, not this schema)     |
| `XDelete`         | Soft-delete payload (`SoftDeleteMixin`)                                    |

```python
class ItemCreate(ItemBase, ItemMediaBase, ItemRelationshipBase):
    model_config = ConfigDict(extra="forbid")

class ItemCreateInternal(ItemCreate, UserTrackingMixin):
    pass

@optional()
class ItemUpdate(ItemContentBase, ItemMediaBase):
    model_config = ConfigDict(extra="forbid")
```

`XRead` on the example adds `updated_by_user_name` / `_email` / `_profile_image_url` with `default=None` so a plain `get` (no join) still validates.

## Repositories

No `crud.py`. No `CRUDBase`. Two levels:

**Thin alias** — resource with no related payload:

```python
ItemRepository = RepositoryBase[
    Item, ItemCreateInternal, ItemUpdate, ItemUpdateInternal, ItemDelete
]
item_repository = ItemRepository(Item)
```

**Subclass** — related data (the example default). Implement `get_single_with_main_relations` and `get_multi_with_main_relations`. Put the `select` + `outerjoin` in `_stmt_with_main_relations`; the two getters reuse it. Copy `.agents/examples/subapp/repositories.py`. The `outerjoin` on `updated_by_user_id` is required: `UserTrackingMixin` leaves two FKs to `system_users`, and `RepositoryBase` autodetect would pick `created_by_user_id`.

`RepositoryBase` already provides `get`, `get_multi`, `create`, `update`, `delete` (soft), `db_delete` (hard), filtering, and sorting. Use `get` / `get_multi` for existence checks; use `*_with_main_relations` for API responses. Custom SQL must call `self.exclude_deleted(stmt)` after joins unless the query needs soft-deleted rows.

### Nested collections (`include_*`)

When a GET should embed children from another subapp, add a flag on `get_single_with_main_relations` and inject the list. Declare the field on `XRead` with a forward ref, import the child schema at the **end** of `schemas.py`, then `model_rebuild()`:

```python
async def get_single_with_main_relations(
    self, db: AsyncSession, include_children: bool = False, **kwargs: Any
) -> Dict[str, Any] | None:
    ...
    if include_children:
        children = await other_repository.get_multi_with_main_relations(
            db=db, offset=0, limit=1000, parent_id=item_id
        )
        data["children"] = children.get("data", [])
    return data
```

```python
class ItemRead(...):
    children: Optional[List["ChildRead"]] = Field(default=None)

# end of schemas.py
from src.apps.example.children.schemas import ChildRead  # noqa: E402

ItemRead.model_rebuild()
```

Do not add this to the example tree (one subapp only). Copy the snippet when a second resource exists.

Business rules stay in `services.py`, not here.
