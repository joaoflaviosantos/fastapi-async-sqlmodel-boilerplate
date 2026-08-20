# Built-in Dependencies
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

# Third-Party Dependencies
import pytest
from sqlalchemy.exc import IntegrityError

# Local Dependencies
from src.apps.system.users.schemas import UserCreate, UserTierUpdate, UserUpdate
from src.apps.system.users.services import UserService
from src.core.exceptions.http_exceptions import (
    BadRequestException,
    DuplicateValueException,
    ForbiddenException,
    InternalErrorException,
    NotFoundException,
)

pytestmark = pytest.mark.unit


def _user_create() -> UserCreate:
    return UserCreate(
        name="User Userson",
        username="userson",
        email="user@tester.com",
        password="Str1ngst!",
    )


def _integrity_error() -> IntegrityError:
    return IntegrityError("INSERT", {}, Exception("orig"))


def _service(
    user_repo: AsyncMock | None = None,
    tier_repo: AsyncMock | None = None,
    rate_limit_repo: AsyncMock | None = None,
) -> tuple[UserService, AsyncMock, AsyncMock, AsyncMock]:
    user_repo = user_repo or AsyncMock()
    tier_repo = tier_repo or AsyncMock()
    rate_limit_repo = rate_limit_repo or AsyncMock()
    return UserService(user_repo, tier_repo, rate_limit_repo), user_repo, tier_repo, rate_limit_repo


async def test_create_user_rejects_duplicate_email() -> None:
    service, user_repo, _, _ = _service()
    user_repo.exists.return_value = True

    with pytest.raises(DuplicateValueException):
        await service.create_user(db=object(), user=_user_create())

    user_repo.create.assert_not_awaited()


async def test_create_user_rejects_duplicate_username() -> None:
    service, user_repo, _, _ = _service()
    user_repo.exists.side_effect = [False, True]

    with pytest.raises(DuplicateValueException):
        await service.create_user(db=object(), user=_user_create())

    user_repo.create.assert_not_awaited()


async def test_create_user_raises_when_default_tier_missing() -> None:
    service, user_repo, tier_repo, _ = _service()
    user_repo.exists.return_value = False
    tier_repo.get.return_value = None

    with patch("src.apps.system.users.services.get_password_hash", return_value="hashed"):
        with pytest.raises(BadRequestException):
            await service.create_user(db=object(), user=_user_create())

    user_repo.create.assert_not_awaited()


async def test_create_user_hashes_password_and_queues_welcome_email() -> None:
    service, user_repo, tier_repo, _ = _service()
    user_repo.exists.return_value = False
    tier_repo.get.return_value = {"id": uuid4()}
    created = SimpleNamespace(email="user@tester.com", username="userson")
    user_repo.create.return_value = created

    with patch(
        "src.apps.system.users.services.get_password_hash", return_value="hashed"
    ) as hash_fn:
        with patch("src.apps.system.users.services.send_welcome_email") as welcome:
            result = await service.create_user(db=object(), user=_user_create())

    assert result is created
    hash_fn.assert_called_once_with(password="Str1ngst!")
    user_repo.create.assert_awaited_once()
    welcome.delay.assert_called_once_with(email="user@tester.com", username="userson")


async def test_get_users_returns_paginated_dict() -> None:
    service, user_repo, _, _ = _service()
    user_repo.get_multi.return_value = {"data": [{"username": "userson"}], "total_count": 1}

    result = await service.get_users(db=object(), page=1, items_per_page=10)

    assert result["data"] == [{"username": "userson"}]
    assert result["total_count"] == 1
    user_repo.get_multi.assert_awaited_once()


async def test_get_user_raises_when_missing() -> None:
    service, user_repo, _, _ = _service()
    user_repo.get.return_value = None

    with pytest.raises(NotFoundException):
        await service.get_user(db=object(), user_id=uuid4())


