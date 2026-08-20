# Third-Party Dependencies
from locust import HttpUser, between

# Local Dependencies
from config import HOST
from tasks import (
    AuthTasks,
    UsersTasks,
    TiersTasks,
    PostsTasks,
    TagsTasks,
    BackgroundTasksTasks,
)


class APIUser(HttpUser):
    """
    Simulates a user interacting with the FastAPI application.

    Task weights:
    - Posts (4): Blog CRUD is the heaviest read/write workload
    - Users (3): User listing and profile access
    - Tasks (2): Background task creation and status checks
    - Tags (1): Tag catalog CRUD
    - Tiers (1): Tier listing (low frequency)
    - Auth (1): Login/logout cycles
    """

    host = HOST
    tasks = {
        PostsTasks: 4,
        UsersTasks: 3,
        BackgroundTasksTasks: 2,
        TagsTasks: 1,
        TiersTasks: 1,
        AuthTasks: 1,
    }
    wait_time = between(1, 3)
