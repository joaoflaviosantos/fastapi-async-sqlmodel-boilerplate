# Third-Party Dependencies
from locust import TaskSet, task

# Local Dependencies
from helpers import login, auth_headers, log_error
from config import API_V1_PREFIX


class UsersTasks(TaskSet):
    """Load test tasks for system users endpoints."""

    access_token: str = ""
    user_id: str = ""

    def on_start(self) -> None:
        """Authenticate and fetch initial user data."""
        self.access_token = login(self.client)
        self._fetch_users()

    def _fetch_users(self) -> None:
        """Fetch paginated users and store the first user ID."""
        response = self.client.get(
            f"{API_V1_PREFIX}/system/users",
            headers=auth_headers(self.access_token),
            params={"page": 1, "items_per_page": 10},
            name="/system/users [list]",
        )
        if response.status_code >= 400:
            log_error(response, context="Users List")
            self.interrupt()
            return

        data = response.json()
        if data.get("data"):
            self.user_id = data["data"][0]["id"]

    @task(4)
    def list_users(self) -> None:
        """GET paginated list of users."""
        response = self.client.get(
            f"{API_V1_PREFIX}/system/users",
            headers=auth_headers(self.access_token),
            params={"page": 1, "items_per_page": 10},
            name="/system/users [list]",
        )
        if response.status_code >= 400:
            log_error(response, context="Users List")

    @task(3)
    def get_current_user(self) -> None:
        """GET current authenticated user (me)."""
        response = self.client.get(
            f"{API_V1_PREFIX}/system/users/me/",
            headers=auth_headers(self.access_token),
            name="/system/users/me",
        )
        if response.status_code >= 400:
            log_error(response, context="Users Me")

    @task(2)
    def get_user_by_id(self) -> None:
        """GET a specific user by ID."""
        if not self.user_id:
            return

        response = self.client.get(
            f"{API_V1_PREFIX}/system/users/{self.user_id}",
            headers=auth_headers(self.access_token),
            name="/system/users/{user_id}",
        )
        if response.status_code >= 400:
            log_error(response, context="Users Get")
