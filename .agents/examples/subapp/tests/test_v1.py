# Third-Party Dependencies
import pytest
from httpx import AsyncClient

# Local Dependencies
from src.core.config import settings
from tests.helper import _get_token

ADMIN_USERNAME = settings.USER_FIRST_ADMIN_USERNAME
ADMIN_PASSWORD = settings.USER_FIRST_ADMIN_PASSWORD
ADMIN_NAME = settings.USER_FIRST_ADMIN_NAME

test_item_id = None
test_item = {
    "title": "This is my test item",
    "text": "This is the content of my test item.",
    "media_url": "https://www.imageurl.com/test_item.jpg",
}


@pytest.mark.asyncio
async def test_create_item(client: AsyncClient) -> None:
    global test_item_id
    assert test_item_id is None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.post(
        url="/api/v1/example/items",
        json=test_item,
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    test_item_id = response.json()["id"]

    assert response.status_code == 201
    assert test_item_id is not None


@pytest.mark.asyncio
async def test_get_created_item(client: AsyncClient) -> None:
    global test_item_id
    assert test_item_id is not None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.get(
        url=f"/api/v1/example/items/{test_item_id}",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    item = response.json()

    assert response.status_code == 200
    assert item["title"] == test_item["title"]
    assert item["text"] == test_item["text"]
    assert item["media_url"] == test_item["media_url"]
    assert item["updated_by_user_name"] == ADMIN_NAME


@pytest.mark.asyncio
async def test_get_multiple_items(client: AsyncClient) -> None:
    global test_item_id
    assert test_item_id is not None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.get(
        url="/api/v1/example/items",
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

    item = next(row for row in result["data"] if row["id"] == test_item_id)
    assert item["updated_by_user_name"] == ADMIN_NAME


@pytest.mark.asyncio
async def test_update_item(client: AsyncClient) -> None:
    global test_item_id
    assert test_item_id is not None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.patch(
        url=f"/api/v1/example/items/{test_item_id}",
        json=test_item,
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Item updated"}


@pytest.mark.asyncio
async def test_delete_item(client: AsyncClient) -> None:
    global test_item_id
    assert test_item_id is not None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.delete(
        url=f"/api/v1/example/items/{test_item_id}",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Item deleted"}


@pytest.mark.asyncio
async def test_delete_already_deleted_item_as_admin(client: AsyncClient) -> None:
    global test_item_id
    assert test_item_id is not None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.delete(
        url=f"/api/v1/example/items/{test_item_id}",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Item already deleted (soft delete)."}


@pytest.mark.asyncio
async def test_delete_db_item(client: AsyncClient) -> None:
    global test_item_id
    assert test_item_id is not None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.delete(
        url=f"/api/v1/example/items/{test_item_id}/db",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Item deleted from the database"}
