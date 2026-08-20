# Built-in Dependencies
from unittest.mock import AsyncMock, patch
from uuid import uuid4

# Third-Party Dependencies
import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

# Local Dependencies
from src.apps.system.rate_limits.schemas import RateLimitCreate, RateLimitUpdate
from src.apps.system.rate_limits.services import RateLimitService
from src.core.exceptions.http_exceptions import (
    DuplicateValueException,
    ForbiddenException,
    InternalErrorException,
    NotFoundException,
    UnprocessableEntityException,
)

pytestmark = pytest.mark.unit


def _rate_limit_create() -> RateLimitCreate:
    return RateLimitCreate(name="users:5:60", path="users", limit=5, period=60)


def test_rate_limit_create_rejects_period_zero() -> None:
    with pytest.raises(ValidationError):
        RateLimitCreate(name="users:5:0", path="users", limit=5, period=0)


def test_rate_limit_create_allows_zero_limit() -> None:
    created = RateLimitCreate(name="users:0:60", path="users", limit=0, period=60)
    assert created.limit == 0
    assert created.period == 60


def _integrity_error() -> IntegrityError:
    return IntegrityError("INSERT", {}, Exception("orig"))


def _service(
    rate_limit_repo: AsyncMock | None = None,
    tier_repo: AsyncMock | None = None,
) -> tuple[RateLimitService, AsyncMock, AsyncMock]:
    rate_limit_repo = rate_limit_repo or AsyncMock()
    tier_repo = tier_repo or AsyncMock()
    return (
        RateLimitService(rate_limit_repo=rate_limit_repo, tier_repo=tier_repo),
        rate_limit_repo,
        tier_repo,
    )


async def test_create_rate_limit_raises_when_tier_missing() -> None:
    service, rate_limit_repo, tier_repo = _service()
    tier_repo.get.return_value = None

    with pytest.raises(NotFoundException):
        await service.create_rate_limit(
            db=object(),
            tier_id=uuid4(),
            rate_limit=_rate_limit_create(),
            app=object(),
        )

    rate_limit_repo.create.assert_not_awaited()


async def test_create_rate_limit_rejects_invalid_path() -> None:
    tier_id = uuid4()
    service, rate_limit_repo, tier_repo = _service()
    tier_repo.get.return_value = {"id": tier_id}

    with patch("src.apps.system.rate_limits.services.is_valid_path", return_value=False):
        with pytest.raises(UnprocessableEntityException):
            await service.create_rate_limit(
                db=object(),
                tier_id=tier_id,
                rate_limit=_rate_limit_create(),
                app=object(),
            )

    rate_limit_repo.create.assert_not_awaited()


async def test_create_rate_limit_rejects_duplicate_path() -> None:
    tier_id = uuid4()
    service, rate_limit_repo, tier_repo = _service()
    tier_repo.get.return_value = {"id": tier_id}
    rate_limit_repo.exists.return_value = True

    with patch("src.apps.system.rate_limits.services.is_valid_path", return_value=True):
        with pytest.raises(DuplicateValueException, match="path"):
            await service.create_rate_limit(
                db=object(),
                tier_id=tier_id,
                rate_limit=_rate_limit_create(),
                app=object(),
            )

    rate_limit_repo.create.assert_not_awaited()


async def test_create_rate_limit_rejects_duplicate_name() -> None:
    tier_id = uuid4()
    service, rate_limit_repo, tier_repo = _service()
    tier_repo.get.return_value = {"id": tier_id}
    rate_limit_repo.exists.side_effect = [False, True]

    with patch("src.apps.system.rate_limits.services.is_valid_path", return_value=True):
        with pytest.raises(DuplicateValueException, match="Name"):
            await service.create_rate_limit(
                db=object(),
                tier_id=tier_id,
                rate_limit=_rate_limit_create(),
                app=object(),
            )

    rate_limit_repo.create.assert_not_awaited()


async def test_create_rate_limit_writes_row() -> None:
    tier_id = uuid4()
    created = {"id": uuid4(), "name": "users:5:60"}
    service, rate_limit_repo, tier_repo = _service()
    tier_repo.get.return_value = {"id": tier_id}
    rate_limit_repo.exists.return_value = False
    rate_limit_repo.create.return_value = created

    with patch("src.apps.system.rate_limits.services.is_valid_path", return_value=True):
        result = await service.create_rate_limit(
            db=object(),
            tier_id=tier_id,
            rate_limit=_rate_limit_create(),
            app=object(),
        )

    assert result == created
    rate_limit_repo.create.assert_awaited_once()


