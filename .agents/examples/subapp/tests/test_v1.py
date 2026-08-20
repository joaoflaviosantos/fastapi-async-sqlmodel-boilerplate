# Built-in Dependencies
from uuid import uuid4

# Third-Party Dependencies
import pytest
from httpx import AsyncClient

# Local Dependencies
from src.core.exceptions.problem import problem_body
from tests.helper import _create_regular_user

pytestmark = pytest.mark.integration

_ITEM_MEDIA_URL = "https://www.imageurl.com/test_item.jpg"


async def _create_item(client: AsyncClient, headers: dict[str, str]) -> dict:
    payload = {
        "title": f"item-{uuid4()}",
        "text": "This is the content of my test item.",
        "media_url": _ITEM_MEDIA_URL,
    }
    response = await client.post("/api/v1/example/items", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    body = response.json()
    return {"id": body["id"], "payload": payload, "body": body}


async def test_create_item(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    created = await _create_item(client, admin_headers)
    assert created["id"]
    assert created["body"]["title"] == created["payload"]["title"]


async def test_create_item_unauthorized(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/example/items",
        json={
            "title": f"item-{uuid4()}",
            "text": "content",
            "media_url": _ITEM_MEDIA_URL,
        },
    )
    assert response.status_code == 401


async def test_get_item(client: AsyncClient, admin_headers: dict[str, str], settings) -> None:
    created = await _create_item(client, admin_headers)
    response = await client.get(
        f"/api/v1/example/items/{created['id']}",
        headers=admin_headers,
    )
    assert response.status_code == 200
    item = response.json()
    assert item["title"] == created["payload"]["title"]
    assert item["text"] == created["payload"]["text"]
    assert item["media_url"] == created["payload"]["media_url"]
    assert item["updated_by_user_name"] == settings.USER_FIRST_ADMIN_NAME


async def test_get_multiple_items(
    client: AsyncClient, admin_headers: dict[str, str], settings
) -> None:
    created = await _create_item(client, admin_headers)
    response = await client.get("/api/v1/example/items", headers=admin_headers)
    assert response.status_code == 200
    result = response.json()
    assert "data" in result
    assert isinstance(result["data"], list)
    assert len(result["data"]) > 0
    assert "total_count" in result
    assert "has_more" in result
    assert "page" in result
    assert "items_per_page" in result
    item = next(row for row in result["data"] if row["id"] == created["id"])
    assert item["updated_by_user_name"] == settings.USER_FIRST_ADMIN_NAME


async def test_update_item(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    created = await _create_item(client, admin_headers)
    response = await client.patch(
        f"/api/v1/example/items/{created['id']}",
        json=created["payload"],
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Item updated"}


async def test_delete_item(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    created = await _create_item(client, admin_headers)
    response = await client.delete(
        f"/api/v1/example/items/{created['id']}",
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Item deleted"}


async def test_delete_already_deleted_item_as_admin(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    created = await _create_item(client, admin_headers)
    first = await client.delete(
        f"/api/v1/example/items/{created['id']}",
        headers=admin_headers,
    )
    assert first.status_code == 200
    second = await client.delete(
        f"/api/v1/example/items/{created['id']}",
        headers=admin_headers,
    )
    assert second.status_code == 404
    assert second.json() == problem_body("Item already deleted (soft delete).", 404, "not_found")


async def test_delete_db_item(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    created = await _create_item(client, admin_headers)
    response = await client.delete(
        f"/api/v1/example/items/{created['id']}/db",
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Item deleted from the database"}


async def test_erase_db_item_forbidden_for_regular_user(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    created = await _create_item(client, admin_headers)
    _, regular_headers = await _create_regular_user(client, admin_headers)
    response = await client.delete(
        f"/api/v1/example/items/{created['id']}/db",
        headers=regular_headers,
    )
    assert response.status_code == 403
    assert response.json() == problem_body("You do not have enough privileges.", 403, "forbidden")
