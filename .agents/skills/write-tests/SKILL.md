---
name: write-tests
description: Write colocated tests in apps/<app>/<subapp>/tests/ (API test_v1.py and unit tests) and infra unit tests in src/core/tests/. Use when adding or changing HTTP endpoints, deps, or subapp tests.
---

# Subapp tests

Follow `AGENTS.md`. This skill is the recipe for colocated tests under `apps/<app>/<subapp>/tests/` and infra tests under `src/core/tests/`.

CRUD template: `.agents/examples/subapp/tests/test_v1.py`. Service unit template: `.agents/examples/subapp/tests/test_item_service.py`. Live auth/client usage: `backend/src/apps/system/users/tests/test_v1.py`. Live service unit: `backend/src/apps/system/users/tests/test_user_service.py`. Unit-test example (deps): `backend/src/apps/system/auth/tests/test_user_context_db.py`. Infra unit: `backend/src/core/tests/`. Fixtures: `backend/tests/conftest.py` (`client`, `admin_headers`, `settings`). Helpers: `backend/tests/helper.py`. Plugin: `backend/conftest.py` (`pytest_plugins = ["tests.conftest"]`). `src/conftest.py` is empty (no nested plugins). Guide: `docs/testing-guide.md`.

## Location

Domain tests live next to the subapp: `backend/src/apps/<app>/<subapp>/tests/` (flat — no `unit/` or `integration/` folders).

```
tests/
  test_v1.py                 # HTTP API v1; pytestmark = integration
  test_<topic>_v1.py         # extra HTTP file only if needed
  test_<resource>_service.py # service unit tests; pytestmark = unit
  test_<subject>.py          # other isolated unit tests; pytestmark = unit
```

Shared-infrastructure unit tests live in `backend/src/core/tests/` (always `pytestmark = pytest.mark.unit`; never HTTP/`client`).

**Do not** create test files in `backend/tests/`. That directory only holds:

- `conftest.py` — suite fixtures (lazy Testcontainers + `client` + `admin_headers` + `settings`)
- `helper.py` — login and disposable-user helpers

Pytest collects `src/` (`testpaths = src` in `backend/pytest.ini`). The plugin is `backend/conftest.py`. The example tree is a mold — do not collect it.

### Integration (`test_v1.py`)

HTTP tests using `AsyncClient` / fixture `client`. File name **must** end with `_v1.py` (or `_v2.py` when that API version exists). Set on the module:

```python
pytestmark = pytest.mark.integration
```

Do **not** put `@pytest.mark.integration` on every function. Do **not** use `@pytest.mark.asyncio` (`asyncio_mode = auto`). A subapp that only has HTTP needs only `test_v1.py` — do not add an empty unit file.

### Unit tests

Isolated tests of deps/services with no HTTP and no Docker. File name must **not** use `*_vN.py`.

```python
pytestmark = pytest.mark.unit
```

Service tests construct the service with `AsyncMock` repositories. They must not request `client`. Cover **every domain `raise`** (assert the exception; `assert_not_awaited` on the write when that applies) **and a happy path** for each public method (assert the return value and that the write was awaited). `except IntegrityError` / `except Exception` each get their own test. Listings with no `raise` need only a happy path with a mocked paginated dict. Celery services mock `apply_async` / `AsyncResult` / `celery_app` — never hit a real broker. Do not stop at the first `if`.

## How to write HTTP tests

- Each test creates the rows it needs. **No** module-level `global` IDs and **no** dependence on file order. A single `pytest ...::test_get_item` must pass.
- Unique payloads (`uuid4()` in name/email/title) so session-scoped DB rows do not collide.
- Login with fixture `admin_headers` or `_get_token` / `_create_regular_user` from `tests.helper`.
- Do **not** `from src.core.config import settings` at the top of a `test_*.py`. Use the `settings` fixture.
- Do **not** mutate `client.cookies` / `client.headers`. Pass cookies on the request.
- Do **not** `flushdb` on the shared Redis. Delete only the keys this test created (`ratelimit:{user_id}:{sanitized_path}:*`).
- Cover create / read / update / soft-delete (and `/db` hard delete if the router has it). Include **401** (no token) and **403** (`/db` as a regular user) as in the mold. Error JSON is RFC 9457: assert `problem_body(...)` from `src.core.exceptions.problem`.
- On GET, assert `updated_by_user_name` when the resource uses tracking.
- **Do not permanently mutate core seed data** (default tier, first admin, system superuser).

```python
pytestmark = pytest.mark.integration


async def test_create_item(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    created = await _create_item(client, admin_headers)
    assert created["id"]
```

## How to write service unit tests

Copy `.agents/examples/subapp/tests/test_item_service.py`: each `raise` plus the matching happy path (create / get / list / update / soft delete / hard delete, including `IntegrityError` → Forbidden and generic `Exception` → Internal).

```python
pytestmark = pytest.mark.unit


async def test_get_item_raises_when_missing() -> None:
    item_repo = AsyncMock()
    item_repo.get_single_with_main_relations.return_value = None
    service = ItemService(item_repo=item_repo)
    with pytest.raises(NotFoundException):
        await service.get_item(db=object(), item_id=uuid4())


async def test_get_item_returns_row() -> None:
    item_id = uuid4()
    row = {"id": item_id, "title": "Example item"}
    item_repo = AsyncMock()
    item_repo.get_single_with_main_relations.return_value = row
    service = ItemService(item_repo=item_repo)
    result = await service.get_item(db=object(), item_id=item_id)
    assert result == row
```

## Run (from `backend/`)

```bash
poetry run pytest -v
poetry run pytest -m unit -v
poetry run pytest -m integration -v
poetry run pytest -v --cov --cov-report=term-missing --cov-fail-under=80
poetry run mypy src
poetry run ruff format --check .
poetry run ruff check src
poetry run pytest src/apps/<app>/<subapp>/tests/ -v
poetry run pytest src/apps/<app>/<subapp>/tests/test_v1.py -v
poetry run pytest src/core/tests/ -v
```

Docker / Testcontainers is required only for integration (and for `pytest -v` with no `-m`). `pytest -m unit` must pass without Docker. Pre-commit runs `pytest -m unit -v` only (no coverage). Coverage (`--cov-fail-under=80`) and HTTP tests run in GitHub Actions job `test` and locally when Docker is up. CI job `checks` runs `ruff format --check .`, `ruff check src`, `mypy src`, and `pytest -m unit -v`.

Do not document `poetry run pytest tests/` as the full suite. Do not put `--cov` in `pytest.ini` `addopts`.
