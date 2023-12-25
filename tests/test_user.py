from fastapi.testclient import TestClient

from src.app.main import app
from src.app.core.config import settings
from .helper import _get_token

test_name = settings.TEST_NAME
test_username = settings.TEST_USERNAME
test_email = settings.TEST_EMAIL
test_password = settings.TEST_PASSWORD

admin_username = settings.ADMIN_USERNAME
admin_password = settings.ADMIN_PASSWORD

client = TestClient(app)

def test_post_user(client: TestClient) -> None:
    response = client.post(
        "/api/v1/user",
        json = {
            "name": test_name,
            "username": test_username,
            "email": test_email,
            "password": test_password
        }
    )
    assert response.status_code == 201

def test_get_user(client: TestClient) -> None:
    response = client.get(
        f"/api/v1/user/{test_username}"
    )
    assert response.status_code == 200

def test_get_multiple_users(client: TestClient) -> None:
    response = client.get(
        "/api/v1/users"
    )
    assert response.status_code == 200

def test_update_user(client: TestClient) -> None:
    token = _get_token(
        username=test_username, 
        password=test_password, 
        client=client
    )
    
    response = client.patch(
        f"/api/v1/user/{test_username}",
        json={
            "name": f"Updated {test_name}"
        },
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'}
    )
    assert response.status_code == 200

def test_delete_user(client: TestClient) -> None:
    token = _get_token(
        username=test_username, 
        password=test_password, 
        client=client
    )

    response = client.delete(
        f"/api/v1/user/{test_username}",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'}
    )
    assert response.status_code == 200

def test_delete_db_user(client: TestClient) -> None:
    token = _get_token(
        username=admin_username, 
        password=admin_password, 
        client=client
    )

    response = client.delete(
        f"/api/v1/db_user/{test_username}",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'}
    )
    assert response.status_code == 200
