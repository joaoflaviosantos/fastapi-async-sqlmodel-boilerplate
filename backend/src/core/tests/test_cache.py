# Built-in Dependencies
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

# Third-Party Dependencies
import pytest
from fastapi import Request

# Local Dependencies
from src.core.exceptions.cache_exceptions import (
    CacheIdentificationInferenceError,
    InvalidRequestError,
)
from src.core.utils import cache as cache_mod
from src.core.utils.cache import (
    _as_scan_pattern,
    _delete_keys_by_pattern,
    _format_prefix,
    _infer_resource_id,
    cache,
)

pytestmark = pytest.mark.unit


def _request(method: str = "GET") -> Request:
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 123),
        "server": ("test", 80),
    }
    return Request(scope)


def test_as_scan_pattern_does_not_double_star() -> None:
    assert _as_scan_pattern("blog:posts:user:abc:*") == "blog:posts:user:abc:*"
    assert _as_scan_pattern("blog:posts:user:abc:") == "blog:posts:user:abc:*"


def test_format_prefix_fingerprints_dicts_stably() -> None:
    template = "blog:posts:filters_{filters}"
    left = _format_prefix(template, {"filters": {"b": 1, "a": 2}})
    right = _format_prefix(template, {"filters": {"a": 2, "b": 1}})
    assert left == right
    assert '"a"' in left


def test_format_prefix_fingerprints_lists_stably() -> None:
    template = "blog:posts:sort_by_{sort_by}"
    left = _format_prefix(template, {"sort_by": [("title", "asc")]})
    right = _format_prefix(template, {"sort_by": [("title", "asc")]})
    assert left == right


def test_infer_resource_id_uses_last_matching_id() -> None:
    post_id = uuid4()
    user_id = uuid4()
    inferred = _infer_resource_id(
        {"request": object(), "user_id": user_id, "post_id": post_id},
        resource_id_type=UUID,
    )
    assert inferred == post_id


def test_infer_resource_id_skips_values_without_id_in_name() -> None:
    with pytest.raises(CacheIdentificationInferenceError):
        _infer_resource_id({"title": "hello"}, resource_id_type=str)


async def test_delete_keys_by_pattern_continues_when_batch_is_empty() -> None:
    mock_client = AsyncMock()
    mock_client.scan = AsyncMock(
        side_effect=[
            (42, []),
            (0, [b"k2"]),
        ]
    )
    mock_client.delete = AsyncMock()

    with patch.object(cache_mod, "client", mock_client):
        await _delete_keys_by_pattern("blog:posts:*")

    assert mock_client.scan.await_count == 2
    mock_client.delete.assert_awaited_once_with(b"k2")


async def test_delete_keys_by_pattern_skips_when_client_missing() -> None:
    with patch.object(cache_mod, "client", None):
        await _delete_keys_by_pattern("blog:posts:*")


async def test_cache_get_uses_setex_and_returns_handler_result() -> None:
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=None)
    mock_client.set = AsyncMock()
    payload = {"id": "abc"}
    calls = {"n": 0}

    @cache(key_prefix="blog:post", resource_id_name="post_id", expiration=60)
    async def read_post(request: Request, post_id: str) -> dict:
        calls["n"] += 1
        return payload

    with patch.object(cache_mod, "client", mock_client):
        result = await read_post(_request("GET"), post_id="abc")

    assert result is payload
    assert calls["n"] == 1
    mock_client.set.assert_awaited_once()
    assert mock_client.set.await_args.kwargs.get("ex") == 60
    mock_client.expire.assert_not_called()


async def test_cache_get_hit_skips_handler() -> None:
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value='{"id": "cached"}')
    calls = {"n": 0}

    @cache(key_prefix="blog:post", resource_id_name="post_id")
    async def read_post(request: Request, post_id: str) -> dict:
        calls["n"] += 1
        return {"id": "fresh"}

    with patch.object(cache_mod, "client", mock_client):
        result = await read_post(_request("GET"), post_id="abc")

    assert result == {"id": "cached"}
    assert calls["n"] == 0


