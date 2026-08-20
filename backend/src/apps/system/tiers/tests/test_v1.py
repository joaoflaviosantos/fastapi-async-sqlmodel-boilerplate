# Built-in Dependencies
from uuid import uuid4

# Third-Party Dependencies
import pytest
from httpx import AsyncClient

# Local Dependencies
from src.core.exceptions.problem import problem_body
from tests.helper import _create_regular_user

pytestmark = pytest.mark.integration


async def _default_tier_id(client: AsyncClient, admin_headers: dict[str, str], settings) -> str:
    response = await client.get("/api/v1/system/tiers", headers=admin_headers)
    assert response.status_code == 200
    tiers_map = {tier["name"]: tier["id"] for tier in response.json()["data"]}
    default_id = tiers_map.get(settings.TIER_NAME_DEFAULT)
    assert default_id is not None
    return default_id


async def _create_tier(client: AsyncClient, admin_headers: dict[str, str]) -> dict:
    payload = {"name": f"tier-{uuid4().hex[:12]}"}
    response = await client.post("/api/v1/system/tiers", json=payload, headers=admin_headers)
    assert response.status_code == 201, response.text
    return {"id": response.json()["id"], "payload": payload}


async def test_get_default_tier(
    client: AsyncClient, admin_headers: dict[str, str], settings
) -> None:
    default_id = await _default_tier_id(client, admin_headers, settings)
    assert default_id


async def test_post_tier(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    created = await _create_tier(client, admin_headers)
    assert created["id"]


async def test_post_tier_unauthorized(client: AsyncClient) -> None:
    response = await client.post("/api/v1/system/tiers", json={"name": f"tier-{uuid4().hex[:12]}"})
    assert response.status_code == 401


async def test_post_tier_forbidden_for_regular_user(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    _, regular_headers = await _create_regular_user(client, admin_headers)
    response = await client.post(
        "/api/v1/system/tiers",
        json={"name": f"tier-{uuid4().hex[:12]}"},
        headers=regular_headers,
    )
    assert response.status_code == 403
    assert response.json() == problem_body("You do not have enough privileges.", 403, "forbidden")


async def test_get_multiple_tiers(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    response = await client.get("/api/v1/system/tiers", headers=admin_headers)
    assert response.status_code == 200
    result = response.json()
    assert "data" in result
    assert isinstance(result["data"], list)
    assert len(result["data"]) > 0
    assert "total_count" in result
    assert "has_more" in result
    assert "page" in result
    assert "items_per_page" in result


async def test_get_tier(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    created = await _create_tier(client, admin_headers)
    response = await client.get(
        f"/api/v1/system/tiers/{created['id']}",
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == created["payload"]["name"]


async def test_update_tier(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    created = await _create_tier(client, admin_headers)
    response = await client.patch(
        f"/api/v1/system/tiers/{created['id']}",
        json={"name": f"updated-{uuid4().hex[:12]}"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Tier updated"}


async def test_update_tier_to_default(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    created = await _create_tier(client, admin_headers)
    response = await client.patch(
        f"/api/v1/system/tiers/{created['id']}",
        json={"default": True},
        headers=admin_headers,
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_error"
    assert body["status"] == 422
    assert body["detail"] == "Request validation failed."
    assert any("Extra inputs are not permitted" in err.get("msg", "") for err in body["errors"])


async def test_update_default_tier(
    client: AsyncClient, admin_headers: dict[str, str], settings
) -> None:
    default_id = await _default_tier_id(client, admin_headers, settings)
    response = await client.patch(
        f"/api/v1/system/tiers/{default_id}",
        json={"name": "Updated Default Tier"},
        headers=admin_headers,
    )
    assert response.status_code == 403
    assert response.json() == problem_body("Default Tier cannot be updated", 403, "forbidden")


async def test_delete_db_tier(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    created = await _create_tier(client, admin_headers)
    response = await client.delete(
        f"/api/v1/system/tiers/{created['id']}/db",
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Tier deleted from the database"}


async def test_erase_db_tier_forbidden_for_regular_user(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    created = await _create_tier(client, admin_headers)
    _, regular_headers = await _create_regular_user(client, admin_headers)
    response = await client.delete(
        f"/api/v1/system/tiers/{created['id']}/db",
        headers=regular_headers,
    )
    assert response.status_code == 403
    assert response.json() == problem_body("You do not have enough privileges.", 403, "forbidden")


async def test_delete_default_tier(
    client: AsyncClient, admin_headers: dict[str, str], settings
) -> None:
    default_id = await _default_tier_id(client, admin_headers, settings)
    response = await client.delete(
        f"/api/v1/system/tiers/{default_id}/db",
        headers=admin_headers,
    )
    assert response.status_code == 403
    assert response.json() == problem_body("Default Tier cannot be deleted", 403, "forbidden")


async def test_get_tiers_as_authenticated_regular_user(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    _, regular_headers = await _create_regular_user(client, admin_headers)
    response = await client.get("/api/v1/system/tiers", headers=regular_headers)
    assert response.status_code == 200
    assert "data" in response.json()
