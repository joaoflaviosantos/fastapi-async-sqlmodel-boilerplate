# Built-in Dependencies
from uuid import uuid4

# Third-Party Dependencies
import pytest
from httpx import AsyncClient

# Local Dependencies
from src.core.exceptions.problem import problem_body
from tests.helper import _create_regular_user

pytestmark = pytest.mark.integration

_POST_MEDIA_URL = "https://www.imageurl.com/test_post.jpg"


async def _admin_user_id(client: AsyncClient, admin_headers: dict[str, str]) -> str:
    response = await client.get("/api/v1/system/users/me/", headers=admin_headers)
    assert response.status_code == 200
    return response.json()["id"]


async def _create_tag(client: AsyncClient, headers: dict[str, str]) -> dict:
    payload = {"name": f"tag-{uuid4().hex[:12]}"}
    response = await client.post("/api/v1/blog/tags", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return {"id": response.json()["id"], "payload": payload}


async def _create_post(client: AsyncClient, admin_headers: dict[str, str], user_id: str) -> dict:
    tag = await _create_tag(client, admin_headers)
    payload = {
        "title": f"post-{uuid4()}",
        "text": "This is the content of my test post.",
        "media_url": _POST_MEDIA_URL,
        "tag_ids": [tag["id"]],
    }
    response = await client.post(
        f"/api/v1/blog/posts/user/{user_id}",
        json=payload,
        headers=admin_headers,
    )
    assert response.status_code == 201, response.text
    return {
        "id": response.json()["id"],
        "payload": payload,
        "user_id": user_id,
        "tag_id": tag["id"],
        "body": response.json(),
    }


async def test_create_post(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    user_id = await _admin_user_id(client, admin_headers)
    created = await _create_post(client, admin_headers, user_id)
    assert created["id"]
    assert created["body"]["tags"]
    assert created["body"]["tags"][0]["id"] == created["tag_id"]


async def test_create_post_requires_tag(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    user_id = await _admin_user_id(client, admin_headers)
    response = await client.post(
        f"/api/v1/blog/posts/user/{user_id}",
        json={
            "title": f"post-{uuid4()}",
            "text": "This is the content of my test post.",
            "media_url": _POST_MEDIA_URL,
        },
        headers=admin_headers,
    )
    assert response.status_code == 422


async def test_create_post_rejects_empty_tag_ids(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    user_id = await _admin_user_id(client, admin_headers)
    response = await client.post(
        f"/api/v1/blog/posts/user/{user_id}",
        json={
            "title": f"post-{uuid4()}",
            "text": "This is the content of my test post.",
            "media_url": _POST_MEDIA_URL,
            "tag_ids": [],
        },
        headers=admin_headers,
    )
    assert response.status_code == 422


async def test_create_post_unauthorized(client: AsyncClient) -> None:
    response = await client.post(
        f"/api/v1/blog/posts/user/{uuid4()}",
        json={
            "title": f"post-{uuid4()}",
            "text": "content",
            "media_url": _POST_MEDIA_URL,
            "tag_ids": [str(uuid4())],
        },
    )
    assert response.status_code == 401


async def test_get_created_post(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    user_id = await _admin_user_id(client, admin_headers)
    created = await _create_post(client, admin_headers, user_id)
    response = await client.get(
        f"/api/v1/blog/posts/{created['id']}/user/{user_id}",
        headers=admin_headers,
    )
    assert response.status_code == 200
    post = response.json()
    assert post["title"] == created["payload"]["title"]
    assert post["text"] == created["payload"]["text"]
    assert post["media_url"] == created["payload"]["media_url"]
    assert post["tags"][0]["id"] == created["tag_id"]


async def test_get_multiple_user_posts(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    user_id = await _admin_user_id(client, admin_headers)
    await _create_post(client, admin_headers, user_id)
    response = await client.get(
        f"/api/v1/blog/posts/user/{user_id}",
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


async def test_filter_posts_by_tag(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    user_id = await _admin_user_id(client, admin_headers)
    matched = await _create_post(client, admin_headers, user_id)
    await _create_post(client, admin_headers, user_id)

    response = await client.get(
        f"/api/v1/blog/posts/user/{user_id}",
        params={"tag_id": matched["tag_id"]},
        headers=admin_headers,
    )
    assert response.status_code == 200
    ids = [item["id"] for item in response.json()["data"]]
    assert matched["id"] in ids
    assert all(
        matched["tag_id"] in [tag["id"] for tag in item["tags"]] for item in response.json()["data"]
    )


async def test_update_post(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    user_id = await _admin_user_id(client, admin_headers)
    created = await _create_post(client, admin_headers, user_id)
    response = await client.patch(
        f"/api/v1/blog/posts/{created['id']}/user/{user_id}",
        json={"title": created["payload"]["title"], "text": created["payload"]["text"]},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Post updated"}


async def test_update_post_rejects_empty_tag_ids(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    user_id = await _admin_user_id(client, admin_headers)
    created = await _create_post(client, admin_headers, user_id)
    response = await client.patch(
        f"/api/v1/blog/posts/{created['id']}/user/{user_id}",
        json={"tag_ids": []},
        headers=admin_headers,
    )
    assert response.status_code == 422


async def test_delete_post(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    user_id = await _admin_user_id(client, admin_headers)
    created = await _create_post(client, admin_headers, user_id)
    response = await client.delete(
        f"/api/v1/blog/posts/{created['id']}/user/{user_id}",
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Post deleted"}


async def test_delete_already_deleted_post_as_admin(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    user_id = await _admin_user_id(client, admin_headers)
    created = await _create_post(client, admin_headers, user_id)
    first = await client.delete(
        f"/api/v1/blog/posts/{created['id']}/user/{user_id}",
        headers=admin_headers,
    )
    assert first.status_code == 200
    second = await client.delete(
        f"/api/v1/blog/posts/{created['id']}/user/{user_id}",
        headers=admin_headers,
    )
    assert second.status_code == 404
    assert second.json() == problem_body("Post already deleted (soft delete).", 404, "not_found")


async def test_delete_db_post(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    user_id = await _admin_user_id(client, admin_headers)
    created = await _create_post(client, admin_headers, user_id)
    response = await client.delete(
        f"/api/v1/blog/posts/{created['id']}/user/{user_id}/db",
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Post deleted from the database"}


async def test_erase_db_post_forbidden_for_regular_user(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    user_id = await _admin_user_id(client, admin_headers)
    created = await _create_post(client, admin_headers, user_id)
    _, regular_headers = await _create_regular_user(client, admin_headers)
    response = await client.delete(
        f"/api/v1/blog/posts/{created['id']}/user/{user_id}/db",
        headers=regular_headers,
    )
    assert response.status_code == 403
    assert response.json() == problem_body("You do not have enough privileges.", 403, "forbidden")


async def test_create_post_invalidates_list_cache(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    user_id = await _admin_user_id(client, admin_headers)
    list_url = f"/api/v1/blog/posts/user/{user_id}"
    warm = await client.get(list_url, headers=admin_headers)
    assert warm.status_code == 200
    created = await _create_post(client, admin_headers, user_id)
    response = await client.get(list_url, headers=admin_headers)
    assert response.status_code == 200
    ids = [item["id"] for item in response.json()["data"]]
    assert created["id"] in ids


async def test_patch_post_invalidates_item_cache(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    user_id = await _admin_user_id(client, admin_headers)
    created = await _create_post(client, admin_headers, user_id)
    item_url = f"/api/v1/blog/posts/{created['id']}/user/{user_id}"
    first = await client.get(item_url, headers=admin_headers)
    assert first.status_code == 200
    assert first.json()["title"] == created["payload"]["title"]
    new_title = f"updated-{uuid4()}"
    patch = await client.patch(
        item_url,
        json={"title": new_title},
        headers=admin_headers,
    )
    assert patch.status_code == 200
    second = await client.get(item_url, headers=admin_headers)
    assert second.status_code == 200
    assert second.json()["title"] == new_title
