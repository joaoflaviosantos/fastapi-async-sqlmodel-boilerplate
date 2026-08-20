# Built-in Dependencies
from unittest.mock import AsyncMock, MagicMock, patch

# Third-Party Dependencies
import pytest

# Local Dependencies
from src.apps.system.tasks.tasks import _check_application_health

pytestmark = pytest.mark.unit

_TASKS = "src.apps.system.tasks.tasks"


def _ok_response() -> MagicMock:
    response = MagicMock()
    response.status_code = 200
    response.raise_for_status = MagicMock()
    return response


def _healthy_session() -> AsyncMock:
    session = AsyncMock()
    result = MagicMock()
    result.scalar.return_value = 1
    session.exec = AsyncMock(return_value=result)
    cm = AsyncMock()
    cm.__aenter__.return_value = session
    cm.__aexit__.return_value = False
    return cm


def _healthy_redis() -> AsyncMock:
    redis_client = AsyncMock()
    redis_client.ping = AsyncMock(return_value=True)
    redis_client.aclose = AsyncMock()
    return redis_client


def _http_client(get_side_effect: list[object]) -> AsyncMock:
    client = AsyncMock()
    client.get = AsyncMock(side_effect=get_side_effect)
    client.__aenter__.return_value = client
    client.__aexit__.return_value = False
    return client


def _probe_urls(settings) -> tuple[str, str]:
    return f"{settings.API_BASE_URL}/health", f"{settings.API_BASE_URL}/ready"


def _assert_probe_urls(http_client: AsyncMock, settings) -> None:
    liveness_url, readiness_url = _probe_urls(settings)
    assert http_client.get.await_count == 2
    assert http_client.get.await_args_list[0].args[0] == liveness_url
    assert http_client.get.await_args_list[1].args[0] == readiness_url
    assert all("queue-health" not in call.args[0] for call in http_client.get.await_args_list)


async def test_check_application_health_returns_all_healthy(settings) -> None:
    live = _ok_response()
    ready = _ok_response()
    http_client = _http_client([live, ready])

    with (
        patch(f"{_TASKS}.local_session", return_value=_healthy_session()),
        patch(f"{_TASKS}.aioredis.from_url", return_value=_healthy_redis()),
        patch(f"{_TASKS}.httpx.AsyncClient", return_value=http_client),
    ):
        result = await _check_application_health()

    assert result["database"] == "healthy"
    assert result["redis"] == "healthy"
    assert result["api"] == "healthy"
    assert result["ready"] == "healthy"
    live.raise_for_status.assert_called_once()
    ready.raise_for_status.assert_called_once()
    _assert_probe_urls(http_client, settings)


async def test_check_application_health_liveness_failure_still_checks_readiness(
    settings,
) -> None:
    ready = _ok_response()
    http_client = _http_client([RuntimeError("liveness down"), ready])

    with (
        patch(f"{_TASKS}.local_session", return_value=_healthy_session()),
        patch(f"{_TASKS}.aioredis.from_url", return_value=_healthy_redis()),
        patch(f"{_TASKS}.httpx.AsyncClient", return_value=http_client),
    ):
        result = await _check_application_health()

    assert result["api"] == "unhealthy"
    assert result["ready"] == "healthy"
    ready.raise_for_status.assert_called_once()
    _assert_probe_urls(http_client, settings)


async def test_check_application_health_readiness_failure_marks_ready_unhealthy(
    settings,
) -> None:
    live = _ok_response()
    http_client = _http_client([live, RuntimeError("readiness down")])

    with (
        patch(f"{_TASKS}.local_session", return_value=_healthy_session()),
        patch(f"{_TASKS}.aioredis.from_url", return_value=_healthy_redis()),
        patch(f"{_TASKS}.httpx.AsyncClient", return_value=http_client),
    ):
        result = await _check_application_health()

    assert result["api"] == "healthy"
    assert result["ready"] == "unhealthy"
    live.raise_for_status.assert_called_once()
    _assert_probe_urls(http_client, settings)


async def test_check_application_health_marks_database_unhealthy_on_exception(
    settings,
) -> None:
    session_cm = AsyncMock()
    session_cm.__aenter__.side_effect = RuntimeError("db down")
    http_client = _http_client([_ok_response(), _ok_response()])

    with (
        patch(f"{_TASKS}.local_session", return_value=session_cm),
        patch(f"{_TASKS}.aioredis.from_url", return_value=_healthy_redis()),
        patch(f"{_TASKS}.httpx.AsyncClient", return_value=http_client),
    ):
        result = await _check_application_health()

    assert result["database"] == "unhealthy"
    assert result["redis"] == "healthy"
    assert result["api"] == "healthy"
    assert result["ready"] == "healthy"
    _assert_probe_urls(http_client, settings)


async def test_check_application_health_marks_redis_unhealthy_on_exception(settings) -> None:
    http_client = _http_client([_ok_response(), _ok_response()])

    with (
        patch(f"{_TASKS}.local_session", return_value=_healthy_session()),
        patch(f"{_TASKS}.aioredis.from_url", side_effect=RuntimeError("redis down")),
        patch(f"{_TASKS}.httpx.AsyncClient", return_value=http_client),
    ):
        result = await _check_application_health()

    assert result["database"] == "healthy"
    assert result["redis"] == "unhealthy"
    assert result["api"] == "healthy"
    assert result["ready"] == "healthy"
    _assert_probe_urls(http_client, settings)
