# Built-in Dependencies
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

# Third-Party Dependencies
import pytest
from sqlalchemy.exc import IntegrityError

# Local Dependencies
from src.apps.blog.posts.schemas import PostCreate, PostUpdate
from src.apps.blog.posts.services import PostService
from src.core.exceptions.http_exceptions import (
    ForbiddenException,
    InternalErrorException,
    NotFoundException,
    UnprocessableEntityException,
)

pytestmark = pytest.mark.unit


def _post_create(tag_ids: list[UUID] | None = None) -> PostCreate:
    return PostCreate(
        title="Hello post",
        text="This is the content of an example post.",
        tag_ids=tag_ids or [uuid4()],
    )


def _integrity_error() -> IntegrityError:
    return IntegrityError("INSERT", {}, Exception("orig"))


def _service(
    post_repo: AsyncMock | None = None,
    user_repo: AsyncMock | None = None,
    tag_repo: AsyncMock | None = None,
    assoc_repo: AsyncMock | None = None,
) -> tuple[PostService, AsyncMock, AsyncMock, AsyncMock, AsyncMock]:
    post_repo = post_repo or AsyncMock()
    user_repo = user_repo or AsyncMock()
    tag_repo = tag_repo or AsyncMock()
    assoc_repo = assoc_repo or AsyncMock()
    return (
        PostService(
            post_repo=post_repo,
            user_repo=user_repo,
            tag_repo=tag_repo,
            assoc_repo=assoc_repo,
        ),
        post_repo,
        user_repo,
        tag_repo,
        assoc_repo,
    )


async def test_create_post_raises_when_user_missing() -> None:
    user_id = uuid4()
    service, post_repo, user_repo, _, _ = _service()
    user_repo.get.return_value = None

    with pytest.raises(NotFoundException):
        await service.create_post(
            db=object(),
            user_id=user_id,
            post=_post_create(),
            current_user={"id": user_id},
        )

    post_repo.create.assert_not_awaited()


async def test_create_post_forbidden_for_other_user() -> None:
    user_id = uuid4()
    service, post_repo, user_repo, _, _ = _service()
    user_repo.get.return_value = {"id": user_id}

    with pytest.raises(ForbiddenException):
        await service.create_post(
            db=object(),
            user_id=user_id,
            post=_post_create(),
            current_user={"id": uuid4()},
        )

    post_repo.create.assert_not_awaited()


async def test_create_post_raises_when_tag_missing() -> None:
    user_id = uuid4()
    service, post_repo, user_repo, tag_repo, _ = _service()
    user_repo.get.return_value = {"id": user_id}
    tag_repo.get.return_value = None

    with pytest.raises(NotFoundException, match="Tag not found"):
        await service.create_post(
            db=object(),
            user_id=user_id,
            post=_post_create(),
            current_user={"id": user_id},
        )

    post_repo.create.assert_not_awaited()


async def test_create_post_rejects_duplicate_tag_ids() -> None:
    user_id = uuid4()
    tag_id = uuid4()
    service, post_repo, user_repo, _, _ = _service()
    user_repo.get.return_value = {"id": user_id}

    with pytest.raises(UnprocessableEntityException, match="Duplicate"):
        await service.create_post(
            db=object(),
            user_id=user_id,
            post=_post_create(tag_ids=[tag_id, tag_id]),
            current_user={"id": user_id},
        )

    post_repo.create.assert_not_awaited()


async def test_validated_tag_ids_rejects_empty() -> None:
    service, _, _, _, _ = _service()

    with pytest.raises(UnprocessableEntityException, match="at least one tag"):
        await service._validated_tag_ids(db=object(), tag_ids=[])


async def test_create_post_writes_row() -> None:
    user_id = uuid4()
    post_id = uuid4()
    tag_id = uuid4()
    created = {"id": post_id, "title": "Hello post", "tags": [{"id": tag_id}]}
    service, post_repo, user_repo, tag_repo, assoc_repo = _service()
    user_repo.get.return_value = {"id": user_id}
    tag_repo.get.return_value = {"id": tag_id, "name": "Python"}
    post_repo.create.return_value = SimpleNamespace(id=post_id)
    post_repo.get_single_with_main_relations.return_value = created

    result = await service.create_post(
        db=object(),
        user_id=user_id,
        post=_post_create(tag_ids=[tag_id]),
        current_user={"id": user_id},
    )

    assert result == created
    post_repo.create.assert_awaited_once()
    assoc_repo.create.assert_awaited_once()
    post_repo.get_single_with_main_relations.assert_awaited_once()


