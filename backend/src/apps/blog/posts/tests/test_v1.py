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
test_post_user_id = None
test_post_id = None
test_post = {
    "title": "This is my test post",
    "text": "This is the content of my test post.",
    "media_url": "https://www.imageurl.com/test_post.jpg",
}


@pytest.mark.asyncio
async def test_get_post_user_data(client: AsyncClient) -> None:
    global test_post_user_id
    assert test_post_user_id is None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.get(
        url="/api/v1/system/users/me/",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    test_post_user_id = response.json()["id"]

    assert response.status_code == 200
    assert test_post_user_id is not None
    assert response.json()["username"] == ADMIN_USERNAME


@pytest.mark.asyncio
async def test_create_post(client: AsyncClient) -> None:
    global test_post_id
    global test_post_user_id
    assert test_post_id is None
    assert test_post_user_id is not None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.post(
        url=f"/api/v1/blog/posts/user/{test_post_user_id}",
        json=test_post,
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    test_post_id = response.json()["id"]

    assert response.status_code == 201
    assert test_post_id is not None


@pytest.mark.asyncio
async def test_get_created_post(client: AsyncClient) -> None:
    global test_post_id
    global test_post_user_id
    assert test_post_id is not None
    assert test_post_user_id is not None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.get(
        url=f"/api/v1/blog/posts/{test_post_id}/user/{test_post_user_id}",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    post = response.json()

    assert response.status_code == 200
    assert post["title"] == test_post["title"]
    assert post["text"] == test_post["text"]
    assert post["media_url"] == test_post["media_url"]


@pytest.mark.asyncio
async def test_get_multiple_user_posts(client: AsyncClient) -> None:
    global test_post_user_id
    assert test_post_user_id is not None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.get(
        url=f"/api/v1/blog/posts/user/{test_post_user_id}",
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
async def test_update_post(client: AsyncClient) -> None:
    global test_post_id
    global test_post_user_id
    assert test_post_id is not None
    assert test_post_user_id is not None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.patch(
        url=f"/api/v1/blog/posts/{test_post_id}/user/{test_post_user_id}",
        json=test_post,
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Post updated"}


@pytest.mark.asyncio
async def test_delete_post(client: AsyncClient) -> None:
    global test_post_id
    global test_post_user_id
    assert test_post_id is not None
    assert test_post_user_id is not None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.delete(
        url=f"/api/v1/blog/posts/{test_post_id}/user/{test_post_user_id}",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Post deleted"}


@pytest.mark.asyncio
async def test_delete_already_deleted_post_as_admin(client: AsyncClient) -> None:
    global test_post_id
    global test_post_user_id
    assert test_post_id is not None
    assert test_post_user_id is not None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.delete(
        url=f"/api/v1/blog/posts/{test_post_id}/user/{test_post_user_id}",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Post already deleted (soft delete)."}


@pytest.mark.asyncio
async def test_delete_db_post(client: AsyncClient) -> None:
    global test_post_id
    global test_post_user_id
    assert test_post_id is not None
    assert test_post_user_id is not None

    token = await _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = await client.delete(
        url=f"/api/v1/blog/posts/{test_post_id}/user/{test_post_user_id}/db",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Post deleted from the database"}
