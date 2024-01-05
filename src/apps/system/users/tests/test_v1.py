# Third-Party Dependencies
from fastapi.testclient import TestClient

# Local Dependencies
from src.core.config import settings
from tests.helper import _get_token

# Test data: 'common user'
TEST_NAME = settings.TEST_NAME
TEST_USERNAME = settings.TEST_USERNAME
TEST_EMAIL = settings.TEST_EMAIL
TEST_PASSWORD = settings.TEST_PASSWORD

# Test data: admin/superuser 'test' credentials
ADMIN_USERNAME = settings.ADMIN_USERNAME
ADMIN_PASSWORD = settings.ADMIN_PASSWORD

def test_post_user(client: TestClient) -> None:
    response = client.post(
        "/api/v1/system/user",
        json = {
            "name": TEST_NAME,
            "username": TEST_USERNAME,
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
    )
    assert response.status_code == 201


def test_get_user(client: TestClient) -> None:
    response = client.get(
        f"/api/v1/system/user/{TEST_USERNAME}"
    )
    assert response.status_code == 200


def test_get_multiple_users(client: TestClient) -> None:
    response = client.get(
        "/api/v1/system/users"
    )
    assert response.status_code == 200


def test_update_user(client: TestClient) -> None:
    token = _get_token(
        username=TEST_USERNAME, 
        password=TEST_PASSWORD, 
        client=client
    )
    
    response = client.patch(
        f"/api/v1/system/user/{TEST_USERNAME}",
        json={
            "name": f"Updated {TEST_NAME}"
        },
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'}
    )
    assert response.status_code == 200


def test_delete_user(client: TestClient) -> None:
    token = _get_token(
        username=TEST_USERNAME, 
        password=TEST_PASSWORD, 
        client=client
    )

    response = client.delete(
        f"/api/v1/system/user/{TEST_USERNAME}",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'}
    )
    assert response.status_code == 200


def test_delete_db_user(client: TestClient) -> None:
    token = _get_token(
        username=ADMIN_USERNAME, 
        password=ADMIN_PASSWORD, 
        client=client
    )

    response = client.delete(
        f"/api/v1/system/db_user/{TEST_USERNAME}",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'}
    )
    assert response.status_code == 200
