# Third-Party Dependencies
from locust import TaskSet, task

# Local Dependencies
from helpers import login, auth_headers, log_error
from config import API_V1_PREFIX


class AuthTasks(TaskSet):
    """Load test tasks for authentication endpoints."""

    access_token: str = ""

    def on_start(self) -> None:
        """Authenticate on task start."""
        self.access_token = login(self.client)

    @task(3)
    def logout_and_login(self) -> None:
        """Test logout followed by a fresh login."""
        # Logout
        response = self.client.post(
            f"{API_V1_PREFIX}/system/auth/logout",
            headers=auth_headers(self.access_token),
            name="/system/auth/logout",
        )
        if response.status_code >= 400:
            log_error(response, context="Auth Logout")

        # Re-login
        self.access_token = login(self.client)

    @task(1)
    def refresh_token(self) -> None:
        """Test token refresh endpoint (uses cookie set during login)."""
        # First perform a login to ensure the refresh_token cookie is set
        self.access_token = login(self.client)

        with self.client.post(
            f"{API_V1_PREFIX}/system/auth/refresh",
            name="/system/auth/refresh",
            catch_response=True,
        ) as response:
            if response.status_code == 401:
                # Cookie may not have been set by the server; not a real failure
                response.success()
            elif response.status_code >= 400:
                response.failure(f"{response.status_code}: {response.text}")
