# Built-in Dependencies
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

# Third-Party Dependencies
import pytest
from fastapi import APIRouter, FastAPI
from starlette.requests import Request

# Local Dependencies
from src.core.exceptions.cache_exceptions import MissingClientError
from src.core.utils import rate_limit as rate_limit_module
from src.core.utils.rate_limit import (
    caller_identifier,
    is_rate_limited,
    is_valid_path,
    match_longest_prefix,
    normalize_route_path,
    request_route_template,
    sanitize_path,
)

pytestmark = pytest.mark.unit


def test_normalize_route_path_strips_query_string() -> None:
    assert normalize_route_path("/users?name=john") == "/users"


def test_sanitize_path_replaces_slashes() -> None:
    assert sanitize_path("/api/v1/system/tasks") == "api_v1_system_tasks"


def test_sanitize_path_normalizes_then_strips() -> None:
    assert sanitize_path("/users?name=john") == "users"


def test_match_longest_prefix_prefers_more_specific_rule() -> None:
    template = sanitize_path("/api/v1/system/tasks/queue-health")
    rules = [
        {"path": "api_v1_system_tasks", "limit": 10, "period": 60},
        {"path": "api_v1_system_tasks_queue-health", "limit": 1, "period": 60},
    ]
    matched = match_longest_prefix(template, rules)
    assert matched is not None
    assert matched["limit"] == 1
    assert matched["path"] == "api_v1_system_tasks_queue-health"


def test_match_longest_prefix_groups_under_parent_path() -> None:
    template = sanitize_path("/api/v1/system/tasks/{task_id}")
    rules = [{"path": "api_v1_system_tasks", "limit": 2, "period": 60}]
    matched = match_longest_prefix(template, rules)
    assert matched is not None
    assert matched["path"] == "api_v1_system_tasks"


def test_match_longest_prefix_returns_none_when_unrelated() -> None:
    template = sanitize_path("/api/v1/system/users")
    rules = [{"path": "api_v1_system_tasks", "limit": 2, "period": 60}]
    assert match_longest_prefix(template, rules) is None


def test_request_route_template_uses_matched_route() -> None:
    request = _request(
        host="127.0.0.1",
        path="/api/v1/system/tasks/abc-uuid",
        path_params={"task_id": "abc-uuid"},
        route_path="/api/v1/system/tasks/{task_id}",
    )
    assert request_route_template(request) == "/api/v1/system/tasks/{task_id}"


def test_request_route_template_joins_router_prefixes() -> None:
    request = _request(
        host="127.0.0.1",
        path="/api/v1/system/tasks/abc-uuid",
        path_params={"task_id": "abc-uuid"},
        route_path="/system/tasks/{task_id}",
    )
    assert request_route_template(request) == "/api/v1/system/tasks/{task_id}"


def test_request_route_template_joins_prefixes_without_params() -> None:
    request = _request(
        host="127.0.0.1",
        path="/api/v1/system/tasks/queue-health",
        route_path="/system/tasks/queue-health",
    )
    assert request_route_template(request) == "/api/v1/system/tasks/queue-health"


def test_request_route_template_falls_back_to_url() -> None:
    request = _request(host="127.0.0.1", path="/api/v1/system/tasks/abc-uuid")
    assert request_route_template(request) == "/api/v1/system/tasks/abc-uuid"


def test_is_valid_path_accepts_route_prefix() -> None:
    app = FastAPI()

    @app.get("/api/v1/system/tasks/queue-health")
    def _queue_health() -> dict:
        return {}

    assert is_valid_path("/api/v1/system/tasks", app) is True
    assert is_valid_path("api_v1_system_tasks_queue-health", app) is True
    assert is_valid_path("/api/v1/does-not-exist", app) is False


def _request(
    *,
    host: str | None,
    headers: dict[str, str] | None = None,
    path: str = "/",
    path_params: dict[str, str] | None = None,
    route_path: str | None = None,
) -> Request:
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [
            (key.lower().encode(), value.encode()) for key, value in (headers or {}).items()
        ],
        "client": (host, 123) if host is not None else None,
        "server": ("test", 80),
        "path_params": path_params or {},
    }
    if route_path is not None:
        scope["route"] = SimpleNamespace(path=route_path)
    return Request(scope)


def test_caller_identifier_uses_direct_host_when_proxy_untrusted() -> None:
    request = _request(
        host="10.0.0.8",
        headers={"x-forwarded-for": "203.0.113.10, 10.0.0.1"},
    )
    assert caller_identifier(request, trust_proxy_headers=False) == "10.0.0.8"


def test_caller_identifier_uses_first_forwarded_hop_when_trusted() -> None:
    request = _request(
        host="10.0.0.8",
        headers={"x-forwarded-for": "203.0.113.10, 10.0.0.1"},
    )
    assert caller_identifier(request, trust_proxy_headers=True) == "203.0.113.10"


def test_caller_identifier_uses_x_real_ip_when_trusted() -> None:
    request = _request(host="10.0.0.8", headers={"x-real-ip": "198.51.100.20"})
    assert caller_identifier(request, trust_proxy_headers=True) == "198.51.100.20"


def test_caller_identifier_none_without_client() -> None:
    request = _request(host=None)
    assert caller_identifier(request, trust_proxy_headers=False) is None


def test_is_valid_path_sees_mounted_prefixes() -> None:
    app = FastAPI()
    inner = APIRouter()

    @inner.get("/system/tasks/{task_id}")
    def _read_task() -> dict:
        return {}

    v1 = APIRouter(prefix="/v1")
    v1.include_router(inner)
    api = APIRouter(prefix="/api")
    api.include_router(v1)
    app.include_router(api)

    assert is_valid_path("/api/v1/system/tasks", app) is True
    assert is_valid_path("api_v1_system_tasks_{task_id}", app) is True


async def test_is_rate_limited_raises_when_client_missing() -> None:
    app = FastAPI()
    with patch.object(rate_limit_module, "client", None):
        with pytest.raises(MissingClientError):
            await is_rate_limited(app, "user-1", "api_v1_system_tasks", 1, 60)


async def test_is_rate_limited_rejects_period_below_one() -> None:
    app = FastAPI()
    mock_client = MagicMock()
    with patch.object(rate_limit_module, "client", mock_client):
        with pytest.raises(ValueError, match="at least 1 second"):
            await is_rate_limited(app, "user-1", "api_v1_system_tasks", 1, 0)


async def test_is_rate_limited_uses_incr_and_expire_nx() -> None:
    app = FastAPI()

    @app.get("/api/v1/system/tasks/queue-health")
    def _queue_health() -> dict:
        return {}

    pipe = MagicMock()
    pipe.execute = AsyncMock(return_value=[2, True])
    mock_client = MagicMock()
    mock_client.pipeline.return_value = pipe

    with patch.object(rate_limit_module, "client", mock_client):
        limited = await is_rate_limited(app, "user-1", "api_v1_system_tasks", 1, 60)

    assert limited is True
    pipe.incr.assert_called_once()
    pipe.expire.assert_called_once()
    expire_kwargs = pipe.expire.call_args.kwargs
    assert expire_kwargs.get("nx") is True
    assert pipe.expire.call_args.args[1] == 60
