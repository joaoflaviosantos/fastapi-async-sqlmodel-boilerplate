# Third-Party Dependencies
from fastapi.testclient import TestClient

# Local Dependencies
from src.core.config import settings
from tests.helper import _get_token

# Test data: admin/superuser 'test' credentials
ADMIN_USERNAME = settings.ADMIN_USERNAME
ADMIN_PASSWORD = settings.ADMIN_PASSWORD

# Test global variables
test_task_id = None
test_task_message = "Test Message"


def test_create_task(client: TestClient) -> None:
    global test_task_id
    assert test_task_id is None

    token = _get_token(username=ADMIN_USERNAME, password=ADMIN_PASSWORD, client=client)

    response = client.post(
        f"/api/v1/system/tasks?message={test_task_message}",
        headers={"Authorization": f'Bearer {token.json()["access_token"]}'},
    )

    test_task_id = response.json()["id"]

    assert test_task_id is not None
    assert response.status_code == 201


def test_get_task(client: TestClient) -> None:
    global test_task_id
    assert test_task_id is not None

    response = client.get(f"/api/v1/system/tasks/{test_task_id}")

    assert response.status_code == 200
    assert response.json()["args"][0] == test_task_message


def test_read_processed_tasks(client: TestClient) -> None:
    response = client.get("/api/v1/system/tasks/processed")

    assert response.status_code == 200


def test_read_pending_tasks(client: TestClient) -> None:
    response = client.get("/api/v1/system/tasks/pending")

    assert response.status_code == 200
