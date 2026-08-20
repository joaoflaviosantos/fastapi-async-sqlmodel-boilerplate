# Built-in Dependencies
from http import HTTPStatus
from typing import Any

PROBLEM_TYPE = "about:blank"

_STATUS_TITLES = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error",
    503: "Service Unavailable",
}

_STATUS_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    422: "unprocessable_entity",
    429: "rate_limit_exceeded",
    500: "internal_error",
    503: "service_unavailable",
}


def status_title(status_code: int) -> str:
    if status_code in _STATUS_TITLES:
        return _STATUS_TITLES[status_code]
    try:
        return HTTPStatus(status_code).phrase
    except ValueError:
        return "Error"


def code_for_status(status_code: int) -> str:
    return _STATUS_CODES.get(status_code, "error")


def problem_body(
    detail: str,
    status: int,
    code: str,
    errors: list[Any] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "type": PROBLEM_TYPE,
        "title": status_title(status),
        "status": status,
        "detail": detail,
        "code": code,
    }
    if errors is not None:
        body["errors"] = errors
    return body
