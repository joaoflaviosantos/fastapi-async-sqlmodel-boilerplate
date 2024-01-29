# Built-in Dependencies
from uuid import uuid4

# Third-Party Dependencies
from fastapi.testclient import TestClient

# Local Dependencies
from src.core.utils.rate_limit import sanitize_path
from src.core.config import settings
from tests.helper import _get_token

# Test data: admin/superuser 'test' credentials
ADMIN_USERNAME = settings.ADMIN_USERNAME
ADMIN_PASSWORD = settings.ADMIN_PASSWORD

# Test global variables
test_rate_limit_id = None
test_rate_limit = {
    "name": "Test Rate Limit",
    "path": "/api/v1/system/task",
    "limit": 100,
    "period": 3600,
}


def test_post_rate_limit(client: TestClient) -> None:
    global test_rate_limit_id

    token = _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = client.post(
        f"/api/v1/system/tier/{settings.TIER_NAME_DEFAULT}/rate_limit",
        json=test_rate_limit,
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )
    test_rate_limit_id = response.json()["id"]

    assert test_rate_limit_id is not None
    assert response.status_code == 201


def test_post_invalid_rate_limit_tier_name(client: TestClient) -> None:
    token = _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    invalid_tier_name = f"invalid-tier-{uuid4()}"

    response = client.post(
        f"/api/v1/system/tier/{invalid_tier_name}/rate_limit",
        json=test_rate_limit,
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 404


def test_post_invalid_rate_limit_path(client: TestClient) -> None:
    token = _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    invalid_test_rate_limit = test_rate_limit.copy()
    invalid_test_rate_limit["path"] = "/api/v1/invalid/route"

    response = client.post(
        f"/api/v1/system/tier/{settings.TIER_NAME_DEFAULT}/rate_limit",
        json=invalid_test_rate_limit,
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert response.status_code == 422


def test_get_multiple_rate_limits(client: TestClient) -> None:
    token = _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = client.get(
        f"/api/v1/system/tier/{settings.TIER_NAME_DEFAULT}/rate_limits",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    assert "data" in response.json()
    assert response.status_code == 200


def test_get_rate_limit(client: TestClient) -> None:
    token = _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = client.get(
        f"/api/v1/system/tier/{settings.TIER_NAME_DEFAULT}/rate_limit/{test_rate_limit_id}",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )
    rate_limit = response.json()

    assert response.status_code == 200
    assert rate_limit["name"] == test_rate_limit["name"]
    assert rate_limit["path"] == sanitize_path(test_rate_limit["path"])
    assert rate_limit["limit"] == test_rate_limit["limit"]
    assert rate_limit["period"] == test_rate_limit["period"]


def test_update_rate_limit(client: TestClient) -> None:
    token = _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    updated_rate_limit = {
        "name": "Updated Test Rate Limit",
        "limit": 200,
        "period": 7200,
    }

    response = client.patch(
        f"/api/v1/system/tier/{settings.TIER_NAME_DEFAULT}/rate_limit/{test_rate_limit_id}",
        json=updated_rate_limit,
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )
    assert response.status_code == 200


def test_erase_rate_limit(client: TestClient) -> None:
    token = _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = client.delete(
        f"/api/v1/system/tier/{settings.TIER_NAME_DEFAULT}/rate_limit/{test_rate_limit_id}",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )
    assert response.status_code == 200
