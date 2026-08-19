# Built-in Dependencies
import uuid

# Third-Party Dependencies
from locust import TaskSet, task

# Local Dependencies
from helpers import login, auth_headers, log_error
from config import API_V1_PREFIX


class ItemsTasks(TaskSet):
    """Template TaskSet for a resource CRUD. Copy to locust/tasks/<resource>.py and rename."""

    access_token: str = ""
    item_id: str = ""

    def on_start(self) -> None:
        self.access_token = login(self.client)

    @task(2)
    def create_item(self) -> None:
        payload = {
            "title": f"Load Test Item {uuid.uuid4().hex[:8]}",
            "text": "This is an item created during load testing. It can be safely deleted.",
        }

        response = self.client.post(
            f"{API_V1_PREFIX}/example/items",
            json=payload,
            headers=auth_headers(self.access_token),
            name="/example/items [create]",
        )
        if response.status_code >= 400:
            log_error(response, context="Items Create")
            return

        data = response.json()
        self.item_id = data.get("id", self.item_id)

    @task(4)
    def list_items(self) -> None:
        response = self.client.get(
            f"{API_V1_PREFIX}/example/items",
            headers=auth_headers(self.access_token),
            params={"page": 1, "items_per_page": 10},
            name="/example/items [list]",
        )
        if response.status_code >= 400:
            log_error(response, context="Items List")
            return

        data = response.json()
        if data.get("data"):
            self.item_id = data["data"][0]["id"]

    @task(3)
    def get_item(self) -> None:
        if not self.item_id:
            self.create_item()
            return

        with self.client.get(
            f"{API_V1_PREFIX}/example/items/{self.item_id}",
            headers=auth_headers(self.access_token),
            name="/example/items/{item_id} [get]",
            catch_response=True,
        ) as response:
            if response.status_code == 404:
                response.success()
                self.item_id = ""
            elif response.status_code >= 400:
                response.failure(f"{response.status_code}: {response.text}")

    @task(1)
    def update_item(self) -> None:
        if not self.item_id:
            return

        payload = {"title": f"Updated Load Test Item {uuid.uuid4().hex[:8]}"}

        with self.client.patch(
            f"{API_V1_PREFIX}/example/items/{self.item_id}",
            json=payload,
            headers=auth_headers(self.access_token),
            name="/example/items/{item_id} [update]",
            catch_response=True,
        ) as response:
            if response.status_code == 404:
                response.success()
                self.item_id = ""
            elif response.status_code >= 400:
                response.failure(f"{response.status_code}: {response.text}")

    @task(1)
    def delete_item(self) -> None:
        if not self.item_id:
            return

        item_to_delete = self.item_id
        self.item_id = ""

        with self.client.delete(
            f"{API_V1_PREFIX}/example/items/{item_to_delete}",
            headers=auth_headers(self.access_token),
            name="/example/items/{item_id} [delete]",
            catch_response=True,
        ) as response:
            if response.status_code == 404:
                response.success()
            elif response.status_code >= 400:
                response.failure(f"{response.status_code}: {response.text}")
