# Built-in Dependencies
import json
from unittest.mock import MagicMock, patch

# Third-Party Dependencies
import pytest
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError

# Local Dependencies
from src.core.exceptions.handlers import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from src.core.exceptions.http_exceptions import NotFoundException, RateLimitException
from src.core.exceptions.problem import problem_body

pytestmark = pytest.mark.unit


def _body(response) -> dict:
    return json.loads(response.body.decode())


async def test_custom_exception_becomes_problem_json() -> None:
    response = await http_exception_handler(MagicMock(), NotFoundException(detail="Tier not found"))

    assert response.status_code == 404
    assert response.media_type == "application/problem+json"
    assert _body(response) == problem_body("Tier not found", 404, "not_found")


async def test_http_exception_maps_status_to_code() -> None:
    response = await http_exception_handler(
        MagicMock(),
        HTTPException(
            status_code=401, detail="Not authenticated", headers={"WWW-Authenticate": "Bearer"}
        ),
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert _body(response)["code"] == "unauthorized"
    assert _body(response)["detail"] == "Not authenticated"


async def test_http_exception_list_detail_uses_first_message() -> None:
    response = await http_exception_handler(
        MagicMock(),
        HTTPException(
            status_code=422,
            detail=[
                {"loc": ["query", "sort_by"], "msg": "Invalid sort field: x", "type": "value_error"}
            ],
        ),
    )

    assert _body(response)["detail"] == "Invalid sort field: x"
    assert _body(response)["code"] == "unprocessable_entity"


async def test_rate_limit_exception_code() -> None:
    response = await http_exception_handler(
        MagicMock(), RateLimitException(detail="Rate limit exceeded.")
    )
    assert _body(response) == problem_body("Rate limit exceeded.", 429, "rate_limit_exceeded")


async def test_validation_error_includes_errors_list() -> None:
    exc = RequestValidationError(
        [{"type": "missing", "loc": ("body", "name"), "msg": "Field required", "input": {}}]
    )
    response = await validation_exception_handler(MagicMock(), exc)
    body = _body(response)

    assert response.status_code == 422
    assert body["code"] == "validation_error"
    assert body["detail"] == "Request validation failed."
    assert body["errors"]


async def test_unhandled_exception_does_not_leak_internals() -> None:
    with patch("src.core.exceptions.handlers.logger_api") as logger:
        response = await unhandled_exception_handler(MagicMock(), RuntimeError("secret-trace"))

    logger.exception.assert_called_once()
    body = _body(response)
    assert response.status_code == 500
    assert body == problem_body("Internal server error.", 500, "internal_error")
    assert "secret-trace" not in response.body.decode()