async def test_get_rate_limits_raises_when_tier_missing() -> None:
    service, _, tier_repo = _service()
    tier_repo.get.return_value = None

    with pytest.raises(NotFoundException):
        await service.get_rate_limits(db=object(), tier_id=uuid4())


async def test_get_rate_limits_returns_paginated_dict() -> None:
    tier_id = uuid4()
    service, rate_limit_repo, tier_repo = _service()
    tier_repo.get.return_value = {"id": tier_id}
    rate_limit_repo.get_multi.return_value = {"data": [{"name": "users:5:60"}], "total_count": 1}

    result = await service.get_rate_limits(db=object(), tier_id=tier_id)

    assert result["data"] == [{"name": "users:5:60"}]
    rate_limit_repo.get_multi.assert_awaited_once()


async def test_get_rate_limit_raises_when_tier_missing() -> None:
    service, _, tier_repo = _service()
    tier_repo.get.return_value = None

    with pytest.raises(NotFoundException):
        await service.get_rate_limit(db=object(), tier_id=uuid4(), rate_limit_id=uuid4())


async def test_get_rate_limit_raises_when_missing() -> None:
    service, rate_limit_repo, tier_repo = _service()
    tier_repo.get.return_value = {"id": uuid4()}
    rate_limit_repo.get.return_value = None

    with pytest.raises(NotFoundException):
        await service.get_rate_limit(db=object(), tier_id=uuid4(), rate_limit_id=uuid4())


async def test_get_rate_limit_returns_row() -> None:
    row = {"id": uuid4(), "name": "users:5:60"}
    service, rate_limit_repo, tier_repo = _service()
    tier_repo.get.return_value = {"id": uuid4()}
    rate_limit_repo.get.return_value = row

    result = await service.get_rate_limit(db=object(), tier_id=uuid4(), rate_limit_id=uuid4())

    assert result == row


async def test_update_rate_limit_raises_when_tier_missing() -> None:
    service, rate_limit_repo, tier_repo = _service()
    tier_repo.get.return_value = None

    with pytest.raises(NotFoundException):
        await service.update_rate_limit(
            db=object(),
            tier_id=uuid4(),
            rate_limit_id=uuid4(),
            values=RateLimitUpdate(),
            app=object(),
        )

    rate_limit_repo.update.assert_not_awaited()


async def test_update_rate_limit_raises_when_missing() -> None:
    service, rate_limit_repo, tier_repo = _service()
    tier_repo.get.return_value = {"id": uuid4()}
    rate_limit_repo.get.return_value = None

    with pytest.raises(NotFoundException):
        await service.update_rate_limit(
            db=object(),
            tier_id=uuid4(),
            rate_limit_id=uuid4(),
            values=RateLimitUpdate(),
            app=object(),
        )

    rate_limit_repo.update.assert_not_awaited()


async def test_update_rate_limit_rejects_invalid_path() -> None:
    service, rate_limit_repo, tier_repo = _service()
    tier_repo.get.return_value = {"id": uuid4()}
    rate_limit_repo.get.return_value = {"id": uuid4()}

    with patch("src.apps.system.rate_limits.services.is_valid_path", return_value=False):
        with pytest.raises(UnprocessableEntityException):
            await service.update_rate_limit(
                db=object(),
                tier_id=uuid4(),
                rate_limit_id=uuid4(),
                values=RateLimitUpdate(path="missing"),
                app=object(),
            )

    rate_limit_repo.update.assert_not_awaited()


async def test_update_rate_limit_rejects_duplicate_path() -> None:
    current_id = uuid4()
    service, rate_limit_repo, tier_repo = _service()
    tier_repo.get.return_value = {"id": uuid4()}
    rate_limit_repo.get.side_effect = [
        {"id": current_id, "path": "old_path", "name": "oldname"},
        {"id": uuid4(), "path": "users"},
    ]

    with patch("src.apps.system.rate_limits.services.is_valid_path", return_value=True):
        with pytest.raises(DuplicateValueException):
            await service.update_rate_limit(
                db=object(),
                tier_id=uuid4(),
                rate_limit_id=current_id,
                values=RateLimitUpdate(path="users"),
                app=object(),
            )

    rate_limit_repo.update.assert_not_awaited()


async def test_update_rate_limit_allows_same_path() -> None:
    current_id = uuid4()
    service, rate_limit_repo, tier_repo = _service()
    tier_repo.get.return_value = {"id": uuid4()}
    rate_limit_repo.get.return_value = {"id": current_id, "path": "users", "name": "oldname"}
    values = RateLimitUpdate(path="users")

    with patch("src.apps.system.rate_limits.services.is_valid_path", return_value=True):
        result = await service.update_rate_limit(
            db=object(),
            tier_id=uuid4(),
            rate_limit_id=current_id,
            values=values,
            app=object(),
        )

    assert result == {"message": "Rate Limit updated"}
    rate_limit_repo.update.assert_awaited_once()


