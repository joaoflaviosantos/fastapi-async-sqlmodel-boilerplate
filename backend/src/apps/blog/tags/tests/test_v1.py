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

_TAGS_LIST_PATH = "/api/v1/blog/tags"


async def _create_tag(client: AsyncClient, headers: dict[str, str]) -> dict:
    payload = {"name": f"tag-{uuid4().hex[:12]}"}
    response = await client.post(_TAGS_LIST_PATH, json=payload, headers=headers)
    assert response.status_code == 201, response.text
    body = response.json()
    return {"id": body["id"], "payload": payload, "body": body}


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


async def test_create_tag(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    created = await _create_tag(client, admin_headers)
    assert created["id"]
    assert created["body"]["name"] == created["payload"]["name"]


async def test_create_tag_unauthorized(client: AsyncClient) -> None:
    response = await client.post(_TAGS_LIST_PATH, json={"name": f"tag-{uuid4().hex[:12]}"})
    assert response.status_code == 401


async def test_create_tag_duplicate_name(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    created = await _create_tag(client, admin_headers)
    response = await client.post(
        _TAGS_LIST_PATH,
        json={"name": created["payload"]["name"]},
        headers=admin_headers,
    )
    assert response.status_code == 422
    assert response.json() == problem_body("Tag name not available", 422, "duplicate_value")


async def test_get_tag(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    created = await _create_tag(client, admin_headers)
    response = await client.get(f"{_TAGS_LIST_PATH}/{created['id']}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["name"] == created["payload"]["name"]


async def test_get_multiple_tags(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    created = await _create_tag(client, admin_headers)
    response = await client.get(
        _TAGS_LIST_PATH,
        params={"name": created["payload"]["name"]},
        headers=admin_headers,
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
    assert any(row["id"] == created["id"] for row in result["data"])


async def test_update_tag(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    created = await _create_tag(client, admin_headers)
    new_name = f"tag-{uuid4().hex[:12]}"
    response = await client.patch(
        f"{_TAGS_LIST_PATH}/{created['id']}",
        json={"name": new_name},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Tag updated"}


async def test_delete_tag(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    created = await _create_tag(client, admin_headers)
    response = await client.delete(f"{_TAGS_LIST_PATH}/{created['id']}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json() == {"message": "Tag deleted"}


async def test_delete_already_deleted_tag_as_admin(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    created = await _create_tag(client, admin_headers)
    first = await client.delete(f"{_TAGS_LIST_PATH}/{created['id']}", headers=admin_headers)
    assert first.status_code == 200
    second = await client.delete(f"{_TAGS_LIST_PATH}/{created['id']}", headers=admin_headers)
    assert second.status_code == 404
    assert second.json() == problem_body("Tag already deleted (soft delete).", 404, "not_found")


async def test_delete_db_tag(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    created = await _create_tag(client, admin_headers)
    response = await client.delete(
        f"{_TAGS_LIST_PATH}/{created['id']}/db",
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Tag deleted from the database"}


async def test_erase_db_tag_forbidden_for_regular_user(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    created = await _create_tag(client, admin_headers)
    _, regular_headers = await _create_regular_user(client, admin_headers)
    response = await client.delete(
        f"{_TAGS_LIST_PATH}/{created['id']}/db",
        headers=regular_headers,
    )
    assert response.status_code == 403
    assert response.json() == problem_body("You do not have enough privileges.", 403, "forbidden")


async def test_delete_tag_forbidden_when_assigned_to_post(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    created = await _create_tag(client, admin_headers)
    user_id = await _admin_user_id(client, admin_headers)
    post_response = await client.post(
        f"/api/v1/blog/posts/user/{user_id}",
        json={
            "title": f"post-{uuid4()}",
            "text": "This is the content of my test post.",
            "tag_ids": [created["id"]],
        },
        headers=admin_headers,
    )
    assert post_response.status_code == 201, post_response.text

    response = await client.delete(f"{_TAGS_LIST_PATH}/{created['id']}", headers=admin_headers)
    assert response.status_code == 403
    assert response.json() == problem_body(
        "Tag cannot be deleted while it is assigned to a post", 403, "forbidden"
    )


async def test_create_tag_invalidates_list_cache(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    name = f"tag-{uuid4().hex[:12]}"
    list_params = {"name": name}
    warm = await client.get(_TAGS_LIST_PATH, params=list_params, headers=admin_headers)
    assert warm.status_code == 200
    assert warm.json()["data"] == []
    created = await client.post(_TAGS_LIST_PATH, json={"name": name}, headers=admin_headers)
    assert created.status_code == 201, created.text
    response = await client.get(_TAGS_LIST_PATH, params=list_params, headers=admin_headers)
    assert response.status_code == 200
    ids = [item["id"] for item in response.json()["data"]]
    assert created.json()["id"] in ids


async def test_tags_list_rate_limiter_blocks_after_configured_limit(
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
            "path": _TAGS_LIST_PATH,
            "limit": 1,
            "period": 3600,
        },
        headers=admin_headers,
    )
    assert rate_limit_response.status_code == 201, rate_limit_response.text
    rate_limit_id = rate_limit_response.json()["id"]

    await _clear_rate_limit_keys(admin_id, _TAGS_LIST_PATH)
    try:
        first_response = await client.get(_TAGS_LIST_PATH, headers=admin_headers)
        second_response = await client.get(_TAGS_LIST_PATH, headers=admin_headers)
        assert first_response.status_code == 200
        assert second_response.status_code == 429
        assert second_response.json() == problem_body(
            "Rate limit exceeded.", 429, "rate_limit_exceeded"
        )
    finally:
        await _clear_rate_limit_keys(admin_id, _TAGS_LIST_PATH)
        await client.delete(
            f"/api/v1/system/rate-limits/{rate_limit_id}/tier/{default_tier['id']}/db",
            headers=admin_headers,
        )
