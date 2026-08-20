# Built-in Dependencies
from typing import Any

# Third-Party Dependencies
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# Local Dependencies
from src.core.exceptions.http_exceptions import CustomException
from src.core.exceptions.problem import code_for_status, problem_body, status_title
from src.core.logger import logger_api


class ProblemJSONResponse(JSONResponse):
    media_type = "application/problem+json"


def _detail_as_str(detail: Any, status_code: int) -> str:
    if isinstance(detail, str) and detail:
        return detail
    if isinstance(detail, list) and detail:
        first = detail[0]
        if isinstance(first, dict) and first.get("msg"):
            return str(first["msg"])
        return str(detail)
    if detail:
        return str(detail)
    return status_title(status_code)


def _problem_response(
    *,
    status_code: int,
    detail: str,
    code: str,
    headers: dict[str, str] | None = None,
    errors: list[Any] | None = None,
) -> ProblemJSONResponse:
    return ProblemJSONResponse(
        status_code=status_code,
        content=problem_body(detail, status_code, code, errors=errors),
        headers=headers,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    status_code = exc.status_code
    code = getattr(exc, "code", None) or code_for_status(status_code)
    headers = getattr(exc, "headers", None)
    return _problem_response(
        status_code=status_code,
        detail=_detail_as_str(exc.detail, status_code),
        code=code,
        headers=headers,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return _problem_response(
        status_code=422,
        detail="Request validation failed.",
        code="validation_error",
        errors=jsonable_encoder(exc.errors()),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger_api.exception("Unhandled exception.")
    return _problem_response(
        status_code=500,
        detail="Internal server error.",
        code="internal_error",
    )


def register_exception_handlers(application: FastAPI) -> None:
    application.add_exception_handler(CustomException, http_exception_handler)
    application.add_exception_handler(StarletteHTTPException, http_exception_handler)
    application.add_exception_handler(RequestValidationError, validation_exception_handler)
    application.add_exception_handler(Exception, unhandled_exception_handler)