async def test_update_rate_limit_allows_same_name() -> None:
    current_id = uuid4()
    service, rate_limit_repo, tier_repo = _service()
    tier_repo.get.return_value = {"id": uuid4()}
    rate_limit_repo.get.return_value = {"id": current_id, "path": "users", "name": "oldname"}

    result = await service.update_rate_limit(
        db=object(),
        tier_id=uuid4(),
        rate_limit_id=current_id,
        values=RateLimitUpdate(name="oldname"),
        app=object(),
    )

    assert result == {"message": "Rate Limit updated"}
    rate_limit_repo.update.assert_awaited_once()


async def test_update_rate_limit_rejects_duplicate_name() -> None:
    current_id = uuid4()
    service, rate_limit_repo, tier_repo = _service()
    tier_repo.get.return_value = {"id": uuid4()}
    rate_limit_repo.get.side_effect = [
        {"id": current_id, "path": "users", "name": "oldname"},
        {"id": uuid4(), "name": "taken"},
    ]

    with pytest.raises(DuplicateValueException):
        await service.update_rate_limit(
            db=object(),
            tier_id=uuid4(),
            rate_limit_id=current_id,
            values=RateLimitUpdate(name="taken"),
            app=object(),
        )

    rate_limit_repo.update.assert_not_awaited()


async def test_update_rate_limit_writes_values() -> None:
    service, rate_limit_repo, tier_repo = _service()
    tier_repo.get.return_value = {"id": uuid4()}
    rate_limit_repo.get.return_value = {"id": uuid4()}
    rate_limit_repo.exists.return_value = False
    values = RateLimitUpdate(limit=10)

    result = await service.update_rate_limit(
        db=object(),
        tier_id=uuid4(),
        rate_limit_id=uuid4(),
        values=values,
        app=object(),
    )

    assert result == {"message": "Rate Limit updated"}
    rate_limit_repo.update.assert_awaited_once()


async def test_db_delete_rate_limit_raises_when_tier_missing() -> None:
    service, rate_limit_repo, tier_repo = _service()
    tier_repo.get.return_value = None

    with pytest.raises(NotFoundException):
        await service.db_delete_rate_limit(db=object(), tier_id=uuid4(), rate_limit_id=uuid4())

    rate_limit_repo.db_delete.assert_not_awaited()


async def test_db_delete_rate_limit_raises_when_missing() -> None:
    service, rate_limit_repo, tier_repo = _service()
    tier_repo.get.return_value = {"id": uuid4()}
    rate_limit_repo.get.return_value = None

    with pytest.raises(NotFoundException):
        await service.db_delete_rate_limit(db=object(), tier_id=uuid4(), rate_limit_id=uuid4())

    rate_limit_repo.db_delete.assert_not_awaited()


async def test_db_delete_rate_limit_integrity_error_is_forbidden() -> None:
    service, rate_limit_repo, tier_repo = _service()
    tier_repo.get.return_value = {"id": uuid4()}
    rate_limit_repo.get.return_value = {"id": uuid4()}
    rate_limit_repo.db_delete.side_effect = _integrity_error()

    with pytest.raises(ForbiddenException):
        await service.db_delete_rate_limit(db=object(), tier_id=uuid4(), rate_limit_id=uuid4())


async def test_db_delete_rate_limit_unexpected_error_is_internal() -> None:
    service, rate_limit_repo, tier_repo = _service()
    tier_repo.get.return_value = {"id": uuid4()}
    rate_limit_repo.get.return_value = {"id": uuid4()}
    rate_limit_repo.db_delete.side_effect = RuntimeError("boom")

    with pytest.raises(InternalErrorException):
        await service.db_delete_rate_limit(db=object(), tier_id=uuid4(), rate_limit_id=uuid4())


async def test_db_delete_rate_limit_hard_deletes() -> None:
    service, rate_limit_repo, tier_repo = _service()
    tier_repo.get.return_value = {"id": uuid4()}
    rate_limit_repo.get.return_value = {"id": uuid4()}

    result = await service.db_delete_rate_limit(
        db=object(),
        tier_id=uuid4(),
        rate_limit_id=uuid4(),
    )

    assert result == {"message": "Rate Limit deleted from the database"}
    rate_limit_repo.db_delete.assert_awaited_once()
