# Built-in Dependencies
import uuid

# Third-Party Dependencies
from locust import TaskSet, task

# Local Dependencies
from helpers import login, auth_headers, log_error
from config import API_V1_PREFIX


class PostsTasks(TaskSet):
    """Load test tasks for blog posts endpoints."""

    access_token: str = ""
    user_id: str = ""
    post_id: str = ""

    def on_start(self) -> None:
        """Authenticate and fetch current user ID."""
        self.access_token = login(self.client)
        self._get_current_user()

    def _get_current_user(self) -> None:
        """Fetch current user to get user_id for post operations."""
        response = self.client.get(
            f"{API_V1_PREFIX}/system/users/me/",
            headers=auth_headers(self.access_token),
            name="/system/users/me [posts setup]",
        )
        if response.status_code >= 400:
            log_error(response, context="Posts Setup - Get Me")
            self.interrupt()
            return

        data = response.json()
        self.user_id = data["id"]

    @task(2)
    def create_post(self) -> None:
        """POST create a new blog post."""
        if not self.user_id:
            return

        payload = {
            "title": f"Load Test Post {uuid.uuid4().hex[:8]}",
            "text": "This is a post created during load testing. It can be safely deleted.",
        }

        response = self.client.post(
            f"{API_V1_PREFIX}/blog/posts/user/{self.user_id}",
            json=payload,
            headers=auth_headers(self.access_token),
            name="/blog/posts/user/{user_id} [create]",
        )
        if response.status_code >= 400:
            log_error(response, context="Posts Create")
            return

        data = response.json()
        self.post_id = data.get("id", self.post_id)

    @task(4)
    def list_posts(self) -> None:
        """GET paginated list of posts for current user."""
        if not self.user_id:
            return

        response = self.client.get(
            f"{API_V1_PREFIX}/blog/posts/user/{self.user_id}",
            headers=auth_headers(self.access_token),
            params={"page": 1, "items_per_page": 10},
            name="/blog/posts/user/{user_id} [list]",
        )
        if response.status_code >= 400:
            log_error(response, context="Posts List")
            return

        data = response.json()
        if data.get("data"):
            self.post_id = data["data"][0]["id"]

    @task(3)
    def get_post(self) -> None:
        """GET a specific post by ID."""
        if not self.user_id or not self.post_id:
            # No post available, create one first
            self.create_post()
            return

        with self.client.get(
            f"{API_V1_PREFIX}/blog/posts/{self.post_id}/user/{self.user_id}",
            headers=auth_headers(self.access_token),
            name="/blog/posts/{post_id}/user/{user_id} [get]",
            catch_response=True,
        ) as response:
            if response.status_code == 404:
                response.success()  # Expected: post was deleted during test
                self.post_id = ""
            elif response.status_code >= 400:
                response.failure(f"{response.status_code}: {response.text}")

    @task(1)
    def update_post(self) -> None:
        """PATCH update an existing post."""
        if not self.user_id or not self.post_id:
            return

        payload = {"title": f"Updated Load Test Post {uuid.uuid4().hex[:8]}"}

        with self.client.patch(
            f"{API_V1_PREFIX}/blog/posts/{self.post_id}/user/{self.user_id}",
            json=payload,
            headers=auth_headers(self.access_token),
            name="/blog/posts/{post_id}/user/{user_id} [update]",
            catch_response=True,
        ) as response:
            if response.status_code == 404:
                response.success()  # Expected: post was deleted during test
                self.post_id = ""
            elif response.status_code >= 400:
                response.failure(f"{response.status_code}: {response.text}")

    @task(1)
    def delete_post(self) -> None:
        """DELETE soft-delete a post."""
        if not self.user_id or not self.post_id:
            return

        # Save and clear post_id before request to avoid race conditions
        post_to_delete = self.post_id
        self.post_id = ""

        with self.client.delete(
            f"{API_V1_PREFIX}/blog/posts/{post_to_delete}/user/{self.user_id}",
            headers=auth_headers(self.access_token),
            name="/blog/posts/{post_id}/user/{user_id} [delete]",
            catch_response=True,
        ) as response:
            if response.status_code == 404:
                response.success()  # Expected: already deleted
            elif response.status_code >= 400:
                response.failure(f"{response.status_code}: {response.text}")
