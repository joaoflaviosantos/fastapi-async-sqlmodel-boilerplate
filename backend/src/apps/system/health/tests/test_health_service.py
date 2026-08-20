# Built-in Dependencies
from unittest.mock import AsyncMock, MagicMock, patch

# Third-Party Dependencies
import pytest

# Local Dependencies
from src.apps.system.health.schemas import HealthRead, ReadyRead
from src.apps.system.health.services import HealthService
from src.core.exceptions.http_exceptions import ServiceUnavailableException

pytestmark = pytest.mark.unit


async def test_liveness_returns_ok() -> None:
    result = await HealthService().liveness()

    assert result == HealthRead(status="ok")


async def test_readiness_returns_ok() -> None:
    db = AsyncMock()
    db.exec = AsyncMock(return_value=MagicMock(one=MagicMock(return_value=(1,))))
    redis_client = AsyncMock()
    redis_client.ping = AsyncMock(return_value=True)

    with patch("src.apps.system.health.services.cache") as cache_module:
        cache_module.client = redis_client
        result = await HealthService().readiness(db=db)

    assert result == ReadyRead(status="ok", database="ok", redis="ok")
    db.exec.assert_awaited_once()
    redis_client.ping.assert_awaited_once()


async def test_readiness_raises_when_database_fails() -> None:
    db = AsyncMock()
    db.exec = AsyncMock(side_effect=RuntimeError("db down"))
    redis_client = AsyncMock()
    redis_client.ping = AsyncMock(return_value=True)

    with patch("src.apps.system.health.services.cache") as cache_module:
        cache_module.client = redis_client
        with pytest.raises(ServiceUnavailableException):
            await HealthService().readiness(db=db)

    redis_client.ping.assert_awaited_once()


async def test_readiness_raises_when_redis_client_missing() -> None:
    db = AsyncMock()
    db.exec = AsyncMock(return_value=MagicMock(one=MagicMock(return_value=(1,))))

    with patch("src.apps.system.health.services.cache") as cache_module:
        cache_module.client = None
        with pytest.raises(ServiceUnavailableException):
            await HealthService().readiness(db=db)


async def test_readiness_raises_when_redis_ping_fails() -> None:
    db = AsyncMock()
    db.exec = AsyncMock(return_value=MagicMock(one=MagicMock(return_value=(1,))))
    redis_client = AsyncMock()
    redis_client.ping = AsyncMock(side_effect=RuntimeError("redis down"))

    with patch("src.apps.system.health.services.cache") as cache_module:
        cache_module.client = redis_client
        with pytest.raises(ServiceUnavailableException):
            await HealthService().readiness(db=db)
