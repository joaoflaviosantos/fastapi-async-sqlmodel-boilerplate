# Third-Party Dependencies
from fastapi.testclient import TestClient

# Local Dependencies
from src.core.config import settings
from tests.helper import _get_token

# Test data: admin/superuser 'test' credentials
ADMIN_USERNAME = settings.ADMIN_USERNAME
ADMIN_PASSWORD = settings.ADMIN_PASSWORD

# Test global variables
test_tier_id = None
test_tier = {"name": "Test Tier"}


def test_post_tier(client: TestClient) -> None:
    global test_tier_id
    assert test_tier_id is None

    token = _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = client.post(
        "/api/v1/system/tiers",
        json=test_tier,
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    test_tier_id = response.json()["id"]

    assert test_tier_id is not None
    assert response.status_code == 201


def test_get_multiple_tiers(client: TestClient) -> None:
    response = client.get("/api/v1/system/tiers")

    assert len(response.json()["data"]) > 0
    assert response.status_code == 200


def test_get_tier(client: TestClient) -> None:
    global test_tier_id
    assert test_tier_id is not None

    response = client.get(f"/api/v1/system/tiers/{test_tier_id}")

    assert response.json()["name"] == test_tier["name"]
    assert response.status_code == 200


def test_update_tier(client: TestClient) -> None:
    global test_tier_id
    assert test_tier_id is not None

    token = _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    updated_tier_name = "Updated Test Tier"

    response = client.patch(
        f"/api/v1/system/tiers/{test_tier_id}",
        json={"name": updated_tier_name},
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.json() == {"message": "Tier updated"}
    assert response.status_code == 200


def test_delete_tier(client: TestClient) -> None:
    global test_tier_id
    assert test_tier_id is not None

    # Obter token de autenticação
    token = _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = client.delete(
        f"/api/v1/system/tiers/{test_tier_id}",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.json() == {"message": "Tier deleted"}
    assert response.status_code == 200
