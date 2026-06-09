# Third-Party Dependencies
from locust import TaskSet, task

# Local Dependencies
from helpers import login, auth_headers, log_error
from config import API_V1_PREFIX


class TiersTasks(TaskSet):
    """Load test tasks for system tiers endpoints."""

    access_token: str = ""
    tier_id: str = ""

    def on_start(self) -> None:
        """Authenticate and fetch initial tier data."""
        self.access_token = login(self.client)
        self._fetch_tiers()

    def _fetch_tiers(self) -> None:
        """Fetch paginated tiers and store the first tier ID."""
        response = self.client.get(
            f"{API_V1_PREFIX}/system/tiers",
            headers=auth_headers(self.access_token),
            params={"page": 1, "items_per_page": 10},
            name="/system/tiers [list]",
        )
        if response.status_code >= 400:
            log_error(response, context="Tiers List")
            self.interrupt()
            return

        data = response.json()
        if data.get("data"):
            self.tier_id = data["data"][0]["id"]

    @task(3)
    def list_tiers(self) -> None:
        """GET paginated list of tiers."""
        response = self.client.get(
            f"{API_V1_PREFIX}/system/tiers",
            headers=auth_headers(self.access_token),
            params={"page": 1, "items_per_page": 10},
            name="/system/tiers [list]",
        )
        if response.status_code >= 400:
            log_error(response, context="Tiers List")

    @task(2)
    def get_tier_by_id(self) -> None:
        """GET a specific tier by ID."""
        if not self.tier_id:
            return

        response = self.client.get(
            f"{API_V1_PREFIX}/system/tiers/{self.tier_id}",
            headers=auth_headers(self.access_token),
            name="/system/tiers/{tier_id}",
        )
        if response.status_code >= 400:
            log_error(response, context="Tiers Get")
