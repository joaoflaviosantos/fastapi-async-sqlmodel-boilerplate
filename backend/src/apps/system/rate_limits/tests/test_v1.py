# Built-in Dependencies
from uuid import uuid4

# Third-Party Dependencies
import pytest
from httpx import AsyncClient

# Local Dependencies
from src.core.exceptions.problem import problem_body
from src.core.utils.rate_limit import sanitize_path
from tests.helper import _create_regular_user

pytestmark = pytest.mark.integration


async def _create_disposable_tier(client: AsyncClient, admin_headers: dict[str, str]) -> str:
    payload = {"name": f"tier-{uuid4().hex[:12]}"}
    response = await client.post("/api/v1/system/tiers", json=payload, headers=admin_headers)
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _create_rate_limit(
    client: AsyncClient, admin_headers: dict[str, str], tier_id: str
) -> dict:
    payload = {
        "name": f"rl-{uuid4().hex[:12]}",
        "path": "/api/v1/system/tasks",
        "limit": 100,
        "period": 3600,
    }
    response = await client.post(
        f"/api/v1/system/rate-limits/tier/{tier_id}",
        json=payload,
        headers=admin_headers,
    )
    assert response.status_code == 201, response.text
    return {"id": response.json()["id"], "payload": payload, "tier_id": tier_id}


async def test_post_rate_limit(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    tier_id = await _create_disposable_tier(client, admin_headers)
    created = await _create_rate_limit(client, admin_headers, tier_id)
    assert created["id"]


async def test_post_rate_limit_unauthorized(client: AsyncClient) -> None:
    response = await client.post(
        f"/api/v1/system/rate-limits/tier/{uuid4()}",
        json={
            "name": f"rl-{uuid4().hex[:12]}",
            "path": "/api/v1/system/tasks",
            "limit": 100,
            "period": 3600,
        },
    )
    assert response.status_code == 401


async def test_post_rate_limit_forbidden_for_regular_user(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    _, regular_headers = await _create_regular_user(client, admin_headers)
    response = await client.post(
        f"/api/v1/system/rate-limits/tier/{uuid4()}",
        json={
            "name": f"rl-{uuid4().hex[:12]}",
            "path": "/api/v1/system/tasks",
            "limit": 100,
            "period": 3600,
        },
        headers=regular_headers,
    )
    assert response.status_code == 403
    assert response.json() == problem_body("You do not have enough privileges.", 403, "forbidden")


async def test_post_invalid_rate_limit_related_tier_id(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    response = await client.post(
        f"/api/v1/system/rate-limits/tier/{uuid4()}",
        json={
            "name": f"rl-{uuid4().hex[:12]}",
            "path": "/api/v1/system/tasks",
            "limit": 100,
            "period": 3600,
        },
        headers=admin_headers,
    )
    assert response.status_code == 404


async def test_post_invalid_rate_limit_path(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    tier_id = await _create_disposable_tier(client, admin_headers)
    response = await client.post(
        f"/api/v1/system/rate-limits/tier/{tier_id}",
        json={
            "name": f"rl-{uuid4().hex[:12]}",
            "path": "/api/v1/invalid/route",
            "limit": 100,
            "period": 3600,
        },
        headers=admin_headers,
    )
    assert response.status_code == 422


async def test_get_multiple_rate_limits(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    tier_id = await _create_disposable_tier(client, admin_headers)
    created = await _create_rate_limit(client, admin_headers, tier_id)
    response = await client.get(
        f"/api/v1/system/rate-limits/tier/{tier_id}",
        headers=admin_headers,
    )
    assert response.status_code == 200
    result = response.json()
    assert "data" in result
    assert isinstance(result["data"], list)
    assert created["id"] in [item["id"] for item in result["data"]]
    assert "total_count" in result
    assert "has_more" in result
    assert "page" in result
    assert "items_per_page" in result


async def test_get_rate_limit(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    tier_id = await _create_disposable_tier(client, admin_headers)
    created = await _create_rate_limit(client, admin_headers, tier_id)
    response = await client.get(
        f"/api/v1/system/rate-limits/{created['id']}/tier/{tier_id}",
        headers=admin_headers,
    )
    assert response.status_code == 200
    rate_limit = response.json()
    assert rate_limit["name"] == created["payload"]["name"]
    assert rate_limit["path"] == sanitize_path(created["payload"]["path"])
    assert rate_limit["limit"] == created["payload"]["limit"]
    assert rate_limit["period"] == created["payload"]["period"]


async def test_update_rate_limit(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    tier_id = await _create_disposable_tier(client, admin_headers)
    created = await _create_rate_limit(client, admin_headers, tier_id)
    response = await client.patch(
        f"/api/v1/system/rate-limits/{created['id']}/tier/{tier_id}",
        json={
            "name": f"updated-{uuid4().hex[:12]}",
            "limit": 200,
            "period": 7200,
        },
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Rate Limit updated"}


async def test_erase_db_rate_limit(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    tier_id = await _create_disposable_tier(client, admin_headers)
    created = await _create_rate_limit(client, admin_headers, tier_id)
    response = await client.delete(
        f"/api/v1/system/rate-limits/{created['id']}/tier/{tier_id}/db",
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Rate Limit deleted from the database"}


async def test_erase_db_rate_limit_forbidden_for_regular_user(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    tier_id = await _create_disposable_tier(client, admin_headers)
    created = await _create_rate_limit(client, admin_headers, tier_id)
    _, regular_headers = await _create_regular_user(client, admin_headers)
    response = await client.delete(
        f"/api/v1/system/rate-limits/{created['id']}/tier/{tier_id}/db",
        headers=regular_headers,
    )
    assert response.status_code == 403
    assert response.json() == problem_body("You do not have enough privileges.", 403, "forbidden")


async def test_update_rate_limit_same_path(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    tier_id = await _create_disposable_tier(client, admin_headers)
    created = await _create_rate_limit(client, admin_headers, tier_id)
    response = await client.patch(
        f"/api/v1/system/rate-limits/{created['id']}/tier/{tier_id}",
        json={"path": created["payload"]["path"]},
        headers=admin_headers,
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"message": "Rate Limit updated"}


async def test_update_invalid_rate_limit_path(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    tier_id = await _create_disposable_tier(client, admin_headers)
    created = await _create_rate_limit(client, admin_headers, tier_id)
    response = await client.patch(
        f"/api/v1/system/rate-limits/{created['id']}/tier/{tier_id}",
        json={"path": "/api/v1/invalid/route"},
        headers=admin_headers,
    )
    assert response.status_code == 422
    assert response.json() == problem_body("Invalid path", 422, "unprocessable_entity")


async def test_erase_missing_rate_limit_is_not_found(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    tier_id = await _create_disposable_tier(client, admin_headers)
    response = await client.delete(
        f"/api/v1/system/rate-limits/{uuid4()}/tier/{tier_id}/db",
        headers=admin_headers,
    )
    assert response.status_code == 404
    assert response.json() == problem_body("Rate Limit not found", 404, "not_found")
