# Built-in Dependencies
import os
import re
import sys
import subprocess
from pathlib import Path

# Third-Party Dependencies
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport, Cookies
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

# Local Dependencies
from tests.helper import _get_token

_API_VERSION_FILE = re.compile(r"_v\d+\.py$")
_FORBIDDEN_TEST_SUBDIRS = frozenset({"unit", "integration"})
_TEST_SECRET_KEY = "pytest-secret-key-not-for-production"

_postgres: PostgresContainer | None = None
_redis: RedisContainer | None = None


class _NonPersistentCookies(Cookies):
    """Ignore Set-Cookie so the session-scoped client does not leak login cookies."""

    def extract_cookies(self, response) -> None:
        return


def _is_docker_available() -> bool:
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _patch_dummy_env() -> None:
    os.environ["POSTGRES_USER"] = "pytest"
    os.environ["POSTGRES_PASSWORD"] = "pytest"
    os.environ["POSTGRES_SERVER"] = "invalid.invalid"
    os.environ["POSTGRES_PORT"] = "1"
    os.environ["POSTGRES_DB"] = "pytest"
    os.environ["REDIS_CACHE_HOST"] = "invalid.invalid"
    os.environ["REDIS_CACHE_PORT"] = "1"
    os.environ["REDIS_CACHE_USERNAME"] = ""
    os.environ["REDIS_CACHE_PASSWORD"] = ""
    os.environ["REDIS_RATE_LIMIT_HOST"] = "invalid.invalid"
    os.environ["REDIS_RATE_LIMIT_PORT"] = "1"
    os.environ["REDIS_RATE_LIMIT_USERNAME"] = ""
    os.environ["REDIS_RATE_LIMIT_PASSWORD"] = ""
    os.environ["REDIS_BROKER_HOST"] = "invalid.invalid"
    os.environ["REDIS_BROKER_PORT"] = "1"
    os.environ["REDIS_BROKER_USERNAME"] = ""
    os.environ["REDIS_BROKER_PASSWORD"] = ""
    os.environ["SECRET_KEY"] = _TEST_SECRET_KEY
    os.environ["EMAIL_SENDER"] = "logger"
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DEFAULT_RATE_LIMIT_LIMIT"] = "10000"
    os.environ["DEFAULT_RATE_LIMIT_PERIOD"] = "3600"


def _patch_container_env(postgres: PostgresContainer, redis: RedisContainer) -> None:
    os.environ["POSTGRES_USER"] = postgres.username
    os.environ["POSTGRES_PASSWORD"] = postgres.password
    os.environ["POSTGRES_SERVER"] = postgres.get_container_host_ip()
    os.environ["POSTGRES_PORT"] = str(postgres.get_exposed_port(5432))
    os.environ["POSTGRES_DB"] = postgres.dbname

    redis_host = redis.get_container_host_ip()
    redis_port = str(redis.get_exposed_port(6379))
    os.environ["REDIS_CACHE_HOST"] = redis_host
    os.environ["REDIS_CACHE_PORT"] = redis_port
    os.environ["REDIS_CACHE_USERNAME"] = ""
    os.environ["REDIS_CACHE_PASSWORD"] = ""
    os.environ["REDIS_RATE_LIMIT_HOST"] = redis_host
    os.environ["REDIS_RATE_LIMIT_PORT"] = redis_port
    os.environ["REDIS_RATE_LIMIT_USERNAME"] = ""
    os.environ["REDIS_RATE_LIMIT_PASSWORD"] = ""
    os.environ["REDIS_BROKER_HOST"] = redis_host
    os.environ["REDIS_BROKER_PORT"] = redis_port
    os.environ["REDIS_BROKER_USERNAME"] = ""
    os.environ["REDIS_BROKER_PASSWORD"] = ""
    os.environ["SECRET_KEY"] = _TEST_SECRET_KEY
    os.environ["EMAIL_SENDER"] = "logger"
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DEFAULT_RATE_LIMIT_LIMIT"] = "10000"
    os.environ["DEFAULT_RATE_LIMIT_PERIOD"] = "3600"


def _markexpr_selects_integration(markexpr: str) -> bool:
    if not markexpr.strip():
        return True
    from _pytest.mark.expression import Expression

    expr = Expression.compile(markexpr)
    return bool(expr.evaluate(lambda name: name == "integration"))


def _arg_may_include_integration(arg: str) -> bool:
    file_part = arg.split("::", 1)[0]
    name = Path(file_part).name
    if name.endswith(".py"):
        return bool(_API_VERSION_FILE.search(name))
    return True


def _cli_args_need_integration(config: pytest.Config) -> bool:
    args = [str(a) for a in config.args]
    if not args:
        return True
    return any(_arg_may_include_integration(a) for a in args)


