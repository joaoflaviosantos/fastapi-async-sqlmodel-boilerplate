# Third-Party Dependencies
import pytest
from httpx import AsyncClient

# Local Dependencies
from src.core.config import settings
from tests.helper import _get_token, _ensure_test_user_exists

# Test data: 'common user'
TEST_NAME = settings.TEST_NAME
TEST_USERNAME = settings.TEST_USERNAME
TEST_EMAIL = settings.TEST_EMAIL
TEST_PASSWORD = settings.TEST_PASSWORD

# Test data: admin/superuser 'test' credentials
ADMIN_USERNAME = settings.ADMIN_USERNAME
ADMIN_PASSWORD = settings.ADMIN_PASSWORD

# Test data: default tier
DEFAULT_TIER_NAME = settings.TIER_NAME_DEFAULT

# Test global variables
user_id = None


@pytest.mark.asyncio
async def test_post_user(client: AsyncClient) -> None:
    global user_id

    # Ensure test user exists (will restore if soft-deleted or create if doesn't exist)
    user_id = await _ensure_test_user_exists(client)

    assert user_id is not None


@pytest.mark.asyncio
async def test_get_own_user_data(client: AsyncClient) -> None:
    global user_id
    assert user_id is not None

    token = await _get_token(username=TEST_USERNAME, password=TEST_PASSWORD, client=client)

    response = await client.get(
        url="/api/v1/system/users/me/",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 200
    assert user_id == response.json()["id"]
    assert response.json()["username"] == TEST_USERNAME


@pytest.mark.asyncio
async def test_get_user(client: AsyncClient) -> None:
    global user_id
    assert user_id is not None

    token = await _get_token(username=TEST_USERNAME, password=TEST_PASSWORD, client=client)

    response = await client.get(
        url=f"/api/v1/system/users/{user_id}",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 200
    assert response.json()["username"] == TEST_USERNAME


@pytest.mark.asyncio
async def test_get_multiple_users(client: AsyncClient) -> None:
    token = await _get_token(username=TEST_USERNAME, password=TEST_PASSWORD, client=client)

    response = await client.get(
        url="/api/v1/system/users",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 200
    result = response.json()
    assert "data" in result
    assert isinstance(result["data"], list)
    assert len(result["data"]) > 0
    assert "total_count" in result
    assert "has_more" in result
    assert "page" in result
    assert "items_per_page" in result


@pytest.mark.asyncio
async def test_update_your_own_user(client: AsyncClient) -> None:
    global user_id
    assert user_id is not None

    token = await _get_token(username=TEST_USERNAME, password=TEST_PASSWORD, client=client)

    response = await client.patch(
        url=f"/api/v1/system/users/{user_id}",
        json={"name": f"Updated {TEST_NAME}"},
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "User updated"}


@pytest.mark.asyncio
async def test_update_user_as_admin(client: AsyncClient) -> None:
    global user_id
    assert user_id is not None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.patch(
        url=f"/api/v1/system/users/{user_id}",
        json={"name": f"Updated {TEST_NAME} (again)"},
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "User updated"}


@pytest.mark.asyncio
async def test_get_user_rate_limits(client: AsyncClient) -> None:
    global user_id
    assert user_id is not None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.get(
        url=f"/api/v1/system/users/{user_id}/rate-limits",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 200
    assert "tier_rate_limits" in response.json()


@pytest.mark.asyncio
async def test_get_user_tier(client: AsyncClient) -> None:
    global user_id
    assert user_id is not None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.get(
        url=f"/api/v1/system/users/{user_id}/tier",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 200
    assert response.json()["tier_name"] == DEFAULT_TIER_NAME


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient) -> None:
    global user_id
    assert user_id is not None

    token = await _get_token(username=TEST_USERNAME, password=TEST_PASSWORD, client=client)

    response = await client.delete(
        url=f"/api/v1/system/users/{user_id}",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "User deleted"}


@pytest.mark.asyncio
async def test_delete_already_deleted_user_as_admin(client: AsyncClient) -> None:
    global user_id
    assert user_id is not None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.delete(
        url=f"/api/v1/system/users/{user_id}",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "User already deleted (soft delete)."}


@pytest.mark.asyncio
async def test_delete_db_user(client: AsyncClient) -> None:
    global user_id
    assert user_id is not None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.delete(
        url=f"/api/v1/system/users/{user_id}/db",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "User deleted from the database"}
