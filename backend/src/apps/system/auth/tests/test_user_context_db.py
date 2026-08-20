# Built-in Dependencies
from types import SimpleNamespace

# Third-Party Dependencies
import pytest

# Local Dependencies
from src.apps.system.auth.deps import async_get_user_context_db

pytestmark = pytest.mark.unit


async def test_async_get_user_context_db_attaches_current_user() -> None:
    db = SimpleNamespace()
    current_user = {"id": "user-1", "username": "admin"}

    result = await async_get_user_context_db(db=db, current_user=current_user)

    assert result is db
    assert getattr(db, "current_user") is current_user
