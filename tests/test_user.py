from fastapi.testclient import TestClient

from src.main import app
from src.core.config import settings
from .helper import _get_token


client = TestClient(app)

def test_post_user(client: TestClient) -> None:
    response = client.post(
        "/api/v1/system/user",
        json = {
            "name": settings.TEST_NAME,
            "username": settings.TEST_USERNAME,
            "email": settings.TEST_EMAIL,
            "password": settings.TEST_PASSWORD
        }
    )
    assert response.status_code == 201

def test_get_user(client: TestClient) -> None:
    response = client.get(
        f"/api/v1/system/user/{settings.TEST_USERNAME}"
    )
    assert response.status_code == 200

def test_get_multiple_users(client: TestClient) -> None:
    response = client.get(
        "/api/v1/system/users"
    )
    assert response.status_code == 200

def test_update_user(client: TestClient) -> None:
    token = _get_token(
        username=settings.TEST_USERNAME, 
        password=settings.TEST_PASSWORD, 
        client=client
    )
    
    response = client.patch(
        f"/api/v1/system/user/{settings.TEST_USERNAME}",
        json={
            "name": f"Updated {settings.TEST_NAME}"
        },
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'}
    )
    assert response.status_code == 200

def test_delete_user(client: TestClient) -> None:
    token = _get_token(
        username=settings.TEST_USERNAME, 
        password=settings.TEST_PASSWORD, 
        client=client
    )

    response = client.delete(
        f"/api/v1/system/user/{settings.TEST_USERNAME}",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'}
    )
    assert response.status_code == 200

def test_delete_db_user(client: TestClient) -> None:
    token = _get_token(
        username=settings.ADMIN_USERNAME, 
        password=settings.ADMIN_PASSWORD, 
        client=client
    )

    response = client.delete(
        f"/api/v1/system/db_user/{settings.TEST_USERNAME}",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'}
    )
    assert response.status_code == 200
