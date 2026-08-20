# Built-in Dependencies
from uuid import uuid4

# Third-Party Dependencies
import pytest
from httpx import AsyncClient
from celery import states

# Local Dependencies
from src.core.exceptions.problem import problem_body
from src.core.utils.rate_limit import sanitize_path
from tests.helper import _create_regular_user

pytestmark = pytest.mark.integration

_QUEUE_HEALTH_PATH = "/api/v1/system/tasks/queue-health"


async def _create_task(client: AsyncClient, admin_headers: dict[str, str]) -> str:
    message = f"task-{uuid4().hex[:12]}"
    response = await client.post(
        f"/api/v1/system/tasks/sample?message={message}",
        headers=admin_headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _admin_user_id(client: AsyncClient, admin_headers: dict[str, str]) -> str:
    response = await client.get("/api/v1/system/users/me/", headers=admin_headers)
    assert response.status_code == 200
    return response.json()["id"]


async def _clear_rate_limit_keys(user_id: str, path: str) -> None:
    from src.core.utils import rate_limit

    pattern = f"ratelimit:{user_id}:{sanitize_path(path)}:*"
    keys = await rate_limit.client.keys(pattern)  # type: ignore[union-attr]
    if keys:
        await rate_limit.client.delete(*keys)  # type: ignore[union-attr]


async def test_create_task(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    task_id = await _create_task(client, admin_headers)
    assert task_id


async def test_create_task_unauthorized(client: AsyncClient) -> None:
    response = await client.post("/api/v1/system/tasks/sample?message=no-auth")
    assert response.status_code == 401


async def test_get_pending_task(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    task_id = await _create_task(client, admin_headers)
    response = await client.get(f"/api/v1/system/tasks/{task_id}", headers=admin_headers)
    assert response.status_code == 200
    result = response.json()
    assert result["task_id"] == task_id
    assert result["status"] in [states.PENDING, states.STARTED, states.SUCCESS]


async def test_read_processed_tasks(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    response = await client.get("/api/v1/system/tasks/processed", headers=admin_headers)
    assert response.status_code == 200
    result = response.json()
    assert "data" in result
    assert isinstance(result["data"], list)
    assert "total_count" in result
    assert "has_more" in result
    assert "page" in result
    assert "items_per_page" in result


async def test_read_pending_tasks(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    response = await client.get("/api/v1/system/tasks/pending", headers=admin_headers)
    assert response.status_code == 200


async def test_get_health_check_from_inexistent_queue(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    inexistent_queue_name = "inexistent_queue"
    response = await client.get(
        _QUEUE_HEALTH_PATH,
        params={"queue_name": inexistent_queue_name},
        headers=admin_headers,
    )
    assert response.status_code == 404
    assert response.json() == problem_body(
        f"Queue with name '{inexistent_queue_name}' not found on broker.",
        404,
        "not_found",
    )


async def test_tasks_get_route_rate_limiter_blocks_after_configured_limit(
    client: AsyncClient, admin_headers: dict[str, str], settings
) -> None:
    admin_id = await _admin_user_id(client, admin_headers)
    tiers_response = await client.get("/api/v1/system/tiers", headers=admin_headers)
    assert tiers_response.status_code == 200
    default_tier = next(
        tier for tier in tiers_response.json()["data"] if tier["name"] == settings.TIER_NAME_DEFAULT
    )

    rate_limit_response = await client.post(
        f"/api/v1/system/rate-limits/tier/{default_tier['id']}",
        json={
            "name": f"rl-{uuid4().hex[:12]}",
            "path": _QUEUE_HEALTH_PATH,
            "limit": 1,
            "period": 3600,
        },
        headers=admin_headers,
    )
    assert rate_limit_response.status_code == 201, rate_limit_response.text
    rate_limit_id = rate_limit_response.json()["id"]

    await _clear_rate_limit_keys(admin_id, _QUEUE_HEALTH_PATH)
    try:
        first_response = await client.get(
            _QUEUE_HEALTH_PATH,
            params={"queue_name": "rate_limit_test_queue"},
            headers=admin_headers,
        )
        second_response = await client.get(
            _QUEUE_HEALTH_PATH,
            params={"queue_name": "rate_limit_test_queue"},
            headers=admin_headers,
        )
        assert first_response.status_code == 404
        assert second_response.status_code == 429
        assert second_response.json() == problem_body(
            "Rate limit exceeded.", 429, "rate_limit_exceeded"
        )
    finally:
        await _clear_rate_limit_keys(admin_id, _QUEUE_HEALTH_PATH)
        await client.delete(
            f"/api/v1/system/rate-limits/{rate_limit_id}/tier/{default_tier['id']}/db",
            headers=admin_headers,
        )


async def test_tasks_prefix_rate_limit_blocks_queue_health(
    client: AsyncClient, admin_headers: dict[str, str], settings
) -> None:
    admin_id = await _admin_user_id(client, admin_headers)
    tiers_response = await client.get("/api/v1/system/tiers", headers=admin_headers)
    assert tiers_response.status_code == 200
    default_tier = next(
        tier for tier in tiers_response.json()["data"] if tier["name"] == settings.TIER_NAME_DEFAULT
    )

    rate_limit_response = await client.post(
        f"/api/v1/system/rate-limits/tier/{default_tier['id']}",
        json={
            "name": f"rl-{uuid4().hex[:12]}",
            "path": "/api/v1/system/tasks",
            "limit": 1,
            "period": 3600,
        },
        headers=admin_headers,
    )
    assert rate_limit_response.status_code == 201, rate_limit_response.text
    rate_limit_id = rate_limit_response.json()["id"]

    await _clear_rate_limit_keys(admin_id, "/api/v1/system/tasks")
    try:
        first_response = await client.get(
            _QUEUE_HEALTH_PATH,
            params={"queue_name": "rate_limit_prefix_queue"},
            headers=admin_headers,
        )
        second_response = await client.get(
            _QUEUE_HEALTH_PATH,
            params={"queue_name": "rate_limit_prefix_queue"},
            headers=admin_headers,
        )
        assert first_response.status_code == 404
        assert second_response.status_code == 429
        assert second_response.json() == problem_body(
            "Rate limit exceeded.", 429, "rate_limit_exceeded"
        )
    finally:
        await _clear_rate_limit_keys(admin_id, "/api/v1/system/tasks")
        await client.delete(
            f"/api/v1/system/rate-limits/{rate_limit_id}/tier/{default_tier['id']}/db",
            headers=admin_headers,
        )


async def test_tasks_get_route_forbids_authenticated_regular_user(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    _, regular_headers = await _create_regular_user(client, admin_headers)
    response = await client.get("/api/v1/system/tasks/pending", headers=regular_headers)
    assert response.status_code == 403
    assert response.json() == problem_body("You do not have enough privileges.", 403, "forbidden")