async def test_get_user_returns_row() -> None:
    user_id = uuid4()
    service, user_repo, _, _ = _service()
    user_repo.get.return_value = {"id": user_id, "username": "userson"}

    result = await service.get_user(db=object(), user_id=user_id)

    assert result["id"] == user_id
    user_repo.get.assert_awaited_once()


async def test_update_user_raises_when_missing() -> None:
    service, user_repo, _, _ = _service()
    user_repo.get.return_value = None

    with pytest.raises(NotFoundException):
        await service.update_user(
            db=object(),
            user_id=uuid4(),
            values=UserUpdate(name="New Name"),
            current_user={"id": uuid4(), "is_superuser": True},
        )

    user_repo.update.assert_not_awaited()


async def test_update_user_forbidden_for_other_regular_user() -> None:
    user_id = uuid4()
    service, user_repo, _, _ = _service()
    user_repo.get.return_value = {"id": user_id, "username": "userson", "email": "user@tester.com"}

    with pytest.raises(ForbiddenException):
        await service.update_user(
            db=object(),
            user_id=user_id,
            values=UserUpdate(name="New Name"),
            current_user={"id": uuid4(), "is_superuser": False},
        )

    user_repo.update.assert_not_awaited()


async def test_update_user_rejects_duplicate_username() -> None:
    user_id = uuid4()
    service, user_repo, _, _ = _service()
    user_repo.get.return_value = {"id": user_id, "username": "userson", "email": "user@tester.com"}
    user_repo.exists.return_value = True

    with pytest.raises(DuplicateValueException):
        await service.update_user(
            db=object(),
            user_id=user_id,
            values=UserUpdate(username="taken"),
            current_user={"id": user_id, "is_superuser": False},
        )

    user_repo.update.assert_not_awaited()


async def test_update_user_rejects_duplicate_email() -> None:
    user_id = uuid4()
    service, user_repo, _, _ = _service()
    user_repo.get.return_value = {"id": user_id, "username": "userson", "email": "user@tester.com"}
    user_repo.exists.return_value = True

    with pytest.raises(DuplicateValueException):
        await service.update_user(
            db=object(),
            user_id=user_id,
            values=UserUpdate(email="taken@tester.com"),
            current_user={"id": user_id, "is_superuser": False},
        )

    user_repo.update.assert_not_awaited()


async def test_update_user_writes_values() -> None:
    user_id = uuid4()
    service, user_repo, _, _ = _service()
    user_repo.get.return_value = {"id": user_id, "username": "userson", "email": "user@tester.com"}
    user_repo.exists.return_value = False
    values = UserUpdate(name="New Name")

    result = await service.update_user(
        db=object(),
        user_id=user_id,
        values=values,
        current_user={"id": user_id, "is_superuser": False},
    )

    assert result == {"message": "User updated"}
    user_repo.update.assert_awaited_once()


async def test_delete_user_raises_when_missing() -> None:
    service, user_repo, _, _ = _service()
    user_repo.get.return_value = None

    with pytest.raises(NotFoundException):
        await service.delete_user(
            db=object(),
            user_id=uuid4(),
            current_user={"id": uuid4(), "is_superuser": True},
        )

    user_repo.delete.assert_not_awaited()


async def test_delete_user_already_deleted_for_superuser() -> None:
    service, user_repo, _, _ = _service()
    user_repo.get.return_value = {"id": uuid4(), "is_deleted": True, "username": "userson"}

    with pytest.raises(NotFoundException, match="already deleted"):
        await service.delete_user(
            db=object(),
            user_id=uuid4(),
            current_user={"id": uuid4(), "is_superuser": True},
        )

    user_repo.delete.assert_not_awaited()


async def test_delete_user_already_deleted_for_regular_user() -> None:
    service, user_repo, _, _ = _service()
    user_repo.get.return_value = {"id": uuid4(), "is_deleted": True, "username": "userson"}

    with pytest.raises(NotFoundException, match="User not found"):
        await service.delete_user(
            db=object(),
            user_id=uuid4(),
            current_user={"id": uuid4(), "is_superuser": False},
        )

    user_repo.delete.assert_not_awaited()


