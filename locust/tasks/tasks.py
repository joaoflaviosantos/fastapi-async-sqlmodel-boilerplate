# Third-Party Dependencies
from locust import TaskSet, task

# Local Dependencies
from helpers import login, auth_headers, log_error
from config import API_V1_PREFIX


class BackgroundTasksTasks(TaskSet):
    """Load test tasks for system background tasks endpoints."""

    access_token: str = ""
    task_id: str = ""

    def on_start(self) -> None:
        """Authenticate on task start."""
        self.access_token = login(self.client)

    @task(2)
    def create_sample_task(self) -> None:
        """POST create a sample background task."""
        response = self.client.post(
            f"{API_V1_PREFIX}/system/tasks/sample",
            headers=auth_headers(self.access_token),
            params={"message": "locust load test"},
            name="/system/tasks/sample [create]",
        )
        if response.status_code >= 400:
            log_error(response, context="Tasks Create")
            return

        data = response.json()
        self.task_id = data.get("id", self.task_id)

    @task(3)
    def get_processed_tasks(self) -> None:
        """GET all processed (non-pending) tasks."""
        response = self.client.get(
            f"{API_V1_PREFIX}/system/tasks/processed",
            headers=auth_headers(self.access_token),
            name="/system/tasks/processed",
        )
        if response.status_code >= 400:
            log_error(response, context="Tasks Processed")

    @task(3)
    def get_pending_tasks(self) -> None:
        """GET all pending tasks."""
        response = self.client.get(
            f"{API_V1_PREFIX}/system/tasks/pending",
            headers=auth_headers(self.access_token),
            name="/system/tasks/pending",
        )
        if response.status_code >= 400:
            log_error(response, context="Tasks Pending")

    @task(2)
    def get_task_by_id(self) -> None:
        """GET a specific task by ID."""
        if not self.task_id:
            return

        response = self.client.get(
            f"{API_V1_PREFIX}/system/tasks/{self.task_id}",
            headers=auth_headers(self.access_token),
            name="/system/tasks/{task_id}",
        )
        if response.status_code >= 400:
            log_error(response, context="Tasks Get")
