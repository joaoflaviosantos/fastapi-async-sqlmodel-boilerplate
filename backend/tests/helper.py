# Third-Party Dependencies
from fastapi.testclient import TestClient

# Local Dependencies
from src.core.config import settings


def _get_token(username: str, password: str, client: TestClient):
    """
    Helper function to obtain an authentication token by making a login request to the authentication endpoint.

    Parameters
    ----------
    username : str
        The username for authentication.
    password : str
        The password for authentication.
    client : TestClient
        The FastAPI test client instance.

    Returns
    ----------
    response
        The response object containing the authentication token.

    Example
    ----------
    Obtaining an authentication token:
    ```python
    token_response = _get_token("example_user", "example_password", test_client_instance)
    ```
    """
    return client.post(
        "/api/v1/system/auth/login",
        data={"username": username, "password": password},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )


def _ensure_test_user_exists(client: TestClient) -> str:
    """
    Helper function to ensure the test user exists and return their ID.
    If the user doesn't exist, creates it.

    Parameters
    ----------
    client : TestClient
        The FastAPI test client instance.

    Returns
    ----------
    str
        The ID of the test user.

    Example
    ----------
    Ensuring test user exists:
    ```python
    user_id = _ensure_test_user_exists(test_client_instance)
    ```
    """
    # Get admin token
    admin_token = _get_token(
        username=settings.ADMIN_USERNAME, password=settings.ADMIN_PASSWORD, client=client
    )

    if admin_token.status_code != 200:
        raise Exception("Failed to get admin token")

    admin_access_token = admin_token.json()["access_token"]

    # Try to find the test user
    response = client.get(
        "/api/v1/system/users",
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )

    if response.status_code == 200:
        users = response.json().get("data", [])
        existing_user = next((u for u in users if u["email"] == settings.TEST_EMAIL), None)
        if existing_user:
            return existing_user["id"]

    # User doesn't exist, try to create it
    response = client.post(
        "/api/v1/system/users",
        json={
            "name": settings.TEST_NAME,
            "username": settings.TEST_USERNAME,
            "email": settings.TEST_EMAIL,
            "password": settings.TEST_PASSWORD,
        },
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )

    if response.status_code == 201:
        return response.json()["id"]
    elif response.status_code == 422 and "already registered" in str(response.json()):
        # User exists but is soft-deleted - we can't access it via API
        # This is a limitation of the current test setup
        # For now, we'll raise an exception to indicate this issue
        raise Exception(f"Test user exists but is soft-deleted: {response.json()}")
    else:
        raise Exception(f"Failed to create test user: {response.json()}")
