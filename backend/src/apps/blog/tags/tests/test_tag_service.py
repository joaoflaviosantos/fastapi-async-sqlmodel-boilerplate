# Built-in Dependencies
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

# Third-Party Dependencies
import pytest
from sqlalchemy.exc import IntegrityError

# Local Dependencies
from src.apps.blog.tags.schemas import TagCreate, TagUpdate
from src.apps.blog.tags.services import TagService
from src.core.exceptions.http_exceptions import (
    DuplicateValueException,
    ForbiddenException,
    InternalErrorException,
    NotFoundException,
)

pytestmark = pytest.mark.unit


def _integrity_error() -> IntegrityError:
    return IntegrityError("INSERT", {}, Exception("orig"))


def _service(
    tag_repo: AsyncMock | None = None,
    assoc_repo: AsyncMock | None = None,
) -> tuple[TagService, AsyncMock, AsyncMock]:
    tag_repo = tag_repo or AsyncMock()
    assoc_repo = assoc_repo or AsyncMock()
    return TagService(tag_repo=tag_repo, assoc_repo=assoc_repo), tag_repo, assoc_repo


async def test_create_tag_rejects_duplicate_name() -> None:
    service, tag_repo, _ = _service()
    tag_repo.get.return_value = {"id": uuid4(), "name": "Python"}

    with pytest.raises(DuplicateValueException):
        await service.create_tag(db=object(), tag=TagCreate(name="Python"))

    tag_repo.create.assert_not_awaited()


async def test_create_tag_writes_row() -> None:
    tag_id = uuid4()
    service, tag_repo, _ = _service()
    tag_repo.get.side_effect = [None, {"id": tag_id, "name": "Python"}]
    tag_repo.create.return_value = SimpleNamespace(id=tag_id)

    result = await service.create_tag(db=object(), tag=TagCreate(name="Python"))

    assert result["id"] == tag_id
    tag_repo.create.assert_awaited_once()


async def test_get_tags_returns_paginated_dict() -> None:
    service, tag_repo, _ = _service()
    tag_repo.get_multi.return_value = {"data": [{"name": "Python"}], "total_count": 1}

    result = await service.get_tags(db=object())

    assert result["data"] == [{"name": "Python"}]
    tag_repo.get_multi.assert_awaited_once()


async def test_get_tag_raises_when_missing() -> None:
    service, tag_repo, _ = _service()
    tag_repo.get.return_value = None

    with pytest.raises(NotFoundException):
        await service.get_tag(db=object(), tag_id=uuid4())


async def test_get_tag_returns_row() -> None:
    tag_id = uuid4()
    row = {"id": tag_id, "name": "Python"}
    service, tag_repo, _ = _service()
    tag_repo.get.return_value = row

    result = await service.get_tag(db=object(), tag_id=tag_id)

    assert result == row
    tag_repo.get.assert_awaited_once()


async def test_update_tag_raises_when_missing() -> None:
    service, tag_repo, _ = _service()
    tag_repo.get.return_value = None

    with pytest.raises(NotFoundException):
        await service.update_tag(
            db=object(),
            tag_id=uuid4(),
            values=TagUpdate(name="Updated"),
        )

    tag_repo.update.assert_not_awaited()


async def test_update_tag_rejects_duplicate_name() -> None:
    tag_id = uuid4()
    service, tag_repo, _ = _service()
    tag_repo.get.side_effect = [
        {"id": tag_id, "name": "Python"},
        {"id": uuid4(), "name": "FastAPI"},
    ]

    with pytest.raises(DuplicateValueException):
        await service.update_tag(
            db=object(),
            tag_id=tag_id,
            values=TagUpdate(name="FastAPI"),
        )

    tag_repo.update.assert_not_awaited()


async def test_update_tag_writes_values() -> None:
    tag_id = uuid4()
    service, tag_repo, _ = _service()
    tag_repo.get.side_effect = [
        {"id": tag_id, "name": "Python"},
        {"id": tag_id, "name": "Python"},
    ]

    result = await service.update_tag(
        db=object(),
        tag_id=tag_id,
        values=TagUpdate(name="Python"),
    )

    assert result == {"message": "Tag updated"}
    tag_repo.update.assert_awaited_once()


