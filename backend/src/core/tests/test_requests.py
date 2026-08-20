# Built-in Dependencies
from unittest.mock import AsyncMock, MagicMock, patch

# Third-Party Dependencies
import httpx
import pytest

# Local Dependencies
from src.core.exceptions.cache_exceptions import (
    CacheIdentificationInferenceError,
    InvalidRequestError,
    MissingClientError,
)
from src.core.utils.requests import (
    BadRequestException,
    _close_client_sync,
    _log_response_debug,
    _reset_client_after_fork,
    close_global_client,
    extract_error_message,
    get_global_client,
    make_delete_request,
    make_get_request,
    make_patch_request,
    make_post_request,
    make_put_request,
    raise_for_status,
    should_retry,
)

pytestmark = pytest.mark.unit


def _response(status_code: int = 200, payload: object | None = None, text: str = "") -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.text = text
    if payload is None:
        response.json.side_effect = ValueError("not json")
    else:
        response.json.return_value = payload
    response.raise_for_status = MagicMock()
    return response


def _client(method: str, response: MagicMock) -> AsyncMock:
    client = AsyncMock()
    getattr(client, method).return_value = response
    return client


def test_extract_error_message_from_nested_error() -> None:
    response = _response(payload={"error": {"message": "nested"}})
    assert extract_error_message(response) == "nested"


def test_extract_error_message_from_message_and_detail() -> None:
    assert extract_error_message(_response(payload={"message": "top"})) == "top"
    assert extract_error_message(_response(payload={"detail": "d"})) == "d"
    assert (
        extract_error_message(
            _response(
                payload={
                    "type": "about:blank",
                    "title": "Not Found",
                    "status": 404,
                    "detail": "gone",
                    "code": "not_found",
                }
            )
        )
        == "gone"
    )
    assert extract_error_message(_response(payload={"other": 1})) == "{'other': 1}"
    assert extract_error_message(_response(payload=["x"])) == "['x']"


def test_extract_error_message_falls_back_to_text() -> None:
    assert extract_error_message(_response(text="plain")) == "plain"


def test_raise_for_status_raises_bad_request() -> None:
    with pytest.raises(BadRequestException, match="400"):
        raise_for_status(_response(status_code=400, payload={"message": "nope"}))


def test_raise_for_status_delegates_to_httpx() -> None:
    response = _response(status_code=200)
    raise_for_status(response)
    response.raise_for_status.assert_called_once()


def test_should_retry_only_for_network_errors() -> None:
    assert should_retry(httpx.TimeoutException("t")) is True
    assert should_retry(httpx.RequestError("r")) is True
    assert should_retry(BadRequestException("b")) is False


def test_log_response_debug_json_and_text() -> None:
    _log_response_debug(_response(payload={"ok": True}))
    _log_response_debug(_response(text="plain"))


def test_reset_client_after_fork() -> None:
    import src.core.utils.requests as req

    req._thread_local.client = object()
    _reset_client_after_fork()
    assert req._thread_local.client is None


def test_close_client_sync_noop_without_client() -> None:
    import src.core.utils.requests as req

    req._thread_local.client = None
    _close_client_sync()


async def test_get_and_close_global_client() -> None:
    client = get_global_client()
    assert isinstance(client, httpx.AsyncClient)
    assert get_global_client() is client
    await close_global_client()
    await close_global_client()


async def test_make_get_request_returns_response() -> None:
    response = _response(payload={"ok": True})
    with patch("src.core.utils.requests.get_global_client", return_value=_client("get", response)):
        result = await make_get_request("http://example.test", debug_mode=True)

    assert result is response


async def test_make_post_put_patch_delete_requests() -> None:
    for func, method in (
        (make_post_request, "post"),
        (make_put_request, "put"),
        (make_patch_request, "patch"),
        (make_delete_request, "delete"),
    ):
        response = _response()
        with patch(
            "src.core.utils.requests.get_global_client",
            return_value=_client(method, response),
        ):
            result = await func("http://example.test", debug_mode=True)
        assert result is response


def test_cache_exceptions_default_messages() -> None:
    assert "infer id" in str(CacheIdentificationInferenceError())
    assert "not supported" in str(InvalidRequestError())
    assert "None" in str(MissingClientError())
