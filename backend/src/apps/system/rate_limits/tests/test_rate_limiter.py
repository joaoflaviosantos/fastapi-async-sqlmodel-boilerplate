# Built-in Dependencies
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

# Third-Party Dependencies
import pytest
from fastapi import FastAPI

# Local Dependencies
from src.apps.system.rate_limits.deps import rate_limiter
from src.core.exceptions.http_exceptions import RateLimitException

pytestmark = pytest.mark.unit


async def test_rate_limiter_matches_longest_prefix_for_redis_key() -> None:
    request = MagicMock()
    request.scope = {"route": SimpleNamespace(path="/system/tasks/{task_id}")}
    request.url.path = "/api/v1/system/tasks/abc-uuid"
    request.path_params = {"task_id": "abc-uuid"}
    request.app = FastAPI()
    user = {"id": uuid4(), "tier_id": uuid4()}
    parent_rule = {"path": "api_v1_system_tasks", "limit": 3, "period": 60}

    with (
        patch("src.apps.system.rate_limits.deps.tier_repository") as tier_repo,
        patch("src.apps.system.rate_limits.deps.rate_limit_repository") as rl_repo,
        patch(
            "src.apps.system.rate_limits.deps.is_rate_limited",
            new_callable=AsyncMock,
            return_value=False,
        ) as limited,
    ):
        tier_repo.get = AsyncMock(return_value={"id": user["tier_id"], "name": "free"})
        rl_repo.get_all = AsyncMock(return_value=[parent_rule])
        await rate_limiter(request=request, db=MagicMock(), user=user)

    limited.assert_awaited_once()
    assert limited.await_args.kwargs["path"] == "api_v1_system_tasks"
    assert limited.await_args.kwargs["limit"] == 3


async def test_rate_limiter_skips_anonymous_without_identifier() -> None:
    request = MagicMock()
    request.scope = {"route": SimpleNamespace(path="/api/v1/system/tasks/queue-health")}
    request.url.path = "/api/v1/system/tasks/queue-health"

    with (
        patch("src.apps.system.rate_limits.deps.caller_identifier", return_value=None),
        patch(
            "src.apps.system.rate_limits.deps.is_rate_limited", new_callable=AsyncMock
        ) as limited,
    ):
        await rate_limiter(request=request, db=MagicMock(), user=None)

    limited.assert_not_awaited()


async def test_rate_limiter_raises_when_limited() -> None:
    request = MagicMock()
    request.scope = {"route": SimpleNamespace(path="/api/v1/system/tasks/queue-health")}
    request.url.path = "/api/v1/system/tasks/queue-health"
    request.app = FastAPI()
    user = {"id": uuid4(), "tier_id": uuid4()}

    with (
        patch("src.apps.system.rate_limits.deps.tier_repository") as tier_repo,
        patch("src.apps.system.rate_limits.deps.rate_limit_repository") as rl_repo,
        patch(
            "src.apps.system.rate_limits.deps.is_rate_limited",
            new_callable=AsyncMock,
            return_value=True,
        ),
    ):
        tier_repo.get = AsyncMock(return_value=None)
        rl_repo.get_all = AsyncMock(return_value=[])
        with pytest.raises(RateLimitException):
            await rate_limiter(request=request, db=MagicMock(), user=user)