async def test_delete_tag_already_deleted_for_superuser() -> None:
    service, tag_repo, assoc_repo = _service()
    tag_repo.get.return_value = None

    with pytest.raises(NotFoundException, match="already deleted"):
        await service.delete_tag(
            db=object(),
            tag_id=uuid4(),
            current_user={"id": uuid4(), "is_superuser": True},
        )

    assoc_repo.exists_for_active_post.assert_not_awaited()
    tag_repo.delete.assert_not_awaited()


async def test_delete_tag_missing_for_regular_user() -> None:
    service, tag_repo, assoc_repo = _service()
    tag_repo.get.return_value = None

    with pytest.raises(NotFoundException, match="Tag not found"):
        await service.delete_tag(
            db=object(),
            tag_id=uuid4(),
            current_user={"id": uuid4(), "is_superuser": False},
        )

    assoc_repo.exists_for_active_post.assert_not_awaited()
    tag_repo.delete.assert_not_awaited()


async def test_delete_tag_forbidden_when_assigned_to_post() -> None:
    tag_id = uuid4()
    service, tag_repo, assoc_repo = _service()
    tag_repo.get.return_value = {"id": tag_id, "is_deleted": False}
    assoc_repo.exists_for_active_post.return_value = True

    with pytest.raises(ForbiddenException, match="assigned to a post"):
        await service.delete_tag(
            db=object(),
            tag_id=tag_id,
            current_user={"id": uuid4(), "is_superuser": False},
        )

    tag_repo.delete.assert_not_awaited()


async def test_delete_tag_soft_deletes() -> None:
    tag_id = uuid4()
    db_tag = {"id": tag_id, "is_deleted": False}
    service, tag_repo, assoc_repo = _service()
    tag_repo.get.return_value = db_tag
    assoc_repo.exists_for_active_post.return_value = False

    result = await service.delete_tag(
        db=object(),
        tag_id=tag_id,
        current_user={"id": uuid4(), "is_superuser": False},
    )

    assert result == {"message": "Tag deleted"}
    tag_repo.delete.assert_awaited_once()


async def test_db_delete_tag_raises_when_missing() -> None:
    service, tag_repo, assoc_repo = _service()
    tag_repo.get.return_value = None

    with pytest.raises(NotFoundException):
        await service.db_delete_tag(db=object(), tag_id=uuid4())

    assoc_repo.exists_for_active_post.assert_not_awaited()
    tag_repo.db_delete.assert_not_awaited()


async def test_db_delete_tag_forbidden_when_assigned_to_post() -> None:
    tag_id = uuid4()
    service, tag_repo, assoc_repo = _service()
    tag_repo.get.return_value = {"id": tag_id}
    assoc_repo.exists_for_active_post.return_value = True

    with pytest.raises(ForbiddenException, match="assigned to a post"):
        await service.db_delete_tag(db=object(), tag_id=tag_id)

    tag_repo.db_delete.assert_not_awaited()


async def test_db_delete_tag_integrity_error_is_forbidden() -> None:
    service, tag_repo, assoc_repo = _service()
    tag_repo.get.return_value = {"id": uuid4()}
    assoc_repo.exists_for_active_post.return_value = False
    tag_repo.db_delete.side_effect = _integrity_error()

    with pytest.raises(ForbiddenException):
        await service.db_delete_tag(db=object(), tag_id=uuid4())


async def test_db_delete_tag_unexpected_error_is_internal() -> None:
    service, tag_repo, assoc_repo = _service()
    tag_repo.get.return_value = {"id": uuid4()}
    assoc_repo.exists_for_active_post.return_value = False
    tag_repo.db_delete.side_effect = RuntimeError("boom")

    with pytest.raises(InternalErrorException):
        await service.db_delete_tag(db=object(), tag_id=uuid4())


async def test_db_delete_tag_hard_deletes() -> None:
    service, tag_repo, assoc_repo = _service()
    tag_repo.get.return_value = {"id": uuid4()}
    assoc_repo.exists_for_active_post.return_value = False

    result = await service.db_delete_tag(db=object(), tag_id=uuid4())

    assert result == {"message": "Tag deleted from the database"}
    tag_repo.db_delete.assert_awaited_once()
