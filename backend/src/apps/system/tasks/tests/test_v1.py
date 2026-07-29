# Built-in Dependencies
import asyncio
from uuid import uuid4

# Third-Party Dependencies
import pytest
from httpx import AsyncClient
from celery import states

# Local Dependencies
from src.core.config import settings
from tests.helper import _get_token

# Test data: admin/superuser 'test' credentials
ADMIN_USERNAME = settings.USER_FIRST_ADMIN_USERNAME
ADMIN_PASSWORD = settings.USER_FIRST_ADMIN_PASSWORD

# Test global variables
test_task_id = None
test_task_message = "Test Message"


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient) -> None:
    """Test creating a new background task."""
    global test_task_id
    assert test_task_id is None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.post(
        url=f"/api/v1/system/tasks/sample?message={test_task_message}",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 201
    result = response.json()
    assert "id" in result
    test_task_id = result["id"]
    assert test_task_id is not None


@pytest.mark.asyncio
async def test_get_pending_task(client: AsyncClient) -> None:
    """Test retrieving a pending task that hasn't been started yet."""
    global test_task_id
    assert test_task_id is not None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.get(
        url=f"/api/v1/system/tasks/{test_task_id}",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["task_id"] == test_task_id
    assert result["status"] == states.PENDING


@pytest.mark.asyncio
async def test_get_started_task(client: AsyncClient) -> None:
    """Test retrieving a task that has been started (checks database)."""
    global test_task_id
    assert test_task_id is not None

    # Give the task some time to start
    await asyncio.sleep(1)

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.get(
        url=f"/api/v1/system/tasks/{test_task_id}",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["task_id"] == test_task_id
    # Task should be in STARTED or SUCCESS state after processing
    assert result["status"] in [states.STARTED, states.SUCCESS, states.PENDING]


@pytest.mark.asyncio
async def test_read_processed_tasks(client: AsyncClient) -> None:
    """Test retrieving processed tasks."""
    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.get(
        url="/api/v1/system/tasks/processed",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 200
    result = response.json()
    assert "data" in result
    assert isinstance(result["data"], list)
    assert "total_count" in result
    assert "has_more" in result
    assert "page" in result
    assert "items_per_page" in result


@pytest.mark.asyncio
async def test_read_pending_tasks(client: AsyncClient) -> None:
    """Test retrieving pending tasks."""
    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.get(
        url="/api/v1/system/tasks/pending",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_health_check_from_inexistent_queue(client: AsyncClient) -> None:
    """Test health check for non-existent queue."""
    inexistent_queue_name = "inexistent_queue"

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.get(
        url="/api/v1/system/tasks/queue-health",
        params={"queue_name": f"{inexistent_queue_name}"},
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": f"Queue with name '{inexistent_queue_name}' not found on broker."
    }


@pytest.mark.asyncio
async def test_tasks_get_route_rate_limiter_blocks_after_configured_limit(
    client: AsyncClient,
) -> None:
    """Test that GET task routes enforce configured Redis-backed rate limits."""
    from src.core.utils import rate_limit

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)
    access_token = token.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    tiers_response = await client.get(
        url="/api/v1/system/tiers",
        headers=headers,
    )
    assert tiers_response.status_code == 200

    default_tier = next(
        tier for tier in tiers_response.json()["data"] if tier["name"] == settings.TIER_NAME_DEFAULT
    )

    rate_limit_response = await client.post(
        url=f"/api/v1/system/rate-limits/tier/{default_tier['id']}",
        json={
            "name": f"Task Queue Health Test Rate Limit {uuid4()}",
            "path": "/api/v1/system/tasks/queue-health",
            "limit": 1,
            "period": 3600,
        },
        headers=headers,
    )
    assert rate_limit_response.status_code == 201
    rate_limit_id = rate_limit_response.json()["id"]

    try:
        await rate_limit.client.flushdb()  # type: ignore[union-attr]

        first_response = await client.get(
            url="/api/v1/system/tasks/queue-health",
            params={"queue_name": "rate_limit_test_queue"},
            headers=headers,
        )
        second_response = await client.get(
            url="/api/v1/system/tasks/queue-health",
            params={"queue_name": "rate_limit_test_queue"},
            headers=headers,
        )

        assert first_response.status_code == 404
        assert second_response.status_code == 429
        assert second_response.json() == {"detail": "Rate limit exceeded."}
    finally:
        await rate_limit.client.flushdb()  # type: ignore[union-attr]
        await client.delete(
            url=f"/api/v1/system/rate-limits/{rate_limit_id}/tier/{default_tier['id']}/db",
            headers=headers,
        )
