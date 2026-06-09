# Built-in Dependencies
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from locust.clients import HttpSession

# Local Dependencies
from config import ADMIN_EMAIL, ADMIN_PASSWORD, API_V1_PREFIX


def login(client: HttpSession, email: str = ADMIN_EMAIL, password: str = ADMIN_PASSWORD) -> str:
    """
    Authenticate with the API and return the access token.

    Parameters
    ----------
    client : HttpSession
        Locust HTTP client.
    email : str
        User email for login.
    password : str
        User password for login.

    Returns
    -------
    str
        The access token.

    Raises
    ------
    RuntimeError
        If authentication fails.
    """
    response = client.post(
        f"{API_V1_PREFIX}/system/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        name="/system/auth/login",
    )

    if response.status_code != 200:
        log_error(response, context="Login")
        raise RuntimeError(f"Login failed with status {response.status_code}")

    data = response.json()
    return data["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    """Return authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {token}"}


def log_error(response, context: str = "") -> None:
    """
    Log an error response with colored output.

    Parameters
    ----------
    response
        The HTTP response object.
    context : str
        Additional context for the error message.
    """
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", "No details available")
        except Exception:
            detail = response.text or "No details available"

        red = "\033[91m"
        yellow = "\033[93m"
        reset = "\033[0m"

        url_path = response.url.split("/", 3)[-1] if "/" in response.url else response.url

        prefix = f"[{context}] " if context else ""
        message = (
            f"{red}{prefix}Error{reset} | "
            f"{yellow}URL:{reset} /{url_path} | "
            f"{yellow}Status:{reset} {response.status_code} | "
            f"{yellow}Detail:{reset} {detail}"
        )
        print(message)
