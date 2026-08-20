# Built-in Dependencies
import uuid

# Third-Party Dependencies
from locust import TaskSet, task

# Local Dependencies
from helpers import login, auth_headers, log_error
from config import API_V1_PREFIX


class TagsTasks(TaskSet):
    """Load test tasks for blog tags endpoints."""

    access_token: str = ""
    tag_id: str = ""

    def on_start(self) -> None:
        self.access_token = login(self.client)

    @task(2)
    def create_tag(self) -> None:
        payload = {"name": f"lt-{uuid.uuid4().hex[:8]}"}

        with self.client.post(
            f"{API_V1_PREFIX}/blog/tags",
            json=payload,
            headers=auth_headers(self.access_token),
            name="/blog/tags [create]",
            catch_response=True,
        ) as response:
            if response.status_code == 429:
                response.success()
                return
            if response.status_code >= 400:
                response.failure(f"{response.status_code}: {response.text}")
                return
            self.tag_id = response.json().get("id", self.tag_id)

    @task(4)
    def list_tags(self) -> None:
        with self.client.get(
            f"{API_V1_PREFIX}/blog/tags",
            headers=auth_headers(self.access_token),
            params={"page": 1, "items_per_page": 10},
            name="/blog/tags [list]",
            catch_response=True,
        ) as response:
            if response.status_code == 429:
                response.success()
                return
            if response.status_code >= 400:
                response.failure(f"{response.status_code}: {response.text}")
                return
            data = response.json()
            if data.get("data"):
                self.tag_id = data["data"][0]["id"]

    @task(3)
    def get_tag(self) -> None:
        if not self.tag_id:
            self.create_tag()
            return

        with self.client.get(
            f"{API_V1_PREFIX}/blog/tags/{self.tag_id}",
            headers=auth_headers(self.access_token),
            name="/blog/tags/{tag_id} [get]",
            catch_response=True,
        ) as response:
            if response.status_code in (404, 429):
                response.success()
                if response.status_code == 404:
                    self.tag_id = ""
            elif response.status_code >= 400:
                response.failure(f"{response.status_code}: {response.text}")

    @task(1)
    def update_tag(self) -> None:
        if not self.tag_id:
            return

        payload = {"name": f"lt-{uuid.uuid4().hex[:8]}"}

        with self.client.patch(
            f"{API_V1_PREFIX}/blog/tags/{self.tag_id}",
            json=payload,
            headers=auth_headers(self.access_token),
            name="/blog/tags/{tag_id} [update]",
            catch_response=True,
        ) as response:
            if response.status_code in (404, 429):
                response.success()
                if response.status_code == 404:
                    self.tag_id = ""
            elif response.status_code >= 400:
                response.failure(f"{response.status_code}: {response.text}")

    @task(1)
    def delete_tag(self) -> None:
        if not self.tag_id:
            return

        tag_to_delete = self.tag_id
        self.tag_id = ""

        with self.client.delete(
            f"{API_V1_PREFIX}/blog/tags/{tag_to_delete}",
            headers=auth_headers(self.access_token),
            name="/blog/tags/{tag_id} [delete]",
            catch_response=True,
        ) as response:
            if response.status_code in (403, 404, 429):
                response.success()
            elif response.status_code >= 400:
                response.failure(f"{response.status_code}: {response.text}")
