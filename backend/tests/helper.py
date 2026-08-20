# Built-in Dependencies
from uuid import uuid4

# Third-Party Dependencies
from httpx import AsyncClient


async def _get_token(username: str, password: str, client: AsyncClient):
    """
    Obtain an authentication token from the login endpoint.
    """
    return await client.post(
        "/api/v1/system/auth/login",
        data={"username": username, "password": password},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )


async def _auth_headers(client: AsyncClient, username: str, password: str) -> dict[str, str]:
    token = await _get_token(username=username, password=password, client=client)
    assert token.status_code == 200, token.text
    return {"Authorization": f"Bearer {token.json()['access_token']}"}


async def _create_user(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    name: str,
    username: str,
    email: str,
    password: str,
) -> str:
    """
    Create a disposable user and return its id.
    """
    response = await client.post(
        "/api/v1/system/users",
        json={
            "name": name,
            "username": username,
            "email": email,
            "password": password,
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _create_regular_user(
    client: AsyncClient,
    admin_headers: dict[str, str],
) -> tuple[str, dict[str, str]]:
    """
    Create a unique non-admin user and return (user_id, auth headers).
    """
    suffix = uuid4().hex[:12]
    username = f"u{suffix}"
    password = "Str1ngst!"
    user_id = await _create_user(
        client,
        admin_headers,
        name="Regular User",
        username=username,
        email=f"{username}@tester.com",
        password=password,
    )
    headers = await _auth_headers(client, username, password)
    return user_id, headers
