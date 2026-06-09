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
        """Test token refresh endpoint."""
        response = self.client.post(
            f"{API_V1_PREFIX}/system/auth/refresh",
            name="/system/auth/refresh",
        )
        # refresh may fail if no refresh_token cookie is set (expected in load test)
        if response.status_code >= 400:
            log_error(response, context="Auth Refresh")
