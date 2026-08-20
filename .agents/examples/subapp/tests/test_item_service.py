# Built-in Dependencies
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

# Third-Party Dependencies
import pytest
from sqlalchemy.exc import IntegrityError

# Local Dependencies
from src.apps.example.items.schemas import ItemCreate, ItemUpdate
from src.apps.example.items.services import ItemService
from src.core.exceptions.http_exceptions import (
    ForbiddenException,
    InternalErrorException,
    NotFoundException,
)

pytestmark = pytest.mark.unit


def _item_create() -> ItemCreate:
    return ItemCreate(title="Example item", text="This is the content of an example item.")


def _integrity_error() -> IntegrityError:
    return IntegrityError("INSERT", {}, Exception("orig"))


async def test_create_item_writes_row() -> None:
    item_id = uuid4()
    user_id = uuid4()
    item_repo = AsyncMock()
    item_repo.create.return_value = SimpleNamespace(id=item_id)
    item_repo.get.return_value = {"id": item_id, "title": "Example item"}
    service = ItemService(item_repo=item_repo)

    result = await service.create_item(
        db=object(),
        item=_item_create(),
        current_user={"id": user_id},
    )

    assert result["id"] == item_id
    item_repo.create.assert_awaited_once()
    item_repo.get.assert_awaited_once()


async def test_get_items_returns_paginated_dict() -> None:
    item_repo = AsyncMock()
    item_repo.get_multi_with_main_relations.return_value = {
        "data": [{"title": "Example item"}],
        "total_count": 1,
    }
    service = ItemService(item_repo=item_repo)

    result = await service.get_items(db=object())

    assert result["data"] == [{"title": "Example item"}]
    item_repo.get_multi_with_main_relations.assert_awaited_once()


async def test_get_item_raises_when_missing() -> None:
    item_repo = AsyncMock()
    item_repo.get_single_with_main_relations.return_value = None
    service = ItemService(item_repo=item_repo)

    with pytest.raises(NotFoundException):
        await service.get_item(db=object(), item_id=uuid4())

    item_repo.get_single_with_main_relations.assert_awaited_once()


async def test_get_item_returns_row() -> None:
    item_id = uuid4()
    row = {"id": item_id, "title": "Example item"}
    item_repo = AsyncMock()
    item_repo.get_single_with_main_relations.return_value = row
    service = ItemService(item_repo=item_repo)

    result = await service.get_item(db=object(), item_id=item_id)

    assert result == row
    item_repo.get_single_with_main_relations.assert_awaited_once()


async def test_update_item_raises_when_missing() -> None:
    item_repo = AsyncMock()
    item_repo.get.return_value = None
    service = ItemService(item_repo=item_repo)

    with pytest.raises(NotFoundException):
        await service.update_item(
            db=object(),
            item_id=uuid4(),
            values=ItemUpdate(title="Updated item"),
        )

    item_repo.update.assert_not_awaited()


async def test_update_item_writes_values() -> None:
    item_repo = AsyncMock()
    item_repo.get.return_value = {"id": uuid4()}
    service = ItemService(item_repo=item_repo)
    values = ItemUpdate(title="Updated item")

    result = await service.update_item(db=object(), item_id=uuid4(), values=values)

    assert result == {"message": "Item updated"}
    item_repo.update.assert_awaited_once()


async def test_delete_item_already_deleted_for_superuser() -> None:
    item_repo = AsyncMock()
    item_repo.get.return_value = None
    service = ItemService(item_repo=item_repo)

    with pytest.raises(NotFoundException, match="already deleted"):
        await service.delete_item(
            db=object(),
            item_id=uuid4(),
            current_user={"id": uuid4(), "is_superuser": True},
        )

    item_repo.delete.assert_not_awaited()


async def test_delete_item_missing_for_regular_user() -> None:
    item_repo = AsyncMock()
    item_repo.get.return_value = None
    service = ItemService(item_repo=item_repo)

    with pytest.raises(NotFoundException, match="Item not found"):
        await service.delete_item(
            db=object(),
            item_id=uuid4(),
            current_user={"id": uuid4(), "is_superuser": False},
        )

    item_repo.delete.assert_not_awaited()


async def test_delete_item_soft_deletes() -> None:
    item_id = uuid4()
    db_item = {"id": item_id, "is_deleted": False}
    item_repo = AsyncMock()
    item_repo.get.return_value = db_item
    service = ItemService(item_repo=item_repo)

    result = await service.delete_item(
        db=object(),
        item_id=item_id,
        current_user={"id": uuid4(), "is_superuser": False},
    )

    assert result == {"message": "Item deleted"}
    item_repo.delete.assert_awaited_once()


async def test_db_delete_item_raises_when_missing() -> None:
    item_repo = AsyncMock()
    item_repo.get.return_value = None
    service = ItemService(item_repo=item_repo)

    with pytest.raises(NotFoundException):
        await service.db_delete_item(db=object(), item_id=uuid4())

    item_repo.db_delete.assert_not_awaited()


async def test_db_delete_item_integrity_error_is_forbidden() -> None:
    item_repo = AsyncMock()
    item_repo.get.return_value = {"id": uuid4()}
    item_repo.db_delete.side_effect = _integrity_error()
    service = ItemService(item_repo=item_repo)

    with pytest.raises(ForbiddenException):
        await service.db_delete_item(db=object(), item_id=uuid4())


async def test_db_delete_item_unexpected_error_is_internal() -> None:
    item_repo = AsyncMock()
    item_repo.get.return_value = {"id": uuid4()}
    item_repo.db_delete.side_effect = RuntimeError("boom")
    service = ItemService(item_repo=item_repo)

    with pytest.raises(InternalErrorException):
        await service.db_delete_item(db=object(), item_id=uuid4())


async def test_db_delete_item_hard_deletes() -> None:
    item_repo = AsyncMock()
    item_repo.get.return_value = {"id": uuid4()}
    service = ItemService(item_repo=item_repo)

    result = await service.db_delete_item(db=object(), item_id=uuid4())

    assert result == {"message": "Item deleted from the database"}
    item_repo.db_delete.assert_awaited_once()