async def test_delete_user_forbidden_for_other_regular_user() -> None:
    user_id = uuid4()
    service, user_repo, _, _ = _service()
    user_repo.get.return_value = {"id": user_id, "is_deleted": False, "username": "userson"}

    with pytest.raises(ForbiddenException):
        await service.delete_user(
            db=object(),
            user_id=user_id,
            current_user={"id": uuid4(), "is_superuser": False},
        )

    user_repo.delete.assert_not_awaited()


async def test_delete_user_soft_deletes() -> None:
    user_id = uuid4()
    db_user = {"id": user_id, "is_deleted": False, "username": "userson"}
    service, user_repo, _, _ = _service()
    user_repo.get.return_value = db_user

    with patch("src.apps.system.users.services.cache") as cache_mod:
        cache_mod.client = None
        result = await service.delete_user(
            db=object(),
            user_id=user_id,
            current_user={"id": user_id, "is_superuser": False},
        )

    assert result == {"message": "User deleted"}
    user_repo.delete.assert_awaited_once()


async def test_delete_user_removes_username_from_cache() -> None:
    user_id = uuid4()
    db_user = {"id": user_id, "is_deleted": False, "username": "userson"}
    service, user_repo, _, _ = _service()
    user_repo.get.return_value = db_user
    cache_client = AsyncMock()

    with patch("src.apps.system.users.services.cache") as cache_mod:
        cache_mod.client = cache_client
        await service.delete_user(
            db=object(),
            user_id=user_id,
            current_user={"id": user_id, "is_superuser": False},
        )

    cache_client.hdel.assert_awaited_once()


async def test_db_delete_user_raises_when_missing() -> None:
    service, user_repo, _, _ = _service()
    user_repo.get.return_value = None

    with pytest.raises(NotFoundException):
        await service.db_delete_user(db=object(), user_id=uuid4())

    user_repo.db_delete.assert_not_awaited()


async def test_db_delete_user_integrity_error_is_forbidden() -> None:
    service, user_repo, _, _ = _service()
    user_repo.get.return_value = {"id": uuid4(), "username": "userson"}
    user_repo.db_delete.side_effect = _integrity_error()

    with pytest.raises(ForbiddenException):
        await service.db_delete_user(db=object(), user_id=uuid4())


async def test_db_delete_user_unexpected_error_is_internal() -> None:
    service, user_repo, _, _ = _service()
    user_repo.get.return_value = {"id": uuid4(), "username": "userson"}
    user_repo.db_delete.side_effect = RuntimeError("boom")

    with pytest.raises(InternalErrorException):
        await service.db_delete_user(db=object(), user_id=uuid4())


async def test_db_delete_user_hard_deletes() -> None:
    service, user_repo, _, _ = _service()
    user_repo.get.return_value = {"id": uuid4(), "username": "userson"}

    with patch("src.apps.system.users.services.cache") as cache_mod:
        cache_mod.client = None
        result = await service.db_delete_user(db=object(), user_id=uuid4())

    assert result == {"message": "User deleted from the database"}
    user_repo.db_delete.assert_awaited_once()


async def test_db_delete_user_removes_username_from_cache() -> None:
    service, user_repo, _, _ = _service()
    user_repo.get.return_value = {"id": uuid4(), "username": "userson"}
    cache_client = AsyncMock()

    with patch("src.apps.system.users.services.cache") as cache_mod:
        cache_mod.client = cache_client
        await service.db_delete_user(db=object(), user_id=uuid4())

    cache_client.hdel.assert_awaited_once()


async def test_get_user_rate_limits_raises_when_user_missing() -> None:
    service, user_repo, _, _ = _service()
    user_repo.get.return_value = None

    with pytest.raises(NotFoundException):
        await service.get_user_rate_limits(db=object(), user_id=uuid4())


