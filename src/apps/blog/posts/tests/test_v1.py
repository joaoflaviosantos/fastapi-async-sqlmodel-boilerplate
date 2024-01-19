# Third-Party Dependencies
from fastapi.testclient import TestClient

# Local Dependencies
from src.core.config import settings
from tests.helper import _get_token

# Test data: admin/superuser 'test' credentials
ADMIN_USERNAME = settings.ADMIN_USERNAME
ADMIN_PASSWORD = settings.ADMIN_PASSWORD

# Test global variables
test_post_id = None
test_post = {
    "title": "This is my test post",
    "text": "This is the content of my test post.",
    "media_url": "https://www.imageurl.com/test_post.jpg",
}


def test_post_post(client: TestClient) -> None:
    global test_post_id

    token = _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)
    response = client.post(
        f"/api/v1/blog/{ADMIN_USERNAME}/post",
        json=test_post,
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )
    test_post_id = response.json()["id"]

    assert test_post_id is not None
    assert response.status_code == 201


def test_get_user_post(client: TestClient) -> None:

    response = client.get(f"/api/v1/blog/{ADMIN_USERNAME}/post/{test_post_id}")
    post = response.json()

    assert response.status_code == 200
    assert post["title"] == test_post["title"]
    assert post["text"] == test_post["text"]
    assert post["media_url"] == test_post["media_url"]


def test_get_multiple_posts(client: TestClient) -> None:
    response = client.get(f"/api/v1/blog/{ADMIN_USERNAME}/posts")

    assert response.status_code == 200


def test_update_post(client: TestClient) -> None:
    token = _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = client.patch(
        f"/api/v1/blog/{ADMIN_USERNAME}/post/{test_post_id}",
        json=test_post,
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )
    assert response.status_code == 200


def test_delete_post(client: TestClient) -> None:
    token = _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = client.delete(
        f"/api/v1/blog/{ADMIN_USERNAME}/post/{test_post_id}",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )
    assert response.status_code == 200


def test_delete_db_post(client: TestClient) -> None:
    token = _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = client.delete(
        f"/api/v1/blog/{ADMIN_USERNAME}/db_post/{test_post_id}",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )
    assert response.status_code == 200
