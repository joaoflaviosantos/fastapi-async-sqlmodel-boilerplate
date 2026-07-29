# Built-in Dependencies
from typing import Annotated, Optional, List, Tuple

# Third-Party Dependencies
from fastapi import Depends, Query, Request
from sqlmodel.ext.asyncio.session import AsyncSession

# Local Dependencies
from src.apps.auth.deps import get_optional_user
from src.apps.system.rate_limits.repositories import rate_limit_repository
from src.apps.system.rate_limits.schemas import sanitize_path
from src.apps.system.rate_limits.services import RateLimitService, rate_limit_service
from src.apps.system.tiers.repositories import tier_repository
from src.core.config import settings
from src.core.db.session import async_get_db
from src.core.exceptions.http_exceptions import RateLimitException
from src.core.logger import logger_api
from src.core.utils.api_params import parse_sort_order
from src.core.utils.rate_limit import is_rate_limited

# Default rate limit settings from configuration
DEFAULT_LIMIT = settings.DEFAULT_RATE_LIMIT_LIMIT
DEFAULT_PERIOD = settings.DEFAULT_RATE_LIMIT_PERIOD


async def get_rate_limit_service() -> RateLimitService:
    return rate_limit_service


async def rate_limiter(
    request: Request,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    user: dict | None = Depends(get_optional_user),
) -> None:
    """
    Apply Redis-backed rate limiting to a FastAPI route.

    Use this dependency in the route decorator, not as a function parameter,
    whenever the handler does not need to access any value returned by the
    limiter. Example:

    ```python
    @router.get(
        "/system/tasks/processed",
        dependencies=[Depends(rate_limiter)],
    )
    async def list_processed_tasks(...):
        ...
    ```

    The dependency identifies the caller as the authenticated user's ID when a
    valid bearer token is present; otherwise it falls back to the client IP (or
    proxy headers). For authenticated users, it first looks for a route-specific
    limit configured for the user's tier and sanitized request path. If no
    route-specific configuration exists, the default limit and period from
    settings are applied.

    Limits are stored in Redis using a fixed-window key composed from the
    caller identifier, sanitized route path, and current time window. When the
    request count exceeds the configured limit, a `RateLimitException` is
    raised and FastAPI returns HTTP 429.
    """
    # Sanitize the path from the request URL
    path = sanitize_path(request.url.path)
    if user:
        # If a user is present, retrieve user-specific rate limit settings
        user_id = user["id"]
        tier = await tier_repository.get(db=db, id=user["tier_id"])
        if tier:
            rate_limit = await rate_limit_repository.get(db=db, tier_id=tier["id"], path=path)
            if rate_limit:
                # If rate limit settings are found, use them; otherwise, apply default settings
                limit, period = rate_limit["limit"], rate_limit["period"]
            else:
                logger_api.warning(
                    f"User {user_id} with tier '{tier['name']}' has no specific rate limit for path '{path}'. Applying default rate limit."
                )
                limit, period = DEFAULT_LIMIT, DEFAULT_PERIOD
        else:
            logger_api.warning(f"User {user_id} has no assigned tier. Applying default rate limit.")
            limit, period = DEFAULT_LIMIT, DEFAULT_PERIOD
    else:
        # If no user is present, apply default rate limit settings based on the client host
        if hasattr(request, "client") and hasattr(request.client, "host"):
            # Check this issue comment if you are using Gunicorn:
            # https://github.com/tiangolo/full-stack-fastapi-postgresql/issues/224#issuecomment-1429593840
            user_id = request.client.host
        else:
            x_forwarded_for = request.headers.get("x-forwarded-for", None)
            x_real_ip = request.headers.get("x-real-ip", None)
            user_id = (
                x_forwarded_for if x_forwarded_for else (x_real_ip if x_real_ip else "Unknown")
            )

        limit, period = DEFAULT_LIMIT, DEFAULT_PERIOD

    # Check if the user is rate-limited for the given path
    is_limited = await is_rate_limited(
        app=request.app,
        db=db,
        user_id=user_id,
        path=path,
        limit=limit,
        period=period,
    )
    if is_limited:
        # Raise an exception if the user exceeds the rate limit
        raise RateLimitException(detail="Rate limit exceeded.")


def rate_limit_filters(
    name: Optional[str] = Query(None, description="Rate limit name"),
    path: Optional[str] = Query(None, description="Rate-limited API path"),
    limit: Optional[int] = Query(None, description="Request limit"),
    period: Optional[int] = Query(None, description="Rate limit period in seconds"),
) -> dict:
    filters_dict = {
        "name": name,
        "path": path,
        "limit": limit,
        "period": period,
    }

    return {key: value for key, value in filters_dict.items() if value is not None}


def rate_limit_sort_order(
    sort_by: Optional[List[str]] = Query(None, description="Sort fields"),
) -> List[Tuple[str, str]] | None:
    allowed_sort_fields = [
        "name",
        "path",
        "limit",
        "period",
        "tier_id",
    ]
    sort_order_result = parse_sort_order(
        sort_by=sort_by,
        allowed_sort_fields=allowed_sort_fields,
    )
    return sort_order_result if len(sort_order_result) > 0 else None