async def test_get_user_rate_limits_empty_when_user_has_no_tier() -> None:
    service, user_repo, _, _ = _service()
    db_user = {"id": uuid4(), "tier_id": None}
    user_repo.get.return_value = db_user

    result = await service.get_user_rate_limits(db=object(), user_id=uuid4())

    assert result["tier_rate_limits"] == []


async def test_get_user_rate_limits_raises_when_tier_missing() -> None:
    service, user_repo, tier_repo, _ = _service()
    user_repo.get.return_value = {"id": uuid4(), "tier_id": uuid4()}
    tier_repo.get.return_value = None

    with pytest.raises(NotFoundException):
        await service.get_user_rate_limits(db=object(), user_id=uuid4())


async def test_get_user_rate_limits_attaches_tier_limits() -> None:
    tier_id = uuid4()
    service, user_repo, tier_repo, rate_limit_repo = _service()
    db_user = {"id": uuid4(), "tier_id": tier_id}
    user_repo.get.return_value = db_user
    tier_repo.get.return_value = {"id": tier_id}
    rate_limit_repo.get_multi.return_value = {"data": [{"name": "users:5:60"}]}

    result = await service.get_user_rate_limits(db=object(), user_id=uuid4())

    assert result["tier_rate_limits"] == [{"name": "users:5:60"}]


async def test_get_user_tier_raises_when_user_missing() -> None:
    service, user_repo, _, _ = _service()
    user_repo.get.return_value = None

    with pytest.raises(NotFoundException):
        await service.get_user_tier(db=object(), user_id=uuid4())


async def test_get_user_tier_raises_when_tier_missing() -> None:
    service, user_repo, tier_repo, _ = _service()
    user_repo.get.return_value = {"id": uuid4(), "tier_id": uuid4(), "username": "userson"}
    tier_repo.exists.return_value = False

    with pytest.raises(NotFoundException):
        await service.get_user_tier(db=object(), user_id=uuid4())


async def test_get_user_tier_returns_joined_row() -> None:
    service, user_repo, tier_repo, _ = _service()
    user_repo.get.return_value = {"id": uuid4(), "tier_id": uuid4(), "username": "userson"}
    tier_repo.exists.return_value = True
    joined = {"username": "userson", "tier_name": "free"}
    user_repo.get_joined.return_value = joined

    result = await service.get_user_tier(db=object(), user_id=uuid4())

    assert result == joined
    user_repo.get_joined.assert_awaited_once()


async def test_update_user_tier_raises_when_user_missing() -> None:
    service, user_repo, _, _ = _service()
    user_repo.get.return_value = None

    with pytest.raises(NotFoundException):
        await service.update_user_tier(
            db=object(),
            user_id=uuid4(),
            values=UserTierUpdate(tier_id=uuid4()),
        )

    user_repo.update.assert_not_awaited()


async def test_update_user_tier_raises_when_tier_missing() -> None:
    service, user_repo, tier_repo, _ = _service()
    user_repo.get.return_value = {"id": uuid4(), "username": "userson"}
    tier_repo.get.return_value = None

    with pytest.raises(NotFoundException):
        await service.update_user_tier(
            db=object(),
            user_id=uuid4(),
            values=UserTierUpdate(tier_id=uuid4()),
        )

    user_repo.update.assert_not_awaited()


async def test_update_user_tier_assigns_tier() -> None:
    user_id = uuid4()
    tier_id = uuid4()
    service, user_repo, tier_repo, _ = _service()
    user_repo.get.return_value = {"id": user_id, "username": "userson"}
    tier_repo.get.return_value = {"id": tier_id, "name": "premium"}
    values = UserTierUpdate(tier_id=tier_id)

    result = await service.update_user_tier(db=object(), user_id=user_id, values=values)

    assert "premium" in result["message"]
    user_repo.update.assert_awaited_once()
