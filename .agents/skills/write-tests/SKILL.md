---
name: write-tests
description: Write colocated async API tests in apps/<app>/<subapp>/tests/test_v1.py using the httpx client fixture. Use when adding or changing HTTP endpoints or subapp tests.
---

# Subapp API tests

Follow `AGENTS.md`. This skill is the recipe for colocated `tests/test_v1.py`.

CRUD template: `.agents/examples/subapp/tests/test_v1.py`. Live auth/client usage: `backend/src/apps/system/users/tests/test_v1.py`. Fixtures: `backend/tests/conftest.py` (`client`). Helpers: `backend/tests/helper.py`. Guide: `docs/testing-guide.md`.

## Location

Put tests **inside the subapp**: `backend/src/apps/<app>/<subapp>/tests/test_v1.py`. Do not mirror them under `backend/tests/apps/`. The example tree is a mold — do not collect it with pytest.

## How to write them

- `@pytest.mark.asyncio` (mode is auto in `pytest.ini`).
- Use the session-scoped `client: AsyncClient` fixture (ASGI + Testcontainers Postgres/Redis).
- Login with `_get_token` from `tests.helper`; admin credentials from `settings.USER_FIRST_ADMIN_*`.
- Hit real paths: `/api/v1/example/items/...` in the template, `/api/v1/system/users/me/` for the current user.
- Cover create / read / update / soft-delete (and `/db` hard delete if the router has it).
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
        url=f"/api/v1/example/items/user/{user_id}",
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
poetry run pytest -v
```

Filter to one subapp:

```bash
poetry run pytest src/apps/<app>/<subapp>/tests/test_v1.py -v
```
