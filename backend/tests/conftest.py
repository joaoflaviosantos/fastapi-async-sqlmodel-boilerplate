# Third-Party Dependencies
import pytest
from fastapi.testclient import TestClient
import subprocess
import os

# Local Dependencies
from src.main import app
from src.core.config import settings


def _hard_delete_test_user_from_db() -> None:
    """
    Hard delete the test user from the database using psql.
    This ensures we start with a clean slate for tests.
    """
    try:
        # Build the connection string
        user = settings.POSTGRES_USER
        password = settings.POSTGRES_PASSWORD
        host = settings.POSTGRES_SERVER
        port = settings.POSTGRES_PORT
        db = settings.POSTGRES_DB

        # Build the DELETE query
        query = f"DELETE FROM sys_user WHERE email = '{settings.TEST_EMAIL}';"

        # Execute the query using psql
        env = os.environ.copy()
        env["PGPASSWORD"] = password

        subprocess.run(
            ["psql", "-h", host, "-p", str(port), "-U", user, "-d", db, "-c", query],
            env=env,
            capture_output=True,
            timeout=5,
        )
    except Exception:
        # Silently fail if we can't delete from DB
        pass


@pytest.fixture(scope="session", autouse=True)
def setup_clean_db():
    """
    Clean up test user from database before running tests.
    """
    _hard_delete_test_user_from_db()
    yield
    # Optionally clean up after tests too
    # _hard_delete_test_user_from_db()


@pytest.fixture(scope="session")
def client():
    """
    Pytest fixture to provide a FastAPI TestClient instance for testing.

    This fixture sets up a TestClient instance using the main FastAPI app, and the scope is set to session,
    meaning it will be shared among all test functions in a session.

    Returns
    ----------
    TestClient
        The FastAPI TestClient instance.

    Example
    ----------
    Using the `client` fixture in a test function:
    ```python
    def test_example(client):
        response = client.get("/example")
        assert response.status_code == 200
        assert response.json() == {"message": "Example response"}
    ```
    """
    with TestClient(app) as _client:
        yield _client