def _session_needs_integration(config: pytest.Config) -> bool:
    if getattr(config.option, "collectonly", False):
        return False
    markexpr = (getattr(config.option, "markexpr", None) or "").strip()
    if not _markexpr_selects_integration(markexpr):
        return False
    return _cli_args_need_integration(config)


def _start_containers() -> None:
    global _postgres, _redis

    if not _is_docker_available():
        hint = (
            "Please ensure Docker Desktop is installed and running."
            if sys.platform == "win32"
            else "Please ensure Docker is installed and the daemon is running."
        )
        pytest.exit(
            f"Docker is not available or not running. {hint} "
            f"Integration tests require Docker to spin up PostgreSQL and Redis test containers.",
            returncode=1,
        )

    os.environ["TESTCONTAINERS_RYUK_DISABLED"] = "true"
    postgres = PostgresContainer("pgvector/pgvector:0.8.0-pg17")
    redis = RedisContainer("redis:alpine")
    try:
        postgres.start()
        redis.start()
    except Exception:
        try:
            redis.stop()
        except Exception:
            pass
        try:
            postgres.stop()
        except Exception:
            pass
        raise

    _postgres = postgres
    _redis = redis
    _patch_container_env(postgres, redis)


def pytest_configure(config: pytest.Config) -> None:
    if _session_needs_integration(config):
        _start_containers()
    else:
        _patch_dummy_env()


def pytest_sessionfinish(session, exitstatus) -> None:
    if _redis is not None:
        _redis.stop()
    if _postgres is not None:
        _postgres.stop()


def _has_forbidden_test_subdir(path: Path) -> bool:
    parts = path.parts
    for index, part in enumerate(parts[:-1]):
        if part == "tests" and parts[index + 1] in _FORBIDDEN_TEST_SUBDIRS:
            return True
    return False


def pytest_collection_modifyitems(config: pytest.Config, items: list) -> None:
    violations: list[str] = []
    for item in items:
        path = Path(item.path)
        if _has_forbidden_test_subdir(path):
            violations.append(
                f"{item.nodeid}: tests must live directly under tests/ "
                f"(tests/unit/ and tests/integration/ are forbidden)"
            )
            continue

        marker_names = {marker.name for marker in item.iter_markers()}
        has_unit = "unit" in marker_names
        has_integration = "integration" in marker_names
        if has_unit == has_integration:
            violations.append(
                f"{item.nodeid}: every test must have exactly one of pytest.mark.unit "
                f"or pytest.mark.integration (set pytestmark on the module)"
            )
            continue

        versioned = bool(_API_VERSION_FILE.search(path.name))
        if has_integration and not versioned:
            violations.append(
                f"{item.nodeid}: integration tests must be named *_vN.py (got {path.name})"
            )
        if has_unit and versioned:
            violations.append(
                f"{item.nodeid}: unit tests must not use the API version suffix *_vN.py "
                f"(got {path.name})"
            )
        if "core" in path.parts and has_integration:
            violations.append(
                f"{item.nodeid}: tests under src/core/ must use pytest.mark.unit "
                f"(shared infrastructure is not HTTP)"
            )

    if violations:
        formatted = "\n".join(f"  - {line}" for line in violations)
        pytest.exit(
            "Test collection contract violated:\n" + formatted,
            returncode=2,
        )


@pytest.fixture
def settings():
    from src.core.config import settings as app_settings

    return app_settings


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient, settings) -> dict[str, str]:
    token = await _get_token(
        username=settings.USER_FIRST_ADMIN_USERNAME,
        password=settings.USER_FIRST_ADMIN_PASSWORD,
        client=client,
    )
    assert token.status_code == 200, token.text
    return {"Authorization": f"Bearer {token.json()['access_token']}"}


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def client():
    import redis.asyncio as aioredis
    from src.core.utils.alembic import run_alembic_migration_sync
    from src.core.utils import rate_limit
    from src.core.utils import cache
    from src.core.config import settings as app_settings
    from src.core.setup import run_seed_scripts
    from src.main import app

    run_alembic_migration_sync()
    await run_seed_scripts()

    cache.pool = aioredis.ConnectionPool.from_url(
        app_settings.REDIS_CACHE_URL, encoding="utf8", decode_responses=True
    )
    cache.client = aioredis.Redis.from_pool(cache.pool)  # type: ignore

    rate_limit.pool = aioredis.ConnectionPool.from_url(
        app_settings.REDIS_RATE_LIMIT_URL, encoding="utf8", decode_responses=True
    )
    rate_limit.client = aioredis.Redis.from_pool(rate_limit.pool)  # type: ignore

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        cookies=_NonPersistentCookies(),
    ) as ac:
        yield ac

    try:
        await cache.client.aclose()  # type: ignore
    except Exception:
        pass

    try:
        await rate_limit.client.aclose()  # type: ignore
    except Exception:
        pass
