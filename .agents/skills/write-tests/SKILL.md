---
name: write-tests
description: Write colocated tests in apps/<app>/<subapp>/tests/ (API test_v1.py and unit tests). Use when adding or changing HTTP endpoints, deps, or subapp tests.
---

# Subapp tests

Follow `AGENTS.md`. This skill is the recipe for colocated tests under `apps/<app>/<subapp>/tests/`.

CRUD template: `.agents/examples/subapp/tests/test_v1.py`. Live auth/client usage: `backend/src/apps/system/users/tests/test_v1.py`. Unit-test example: `backend/src/apps/system/auth/tests/test_user_context_db.py`. Fixtures: `backend/tests/conftest.py` (`client`). Helpers: `backend/tests/helper.py`. Guide: `docs/testing-guide.md`.

## Location

Put **all** tests inside the subapp: `backend/src/apps/<app>/<subapp>/tests/`. That includes HTTP integration (`test_v1.py`) **and** unit tests of deps/services (e.g. the `async_get_user_context_db` contract).

**Do not** create test files in `backend/tests/`. That directory only holds:

- `conftest.py` — suite fixtures (Testcontainers + `client`)
- `helper.py` — login helpers
- `test_main.py` — aggregator (star-imports)

The example tree is a mold — do not collect it with pytest.

### Integration (`test_v1.py`)

`test_v1.py` alone does **not** need a `conftest.py` in the subapp. The suite picks it up via star-import in `backend/tests/test_main.py` under `# Integration tests imports (V1 routes)` and uses `backend/tests/conftest.py`.

### Unit tests

When the subapp gains tests that are not only `test_v1.py`, add `tests/conftest.py` in that subapp with exactly:

```python
pytest_plugins = ["tests.conftest"]
```

That loads the suite fixtures (`client`, Testcontainers) if pytest is invoked on the subapp folder. Do not add this file to subapps that only have `test_v1.py`.

Star-import the unit module in `backend/tests/test_main.py` **under** `# Unit tests imports`. Without that, `poetry run pytest tests/` will not collect it.

```python
# Unit tests imports
from src.apps.system.auth.tests.test_user_context_db import *

# Integration tests imports (V1 routes)
from src.apps.system.auth.tests.test_v1 import *
```

## How to write them

- `@pytest.mark.asyncio` (mode is auto in `pytest.ini`).
- Use the session-scoped `client: AsyncClient` fixture (ASGI + Testcontainers Postgres/Redis).
- Login with `_get_token` from `tests.helper`; admin credentials from `settings.USER_FIRST_ADMIN_*`.
- Hit real paths: `/api/v1/example/items` and `/api/v1/example/items/{item_id}` in the template, `/api/v1/system/users/me/` for the current user.
- Cover create / read / update / soft-delete (and `/db` hard delete if the router has it). On GET, assert `updated_by_user_name` when the resource uses tracking.
- Docker must be running (testcontainers).

```python
@pytest.mark.asyncio
async def test_create_item(client: AsyncClient) -> None:
    token = await _get_token(
        username=settings.USER_FIRST_ADMIN_USERNAME,
        password=settings.USER_FIRST_ADMIN_PASSWORD,
        client=client,
    )
    response = await client.post(
        url="/api/v1/example/items",
        json=test_item,
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )
    assert response.status_code == 201
```

Prefer independent tests (each test creates what it needs). The example `test_v1.py` uses module-level `global`s and file order — keep that pattern only when copying that file.

## Constraints

- Tests share one DB session for the run. **Do not permanently mutate core seed data** (default tier, first admin, system superuser).
- Prefer creating disposable rows and asserting on those.

## Run (from `backend/`)

```bash
poetry run pytest tests/ -v
```

Filter to one subapp:

```bash
poetry run pytest src/apps/<app>/<subapp>/tests/test_v1.py -v
```
