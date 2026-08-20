# Built-in Dependencies
from unittest.mock import AsyncMock
from uuid import uuid4

# Third-Party Dependencies
import pytest
from sqlalchemy.exc import IntegrityError

# Local Dependencies
from src.apps.system.tiers.schemas import TierCreate, TierUpdate
from src.apps.system.tiers.services import TierService
from src.core.exceptions.http_exceptions import (
    DuplicateValueException,
    ForbiddenException,
    InternalErrorException,
    NotFoundException,
)

pytestmark = pytest.mark.unit


def _integrity_error() -> IntegrityError:
    return IntegrityError("INSERT", {}, Exception("orig"))


async def test_create_tier_rejects_duplicate_name() -> None:
    tier_repo = AsyncMock()
    tier_repo.exists.return_value = True
    service = TierService(tier_repo)

    with pytest.raises(DuplicateValueException):
        await service.create_tier(db=object(), tier=TierCreate(name="Premium"))

    tier_repo.create.assert_not_awaited()


async def test_create_tier_writes_row() -> None:
    tier_repo = AsyncMock()
    tier_repo.exists.return_value = False
    created = {"id": uuid4(), "name": "Premium"}
    tier_repo.create.return_value = created
    service = TierService(tier_repo)

    result = await service.create_tier(db=object(), tier=TierCreate(name="Premium"))

    assert result == created
    tier_repo.create.assert_awaited_once()


async def test_get_tiers_returns_paginated_dict() -> None:
    tier_repo = AsyncMock()
    tier_repo.get_multi.return_value = {"data": [{"name": "free"}], "total_count": 1}
    service = TierService(tier_repo)

    result = await service.get_tiers(db=object())

    assert result["data"] == [{"name": "free"}]
    assert result["total_count"] == 1
    tier_repo.get_multi.assert_awaited_once()


async def test_get_tier_raises_when_missing() -> None:
    tier_repo = AsyncMock()
    tier_repo.get.return_value = None
    service = TierService(tier_repo)

    with pytest.raises(NotFoundException):
        await service.get_tier(db=object(), tier_id=uuid4())


async def test_get_tier_returns_row() -> None:
    tier_id = uuid4()
    tier_repo = AsyncMock()
    tier_repo.get.return_value = {"id": tier_id, "name": "Premium"}
    service = TierService(tier_repo)

    result = await service.get_tier(db=object(), tier_id=tier_id)

    assert result["id"] == tier_id
    tier_repo.get.assert_awaited_once()


async def test_update_tier_raises_when_missing() -> None:
    tier_repo = AsyncMock()
    tier_repo.get.return_value = None
    service = TierService(tier_repo)

    with pytest.raises(NotFoundException):
        await service.update_tier(
            db=object(),
            tier_id=uuid4(),
            values=TierUpdate(name="Renamed"),
        )

    tier_repo.update.assert_not_awaited()


async def test_update_tier_rejects_default(settings) -> None:
    tier_repo = AsyncMock()
    tier_repo.get.return_value = {"name": settings.TIER_NAME_DEFAULT}
    service = TierService(tier_repo)

    with pytest.raises(ForbiddenException):
        await service.update_tier(
            db=object(),
            tier_id=uuid4(),
            values=TierUpdate(name="Renamed"),
        )

    tier_repo.update.assert_not_awaited()


async def test_update_tier_writes_values() -> None:
    tier_repo = AsyncMock()
    tier_repo.get.return_value = {"name": "Premium"}
    service = TierService(tier_repo)
    values = TierUpdate(name="Gold")

    result = await service.update_tier(db=object(), tier_id=uuid4(), values=values)

    assert result == {"message": "Tier updated"}
    tier_repo.update.assert_awaited_once()


async def test_db_delete_tier_raises_when_missing() -> None:
    tier_repo = AsyncMock()
    tier_repo.get.return_value = None
    service = TierService(tier_repo)

    with pytest.raises(NotFoundException):
        await service.db_delete_tier(db=object(), tier_id=uuid4())

    tier_repo.db_delete.assert_not_awaited()


async def test_db_delete_tier_rejects_default(settings) -> None:
    tier_repo = AsyncMock()
    tier_repo.get.return_value = {"name": settings.TIER_NAME_DEFAULT}
    service = TierService(tier_repo)

    with pytest.raises(ForbiddenException):
        await service.db_delete_tier(db=object(), tier_id=uuid4())

    tier_repo.db_delete.assert_not_awaited()


async def test_db_delete_tier_integrity_error_is_forbidden() -> None:
    tier_repo = AsyncMock()
    tier_repo.get.return_value = {"name": "Premium"}
    tier_repo.db_delete.side_effect = _integrity_error()
    service = TierService(tier_repo)

    with pytest.raises(ForbiddenException):
        await service.db_delete_tier(db=object(), tier_id=uuid4())


async def test_db_delete_tier_unexpected_error_is_internal() -> None:
    tier_repo = AsyncMock()
    tier_repo.get.return_value = {"name": "Premium"}
    tier_repo.db_delete.side_effect = RuntimeError("boom")
    service = TierService(tier_repo)

    with pytest.raises(InternalErrorException):
        await service.db_delete_tier(db=object(), tier_id=uuid4())


async def test_db_delete_tier_hard_deletes() -> None:
    tier_repo = AsyncMock()
    tier_repo.get.return_value = {"name": "Premium"}
    service = TierService(tier_repo)

    result = await service.db_delete_tier(db=object(), tier_id=uuid4())

    assert result == {"message": "Tier deleted from the database"}
    tier_repo.db_delete.assert_awaited_once()
