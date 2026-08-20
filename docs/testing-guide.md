# Testing Guide

## Overview

The suite is fully asynchronous (`pytest-asyncio`, `asyncio_mode = auto`). Pytest collects tests natively from `backend/src/` (`testpaths = src`, `--import-mode=importlib`): domain tests under `apps/<app>/<subapp>/tests/` and infra unit tests under `core/tests/`. Plugin: `backend/conftest.py` (`pytest_plugins = ["tests.conftest"]`). `src/conftest.py` is empty (no nested plugins). There is no aggregator file.

Classification is **explicit** on each test module:

```python
pytestmark = pytest.mark.integration  # HTTP; file must be named *_vN.py
pytestmark = pytest.mark.unit         # isolated; no *_vN.py suffix
```

Markers come from `pytestmark`, not from folders. Do not create `tests/unit/` or `tests/integration/`. Do not put `test_*.py` in `backend/tests/` (that directory is only `conftest.py` and `helper.py`).

HTTP tests use a session-scoped `httpx.AsyncClient` against Testcontainers PostgreSQL (pgvector) and Redis. Unit tests must not need Docker.

## Prerequisites

- **Poetry** and the backend virtualenv (`cd backend && poetry install`).
- **Docker** only for integration (or a full `pytest -v` with no `-m`): Docker Desktop or Engine must be running so Testcontainers can start Postgres and Redis.

## Running Tests

From the `backend` directory:

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

From the repository root, the same commands are available under **Project Tools**: `python setup.py tools` (or `python3 setup.py` → option 2).

`pytest -m unit` is what pre-commit runs. It must pass without Docker and without `--cov`.

The coverage gate (`--cov-fail-under=80`) applies only to the **full** suite. Do not put `--cov` in `pytest.ini` `addopts`. Config lives in `[tool.coverage.*]` in `pyproject.toml` (`source = ["src"]`; tests, `src/conftest.py`, and Alembic revisions are omitted).

Do not use `poetry run pytest tests/` as the full suite. That directory has no `test_*.py`.

Without Docker, requesting integration still **aborts** (`pytest.exit`). That is intentional: a green commit must not skip HTTP by accident.

## Writing Tests

- Domain tests live next to the subapp: `src/apps/<app>/<subapp>/tests/`. Infra unit tests live in `src/core/tests/` (always `pytestmark = unit`).
- HTTP: `test_v1.py` (and `test_v2.py` when that API exists). Each test creates its own rows (`uuid4()` in unique fields). No module-level `global` IDs, no file-order coupling.
- Service unit: `test_<resource>_service.py` with `AsyncMock` repositories (see `.agents/examples/subapp/tests/test_item_service.py`). Cover every domain `raise` and a happy path per public method — not only the first `if`.
- Fixtures: `client` (session, HTTP only), `admin_headers` (function), `settings` (lazy import — do not import `src.core.config.settings` at the top of a test module).
- Do not mutate `client.cookies`. The session cookie jar ignores `Set-Cookie` so login does not leak across tests. Do not `flushdb` the shared Redis.
- Cover 401 (missing token) and 403 (`/db` as a non-superuser) in addition to the happy-path CRUD. HTTP errors are RFC 9457 Problem Details: assert `problem_body(...)` from `src.core.exceptions.problem` (not FastAPI's `{"detail": ...}`).
- Tests share one DB for the run. **Do not permanently mutate core seed data** (default tier, first admin, system superuser). Rate-limit HTTP tests must use a disposable tier.

The mold `.agents/examples/subapp/tests/` is not collected.

## Typing

From `backend/`:

```bash
poetry run mypy src
```

`backend/mypy.ini` sets `disallow_untyped_defs` and `check_untyped_defs` for `src/` (`apps/`, `core/`, `_overrides/`), with the SQLAlchemy mypy plugin. Tests and Alembic revisions are excluded. This is not `mypy --strict`. SQLModel/SQLAlchemy stub mismatches (`Field()`, `exec()`, `Row["col"]`, `ConfigDict`) stay listed in `disable_error_code` with a comment — `var-annotated` is left on. `_overrides/pydantic/optional.py` is ignored as a whole (`create_model`).

## Continuous Integration

[`.github/workflows/tests.yml`](../.github/workflows/tests.yml) runs on push/PR:

- **checks** (no Docker): `ruff format --check .`, `ruff check src`, `mypy src`, `pytest -m unit -v`
- **test** (Testcontainers): `pytest -v --cov --cov-report=term-missing --cov-fail-under=80`

Dummy `SECRET_KEY` and broker settings come from the pytest plugin — CI does not need repository secrets. Dependabot updates pip (`/backend`) and GitHub Actions weekly.

---

[Back to backend README](../backend/README.md)
