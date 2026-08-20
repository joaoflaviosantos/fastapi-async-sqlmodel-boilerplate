# Built-in Dependencies
from unittest.mock import patch

# Third-Party Dependencies
import pytest
from httpx import AsyncClient

# Local Dependencies
from src.core.exceptions.problem import problem_body
from src.core.utils.rate_limit import sanitize_path

pytestmark = pytest.mark.integration

_LOGIN_PATH = "/api/v1/system/auth/login"


async def _login(client: AsyncClient, settings):
    return await client.post(
        _LOGIN_PATH,
        data={
            "username": settings.USER_FIRST_ADMIN_USERNAME,
            "password": settings.USER_FIRST_ADMIN_PASSWORD,
        },
        headers={"content-type": "application/x-www-form-urlencoded"},
    )


async def _clear_login_rate_limit_keys() -> None:
    from src.core.utils import rate_limit

    pattern = f"ratelimit:127.0.0.1:{sanitize_path(_LOGIN_PATH)}:*"
    keys = await rate_limit.client.keys(pattern)  # type: ignore[union-attr]
    if keys:
        await rate_limit.client.delete(*keys)  # type: ignore[union-attr]


def _set_cookie_header(response) -> str:
    return "; ".join(response.headers.get_list("set-cookie")).lower()


async def test_auth_login(client: AsyncClient, settings) -> None:
    response = await _login(client, settings)
    body = response.json()
    assert response.status_code == 200
    assert body["access_token"] is not None
    assert body["token_type"] == "bearer"
    assert response.cookies.get("refresh_token")


async def test_auth_refresh(client: AsyncClient, settings) -> None:
    login = await _login(client, settings)
    assert login.status_code == 200
    refresh_token = login.cookies.get("refresh_token")
    assert refresh_token

    response = await client.post(
        "/api/v1/system/auth/refresh",
        headers={"Cookie": f"refresh_token={refresh_token}"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["access_token"] is not None
    assert body["token_type"] == "bearer"


async def test_auth_refresh_unauthorized(client: AsyncClient) -> None:
    response = await client.post("/api/v1/system/auth/refresh")
    assert response.status_code == 401


async def test_auth_logout(client: AsyncClient, settings) -> None:
    login = await _login(client, settings)
    assert login.status_code == 200
    access_token = login.json()["access_token"]

    response = await client.post(
        "/api/v1/system/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Logged out successfully"}
    set_cookie = _set_cookie_header(response)
    assert "refresh_token=" in set_cookie
    assert "max-age=0" in set_cookie


async def test_auth_logout_unauthorized(client: AsyncClient) -> None:
    response = await client.post("/api/v1/system/auth/logout")
    assert response.status_code == 401


async def test_auth_login_rate_limiter_blocks_after_default_limit(
    client: AsyncClient, settings
) -> None:
    await _clear_login_rate_limit_keys()
    try:
        with patch("src.apps.system.rate_limits.deps.DEFAULT_LIMIT", 1):
            first_response = await _login(client, settings)
            second_response = await _login(client, settings)
        assert first_response.status_code == 200, first_response.text
        assert second_response.status_code == 429
        assert second_response.json() == problem_body(
            "Rate limit exceeded.", 429, "rate_limit_exceeded"
        )
    finally:
        await _clear_login_rate_limit_keys()
