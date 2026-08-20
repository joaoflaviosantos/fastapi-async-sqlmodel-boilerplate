# Built-in Dependencies
from uuid import uuid4

# Third-Party Dependencies
import pytest
from httpx import AsyncClient

# Local Dependencies
from src.core.exceptions.problem import problem_body
from tests.helper import _auth_headers, _create_regular_user, _create_user

pytestmark = pytest.mark.integration


async def _create_disposable_user(
    client: AsyncClient, admin_headers: dict[str, str]
) -> tuple[str, str, str]:
    suffix = uuid4().hex[:12]
    username = f"u{suffix}"
    password = "Str1ngst!"
    user_id = await _create_user(
        client,
        admin_headers,
        name="Disposable User",
        username=username,
        email=f"{username}@tester.com",
        password=password,
    )
    return user_id, username, password


async def test_post_user(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    user_id, _, _ = await _create_disposable_user(client, admin_headers)
    assert user_id


async def test_post_user_unauthorized(client: AsyncClient) -> None:
    suffix = uuid4().hex[:12]
    response = await client.post(
        "/api/v1/system/users",
        json={
            "name": "Disposable User",
            "username": f"u{suffix}",
            "email": f"u{suffix}@tester.com",
            "password": "Str1ngst!",
        },
    )
    assert response.status_code == 401


async def test_get_own_user_data(
    client: AsyncClient, admin_headers: dict[str, str], settings
) -> None:
    response = await client.get("/api/v1/system/users/me/", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == settings.USER_FIRST_ADMIN_USERNAME


async def test_get_user(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    user_id, username, _ = await _create_disposable_user(client, admin_headers)
    response = await client.get(f"/api/v1/system/users/{user_id}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["username"] == username


async def test_get_multiple_users(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    response = await client.get("/api/v1/system/users", headers=admin_headers)
    assert response.status_code == 200
    result = response.json()
    assert "data" in result
    assert isinstance(result["data"], list)
    assert len(result["data"]) > 0
    assert "total_count" in result
    assert "has_more" in result
    assert "page" in result
    assert "items_per_page" in result


async def test_update_your_own_user(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    user_id, username, password = await _create_disposable_user(client, admin_headers)
    headers = await _auth_headers(client, username, password)
    response = await client.patch(
        f"/api/v1/system/users/{user_id}",
        json={"name": "Updated Disposable User"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json() == {"message": "User updated"}


async def test_update_user_as_admin(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    user_id, _, _ = await _create_disposable_user(client, admin_headers)
    response = await client.patch(
        f"/api/v1/system/users/{user_id}",
        json={"name": "Updated Disposable User (admin)"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json() == {"message": "User updated"}


async def test_get_user_rate_limits(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    user_id, _, _ = await _create_disposable_user(client, admin_headers)
    response = await client.get(
        f"/api/v1/system/users/{user_id}/rate-limits",
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert "tier_rate_limits" in response.json()


async def test_get_user_rate_limits_forbidden_for_regular_user(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    user_id, regular_headers = await _create_regular_user(client, admin_headers)
    response = await client.get(
        f"/api/v1/system/users/{user_id}/rate-limits",
        headers=regular_headers,
    )
    assert response.status_code == 403
    assert response.json() == problem_body("You do not have enough privileges.", 403, "forbidden")


async def test_get_user_tier(client: AsyncClient, admin_headers: dict[str, str], settings) -> None:
    user_id, _, _ = await _create_disposable_user(client, admin_headers)
    response = await client.get(
        f"/api/v1/system/users/{user_id}/tier",
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["tier_name"] == settings.TIER_NAME_DEFAULT


async def test_delete_user(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    user_id, username, password = await _create_disposable_user(client, admin_headers)
    headers = await _auth_headers(client, username, password)
    response = await client.delete(f"/api/v1/system/users/{user_id}", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"message": "User deleted"}


async def test_delete_already_deleted_user_as_admin(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    user_id, username, password = await _create_disposable_user(client, admin_headers)
    headers = await _auth_headers(client, username, password)
    first = await client.delete(f"/api/v1/system/users/{user_id}", headers=headers)
    assert first.status_code == 200
    second = await client.delete(f"/api/v1/system/users/{user_id}", headers=admin_headers)
    assert second.status_code == 404
    assert second.json() == problem_body("User already deleted (soft delete).", 404, "not_found")


async def test_delete_db_user(client: AsyncClient, admin_headers: dict[str, str]) -> None:
    user_id, _, _ = await _create_disposable_user(client, admin_headers)
    response = await client.delete(
        f"/api/v1/system/users/{user_id}/db",
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json() == {"message": "User deleted from the database"}


async def test_erase_db_user_forbidden_for_regular_user(
    client: AsyncClient, admin_headers: dict[str, str]
) -> None:
    user_id, regular_headers = await _create_regular_user(client, admin_headers)
    response = await client.delete(
        f"/api/v1/system/users/{user_id}/db",
        headers=regular_headers,
    )
    assert response.status_code == 403
    assert response.json() == problem_body("You do not have enough privileges.", 403, "forbidden")