async def test_create_post_raises_when_reread_missing() -> None:
    user_id = uuid4()
    service, post_repo, user_repo, tag_repo, _ = _service()
    user_repo.get.return_value = {"id": user_id}
    tag_repo.get.return_value = {"id": uuid4(), "name": "Python"}
    post_repo.create.return_value = SimpleNamespace(id=uuid4())
    post_repo.get_single_with_main_relations.return_value = None

    with pytest.raises(InternalErrorException):
        await service.create_post(
            db=object(),
            user_id=user_id,
            post=_post_create(),
            current_user={"id": user_id},
        )


async def test_get_posts_raises_when_user_missing() -> None:
    service, _, user_repo, _, _ = _service()
    user_repo.get.return_value = None

    with pytest.raises(NotFoundException):
        await service.get_posts(db=object(), user_id=uuid4())


async def test_get_posts_returns_paginated_dict() -> None:
    user_id = uuid4()
    service, post_repo, user_repo, _, _ = _service()
    user_repo.get.return_value = {"id": user_id}
    post_repo.get_multi_with_main_relations.return_value = {
        "data": [{"title": "Hello post"}],
        "total_count": 1,
    }

    result = await service.get_posts(db=object(), user_id=user_id)

    assert result["data"] == [{"title": "Hello post"}]
    post_repo.get_multi_with_main_relations.assert_awaited_once()


async def test_get_post_raises_when_user_missing() -> None:
    service, _, user_repo, _, _ = _service()
    user_repo.get.return_value = None

    with pytest.raises(NotFoundException):
        await service.get_post(db=object(), user_id=uuid4(), post_id=uuid4())


async def test_get_post_raises_when_missing() -> None:
    service, post_repo, user_repo, _, _ = _service()
    user_repo.get.return_value = {"id": uuid4()}
    post_repo.get_single_with_main_relations.return_value = None

    with pytest.raises(NotFoundException):
        await service.get_post(db=object(), user_id=uuid4(), post_id=uuid4())


async def test_get_post_returns_row() -> None:
    row = {"id": uuid4(), "title": "Hello post", "tags": []}
    service, post_repo, user_repo, _, _ = _service()
    user_repo.get.return_value = {"id": uuid4()}
    post_repo.get_single_with_main_relations.return_value = row

    result = await service.get_post(db=object(), user_id=uuid4(), post_id=uuid4())

    assert result == row


async def test_update_post_raises_when_user_missing() -> None:
    service, post_repo, user_repo, _, _ = _service()
    user_repo.get.return_value = None

    with pytest.raises(NotFoundException):
        await service.update_post(
            db=object(),
            user_id=uuid4(),
            post_id=uuid4(),
            values=PostUpdate(title="Updated post"),
            current_user={"id": uuid4()},
        )

    post_repo.update.assert_not_awaited()


async def test_update_post_forbidden_for_other_user() -> None:
    user_id = uuid4()
    service, post_repo, user_repo, _, _ = _service()
    user_repo.get.return_value = {"id": user_id}

    with pytest.raises(ForbiddenException):
        await service.update_post(
            db=object(),
            user_id=user_id,
            post_id=uuid4(),
            values=PostUpdate(title="Updated post"),
            current_user={"id": uuid4()},
        )

    post_repo.update.assert_not_awaited()


async def test_update_post_raises_when_missing() -> None:
    user_id = uuid4()
    service, post_repo, user_repo, _, _ = _service()
    user_repo.get.return_value = {"id": user_id}
    post_repo.get.return_value = None

    with pytest.raises(NotFoundException):
        await service.update_post(
            db=object(),
            user_id=user_id,
            post_id=uuid4(),
            values=PostUpdate(title="Updated post"),
            current_user={"id": user_id},
        )

    post_repo.update.assert_not_awaited()


async def test_update_post_writes_values() -> None:
    user_id = uuid4()
    service, post_repo, user_repo, _, assoc_repo = _service()
    user_repo.get.return_value = {"id": user_id}
    post_repo.get.return_value = {"id": uuid4()}
    values = PostUpdate(title="Updated post")

    result = await service.update_post(
        db=object(),
        user_id=user_id,
        post_id=uuid4(),
        values=values,
        current_user={"id": user_id},
    )

    assert result == {"message": "Post updated"}
    post_repo.update.assert_awaited_once()
    assoc_repo.create.assert_not_awaited()


async def test_update_post_replaces_tags() -> None:
    user_id = uuid4()
    tag_id = uuid4()
    service, post_repo, user_repo, tag_repo, assoc_repo = _service()
    user_repo.get.return_value = {"id": user_id}
    post_repo.get.return_value = {"id": uuid4()}
    tag_repo.get.return_value = {"id": tag_id, "name": "Python"}

    result = await service.update_post(
        db=object(),
        user_id=user_id,
        post_id=uuid4(),
        values=PostUpdate(tag_ids=[tag_id]),
        current_user={"id": user_id},
    )

    assert result == {"message": "Post updated"}
    assoc_repo.db_delete.assert_awaited_once()
    assoc_repo.create.assert_awaited_once()
    post_repo.update.assert_awaited_once()