async def test_cache_get_infers_uuid_resource_id() -> None:
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=None)
    mock_client.set = AsyncMock()
    post_id = uuid4()

    @cache(key_prefix="blog:post", resource_id_type=UUID)
    async def read_post(request: Request, post_id: UUID) -> dict:
        return {"id": str(post_id)}

    with patch.object(cache_mod, "client", mock_client):
        result = await read_post(_request("GET"), post_id=post_id)

    assert result == {"id": str(post_id)}
    cache_key = mock_client.get.await_args.args[0]
    assert cache_key == f"blog:post:{post_id}"


async def test_cache_get_fails_open_without_client() -> None:
    @cache(key_prefix="blog:post", resource_id_name="post_id")
    async def read_post(request: Request, post_id: str) -> dict:
        return {"id": post_id}

    with patch.object(cache_mod, "client", None):
        result = await read_post(_request("GET"), post_id="abc")

    assert result == {"id": "abc"}


async def test_cache_get_fails_open_when_redis_get_raises() -> None:
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=ConnectionError("redis down"))

    @cache(key_prefix="blog:post", resource_id_name="post_id")
    async def read_post(request: Request, post_id: str) -> dict:
        return {"id": post_id}

    with patch.object(cache_mod, "client", mock_client):
        result = await read_post(_request("GET"), post_id="abc")

    assert result == {"id": "abc"}
    mock_client.set.assert_not_called()


async def test_cache_get_fails_open_when_setex_raises() -> None:
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=None)
    mock_client.set = AsyncMock(side_effect=ConnectionError("redis down"))

    @cache(key_prefix="blog:post", resource_id_name="post_id")
    async def read_post(request: Request, post_id: str) -> dict:
        return {"id": post_id}

    with patch.object(cache_mod, "client", mock_client):
        result = await read_post(_request("GET"), post_id="abc")

    assert result == {"id": "abc"}


async def test_cache_get_rejects_invalidate_params() -> None:
    @cache(
        key_prefix="blog:post",
        resource_id_name="post_id",
        pattern_to_invalidate_extra=["blog:posts:*"],
    )
    async def read_post(request: Request, post_id: str) -> dict:
        return {"id": post_id}

    with pytest.raises(InvalidRequestError):
        await read_post(_request("GET"), post_id="abc")


async def test_cache_post_without_resource_id_only_scans_lists() -> None:
    mock_client = AsyncMock()
    mock_client.scan = AsyncMock(return_value=(0, ["blog:posts:user:u1:page:1"]))
    mock_client.delete = AsyncMock()

    @cache(
        key_prefix="blog:post",
        pattern_to_invalidate_extra=["blog:posts:user:{user_id}:*"],
    )
    async def write_post(request: Request, user_id: str) -> dict:
        return {"created": True}

    with patch.object(cache_mod, "client", mock_client):
        result = await write_post(_request("POST"), user_id="u1")

    assert result == {"created": True}
    mock_client.scan.assert_awaited_once()
    assert mock_client.scan.await_args.kwargs["match"] == "blog:posts:user:u1:*"
    delete_keys = [call.args[0] for call in mock_client.delete.await_args_list]
    assert "blog:post:None" not in delete_keys
    assert "blog:post:u1" not in delete_keys
    assert "blog:posts:user:u1:page:1" in delete_keys


async def test_cache_patch_deletes_item_key() -> None:
    mock_client = AsyncMock()
    mock_client.scan = AsyncMock(return_value=(0, []))
    mock_client.delete = AsyncMock()

    @cache(
        key_prefix="blog:post",
        resource_id_name="post_id",
        pattern_to_invalidate_extra=["blog:posts:user:{user_id}:*"],
    )
    async def patch_post(request: Request, user_id: str, post_id: str) -> dict:
        return {"message": "updated"}

    with patch.object(cache_mod, "client", mock_client):
        await patch_post(_request("PATCH"), user_id="u1", post_id="p1")

    mock_client.delete.assert_any_await("blog:post:p1")


async def test_cache_write_invalidation_failure_does_not_hide_result() -> None:
    mock_client = AsyncMock()
    mock_client.delete = AsyncMock(side_effect=ConnectionError("redis down"))

    @cache(key_prefix="blog:post", resource_id_name="post_id")
    async def patch_post(request: Request, post_id: str) -> dict:
        return {"message": "updated"}

    with patch.object(cache_mod, "client", mock_client):
        result = await patch_post(_request("PATCH"), post_id="p1")

    assert result == {"message": "updated"}
