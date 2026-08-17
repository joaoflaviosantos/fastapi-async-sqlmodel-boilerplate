---
name: alembic
description: Register SQLModel tables for autogenerate and run Alembic from backend/. Use when adding or changing table=True models, creating revisions, or applying upgrade/downgrade. Single migration tree.
---

# Alembic

Guide: `docs/database-migration-guide.md`. Env loads models via `from src.core.db import *`.

## 1. Register the model

Every `table=True` class must be imported in `backend/src/core/db/__init__.py`:

```python
from src.apps.blog.posts.models import Post
```

If this import is missing, `alembic revision --autogenerate` will not see the table.

There is **one** migration tree (`backend/src/migrations/`). No separate shared/tenant trees.

## 2. Generate and apply (from `backend/`)

```bash
cd backend
poetry run alembic revision --autogenerate -m "add blog_comment"
poetry run alembic upgrade head
```

Optional: `poetry run alembic downgrade -1`.

Review the new file under `backend/src/migrations/versions/` before applying. Autogenerate misses comments, renames (shows as drop+create), some defaults, and some constraint edits — add those by hand.

## 3. Checklist

1. Model exists with `__tablename__` and mixins as needed.
2. Import in `core/db/__init__.py`.
3. Autogenerate, read the revision, upgrade.
4. Commit the revision file.

## Do not

- Do not require `ENVIRONMENT=migration` (that is not how this repo gates Alembic).
- Do not add a second Alembic env for “tenants”.
- Do not use `SQLModel.metadata.create_all` for schema changes in this project.
