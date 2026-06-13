# Built-in Dependencies
import os

# Third-Party Dependencies
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from testcontainers.postgres import PostgresContainer

# ===========================================================================
# 1. TEST ENVIRONMENT INITIALIZATION
# ===========================================================================
# Start the PostgreSQL container eagerly at module import time.
# We do this here so that the database environment variables are patched
# *before* `src.core.config.settings` and the SQLAlchemy engine are imported.
# This prevents the application from initializing the engine with the wrong URL.

# Disable the Ryuk (Reaper) container — it tries to bind port 8080 and fails
# on Windows/Docker Desktop. Cleanup is instead handled in `pytest_sessionfinish`.
os.environ["TESTCONTAINERS_RYUK_DISABLED"] = "true"

_postgres = PostgresContainer("postgres:16-alpine")
_postgres.start()

# Patch the application's environment variables with the testcontainer's details
os.environ["POSTGRES_USER"] = _postgres.username
os.environ["POSTGRES_PASSWORD"] = _postgres.password
os.environ["POSTGRES_SERVER"] = _postgres.get_container_host_ip()
os.environ["POSTGRES_PORT"] = str(_postgres.get_exposed_port(5432))
os.environ["POSTGRES_DB"] = _postgres.dbname
os.environ["ENVIRONMENT"] = "test"


def pytest_sessionfinish(session, exitstatus):
    """
    Hook function called by pytest after the entire test session completes.
    Stops the PostgreSQL container to ensure proper cleanup.
    """
    _postgres.stop()


# ===========================================================================
# 2. TEST FIXTURES
# ===========================================================================
@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def client():
    """
    Pytest fixture to provide an async HTTPX AsyncClient for testing.

    This fixture ensures that the application has a fully functioning environment
    (Database and Cache) before yielding the client to the tests.

    The 'session' scope guarantees this setup is run exactly once for all tests,
    saving time and preserving the state (like sequential IDs) across tests.
    """

    # -----------------------------------------------------------------------
    # STAGE 1: Lazy Imports
    # -----------------------------------------------------------------------
    # We import the application modules only here, inside the function.
    # This ensures that the database environment variables (configured above
    # by Testcontainers) are already injected into `os.environ` before
    # `settings` and the SQLAlchemy `session` are loaded for the first time.
    from src.core.setup import create_tables, run_seed_scripts
    from src.core.utils import cache, rate_limit
    from src.core.config import settings
    from src.main import app
    import redis.asyncio as aioredis

    # -----------------------------------------------------------------------
    # STAGE 2: Initialization (STARTUP)
    # -----------------------------------------------------------------------
    # Since we are not using the standard FastAPI Lifespan context in our
    # tests (to prevent conflicts regarding the closure of the event loop
    # by pytest-asyncio), we must manually replicate the startup process here.

    # 2.1. Create Database Schema
    # Testcontainers boots a completely empty PostgreSQL database.
    # The command below creates all tables and schemas defined by SQLModel.
    await create_tables()

    # 2.2. Run Seed Scripts
    # Populates the database with the minimum data required by the system
    # to operate, such as the 'Default' Tier, the Admin Superuser, and the first Post.
    await run_seed_scripts()

    # 2.3. Configure Redis Connection Pools
    # The system utilizes middlewares and dependencies (like Rate Limiting and Caching)
    # that require Redis pools to exist in the application's memory. Here we
    # initialize them based on the environment configuration (local/mocked context).
    cache.pool = aioredis.ConnectionPool.from_url(
        settings.REDIS_CACHE_URL, encoding="utf8", decode_responses=True
    )
    cache.client = aioredis.Redis.from_pool(cache.pool)  # type: ignore

    rate_limit.pool = aioredis.ConnectionPool.from_url(
        settings.REDIS_RATE_LIMIT_URL, encoding="utf8", decode_responses=True
    )
    rate_limit.client = aioredis.Redis.from_pool(rate_limit.pool)  # type: ignore

    # -----------------------------------------------------------------------
    # STAGE 3: Test Execution (YIELD)
    # -----------------------------------------------------------------------
    # Creates the AsyncClient using the ASGITransport, which sends requests
    # directly to the instance of our FastAPI application (`app`) in memory,
    # without needing to boot a real web server (like Uvicorn) on HTTP ports.
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    # -----------------------------------------------------------------------
    # STAGE 4: Finalization (SHUTDOWN)
    # -----------------------------------------------------------------------
    # After all tests in the session have finished running, we gracefully close
    # the active Redis connections. The database (Testcontainers) will be
    # torn down by the `pytest_sessionfinish` function declared above.
    try:
        await cache.client.aclose()  # type: ignore
    except Exception:
        pass

    try:
        await rate_limit.client.aclose()  # type: ignore
    except Exception:
        pass
