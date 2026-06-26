# Third-Party Dependencies
import pytest
from httpx import AsyncClient

# Local Dependencies
from src.core.config import settings
from tests.helper import _get_token

# Test data: admin/superuser 'test' credentials
ADMIN_USERNAME = settings.USER_FIRST_ADMIN_USERNAME
ADMIN_PASSWORD = settings.USER_FIRST_ADMIN_PASSWORD

# Test global variables
test_default_tier_id = None
test_tier_id = None
test_tier = {"name": "Test Tier"}


@pytest.mark.asyncio
async def test_get_default_tier(client: AsyncClient) -> None:
    global test_default_tier_id
    assert test_default_tier_id is None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.get(
        url="/api/v1/system/tiers",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    tiers_data = response.json()["data"]

    # Create a dictionary to map tier names to IDs
    tiers_map = dict((tier["name"], tier["id"]) for tier in tiers_data)

    # Get the ID of the related tier using the mapping
    test_default_tier_id = tiers_map.get(settings.TIER_NAME_DEFAULT)

    assert response.status_code == 200
    assert test_default_tier_id is not None


@pytest.mark.asyncio
async def test_post_tier(client: AsyncClient) -> None:
    global test_tier_id
    assert test_tier_id is None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.post(
        "/api/v1/system/tiers",
        json=test_tier,
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    test_tier_id = response.json()["id"]

    assert response.status_code == 201
    assert test_tier_id is not None


@pytest.mark.asyncio
async def test_get_multiple_tiers(client: AsyncClient) -> None:
    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.get(
        url="/api/v1/system/tiers",
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
async def test_get_tier(client: AsyncClient) -> None:
    global test_tier_id
    assert test_tier_id is not None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.get(
        url=f"/api/v1/system/tiers/{test_tier_id}",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 200
    assert response.json()["name"] == test_tier["name"]


@pytest.mark.asyncio
async def test_update_tier(client: AsyncClient) -> None:
    global test_tier_id
    assert test_tier_id is not None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    updated_tier_name = "Updated Test Tier"

    response = await client.patch(
        url=f"/api/v1/system/tiers/{test_tier_id}",
        json={"name": updated_tier_name},
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Tier updated"}


@pytest.mark.asyncio
async def test_update_tier_to_default(client: AsyncClient) -> None:
    global test_tier_id
    assert test_tier_id is not None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.patch(
        url=f"/api/v1/system/tiers/{test_tier_id}",
        json={"default": True},
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "Extra inputs are not permitted"


@pytest.mark.asyncio
async def test_update_default_tier(client: AsyncClient) -> None:
    global test_default_tier_id
    assert test_default_tier_id is not None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    updated_default_tier_name = "Updated Default Tier"

    response = await client.patch(
        url=f"/api/v1/system/tiers/{test_default_tier_id}",
        json={"name": updated_default_tier_name},
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Default Tier cannot be updated"}


@pytest.mark.asyncio
async def test_delete_db_tier(client: AsyncClient) -> None:
    global test_tier_id
    assert test_tier_id is not None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.delete(
        url=f"/api/v1/system/tiers/{test_tier_id}/db",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Tier deleted from the database"}


@pytest.mark.asyncio
async def test_delete_default_tier(client: AsyncClient) -> None:
    global test_default_tier_id
    assert test_default_tier_id is not None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.delete(
        url=f"/api/v1/system/tiers/{test_default_tier_id}/db",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Default Tier cannot be deleted"}
