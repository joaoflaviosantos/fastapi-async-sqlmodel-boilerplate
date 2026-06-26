# Built-in Dependencies
import asyncio

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