async def test_delete_post_raises_when_user_missing() -> None:
    service, post_repo, user_repo, _, _ = _service()
    user_repo.get.return_value = None

    with pytest.raises(NotFoundException):
        await service.delete_post(
            db=object(),
            user_id=uuid4(),
            post_id=uuid4(),
            current_user={"id": uuid4(), "is_superuser": False},
        )

    post_repo.delete.assert_not_awaited()


async def test_delete_post_forbidden_for_other_regular_user() -> None:
    user_id = uuid4()
    service, post_repo, user_repo, _, _ = _service()
    user_repo.get.return_value = {"id": user_id}

    with pytest.raises(ForbiddenException):
        await service.delete_post(
            db=object(),
            user_id=user_id,
            post_id=uuid4(),
            current_user={"id": uuid4(), "is_superuser": False},
        )

    post_repo.delete.assert_not_awaited()


async def test_delete_post_already_deleted_for_superuser() -> None:
    user_id = uuid4()
    service, post_repo, user_repo, _, _ = _service()
    user_repo.get.return_value = {"id": user_id}
    post_repo.get.return_value = None

    with pytest.raises(NotFoundException, match="already deleted"):
        await service.delete_post(
            db=object(),
            user_id=user_id,
            post_id=uuid4(),
            current_user={"id": uuid4(), "is_superuser": True},
        )

    post_repo.delete.assert_not_awaited()


async def test_delete_post_missing_for_regular_user() -> None:
    user_id = uuid4()
    service, post_repo, user_repo, _, _ = _service()
    user_repo.get.return_value = {"id": user_id}
    post_repo.get.return_value = None

    with pytest.raises(NotFoundException, match="Post not found"):
        await service.delete_post(
            db=object(),
            user_id=user_id,
            post_id=uuid4(),
            current_user={"id": user_id, "is_superuser": False},
        )

    post_repo.delete.assert_not_awaited()


async def test_delete_post_soft_deletes() -> None:
    user_id = uuid4()
    post_id = uuid4()
    db_post = {"id": post_id, "is_deleted": False}
    service, post_repo, user_repo, _, _ = _service()
    user_repo.get.return_value = {"id": user_id}
    post_repo.get.return_value = db_post

    result = await service.delete_post(
        db=object(),
        user_id=user_id,
        post_id=post_id,
        current_user={"id": user_id, "is_superuser": False},
    )

    assert result == {"message": "Post deleted"}
    post_repo.delete.assert_awaited_once()


async def test_db_delete_post_raises_when_user_missing() -> None:
    service, post_repo, user_repo, _, assoc_repo = _service()
    user_repo.get.return_value = None

    with pytest.raises(NotFoundException):
        await service.db_delete_post(db=object(), user_id=uuid4(), post_id=uuid4())

    assoc_repo.db_delete.assert_not_awaited()
    post_repo.db_delete.assert_not_awaited()


async def test_db_delete_post_raises_when_missing() -> None:
    service, post_repo, user_repo, _, assoc_repo = _service()
    user_repo.get.return_value = {"id": uuid4()}
    post_repo.get.return_value = None

    with pytest.raises(NotFoundException):
        await service.db_delete_post(db=object(), user_id=uuid4(), post_id=uuid4())

    assoc_repo.db_delete.assert_not_awaited()
    post_repo.db_delete.assert_not_awaited()


async def test_db_delete_post_integrity_error_is_forbidden() -> None:
    service, post_repo, user_repo, _, _ = _service()
    user_repo.get.return_value = {"id": uuid4()}
    post_repo.get.return_value = {"id": uuid4()}
    post_repo.db_delete.side_effect = _integrity_error()

    with pytest.raises(ForbiddenException):
        await service.db_delete_post(db=object(), user_id=uuid4(), post_id=uuid4())


async def test_db_delete_post_unexpected_error_is_internal() -> None:
    service, post_repo, user_repo, _, _ = _service()
    user_repo.get.return_value = {"id": uuid4()}
    post_repo.get.return_value = {"id": uuid4()}
    post_repo.db_delete.side_effect = RuntimeError("boom")

    with pytest.raises(InternalErrorException):
        await service.db_delete_post(db=object(), user_id=uuid4(), post_id=uuid4())


async def test_db_delete_post_hard_deletes() -> None:
    service, post_repo, user_repo, _, assoc_repo = _service()
    user_repo.get.return_value = {"id": uuid4()}
    post_repo.get.return_value = {"id": uuid4()}

    result = await service.db_delete_post(db=object(), user_id=uuid4(), post_id=uuid4())

    assert result == {"message": "Post deleted from the database"}
    assoc_repo.db_delete.assert_awaited_once()
    post_repo.db_delete.assert_awaited_once()
