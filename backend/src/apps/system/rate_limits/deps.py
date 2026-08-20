# Built-in Dependencies
from typing import Annotated, Optional, List, Tuple

# Third-Party Dependencies
from fastapi import Depends, Query, Request
from sqlmodel.ext.asyncio.session import AsyncSession

# Local Dependencies
from src.apps.system.auth.deps import get_optional_user
from src.apps.system.rate_limits.repositories import rate_limit_repository
from src.apps.system.rate_limits.schemas import RateLimitRead
from src.apps.system.rate_limits.services import RateLimitService, rate_limit_service
from src.apps.system.tiers.repositories import tier_repository
from src.core.config import settings
from src.core.db.session import async_get_db
from src.core.exceptions.http_exceptions import RateLimitException
from src.core.logger import logger_api
from src.core.utils.api_params import parse_sort_order
from src.core.utils.rate_limit import (
    caller_identifier,
    is_rate_limited,
    match_longest_prefix,
    request_route_template,
    sanitize_path,
)

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

    Authenticated callers are keyed by user id. Unauthenticated callers use the
    client IP, or the first ``X-Forwarded-For`` / ``X-Real-IP`` hop when
    ``TRUST_PROXY_HEADERS`` is enabled.

    Configured rules for the user's tier are matched with longest-prefix against
    the sanitized **route template** (path parameters stay as ``{param}``). If no
    rule matches, the default limit and period from settings apply.

    Limits are stored in Redis using a fixed-window key. When the request count
    exceeds the configured limit, a `RateLimitException` is raised (HTTP 429).
    """
    route_template = sanitize_path(request_route_template(request))
    redis_path = route_template
    limit, period = DEFAULT_LIMIT, DEFAULT_PERIOD

    if user:
        user_id = str(user["id"])
        tier = await tier_repository.get(db=db, id=user["tier_id"])
        if tier:
            rules = await rate_limit_repository.get_all(
                db=db, schema_to_select=RateLimitRead, tier_id=tier["id"]
            )
            matched = match_longest_prefix(route_template, list(rules))
            if matched:
                limit, period = matched["limit"], matched["period"]
                redis_path = matched["path"]
            else:
                logger_api.warning(
                    f"User {user_id} with tier '{tier['name']}' has no specific rate limit "
                    f"for path '{route_template}'. Applying default rate limit."
                )
        else:
            logger_api.warning(f"User {user_id} has no assigned tier. Applying default rate limit.")
    else:
        user_id = caller_identifier(request, settings.TRUST_PROXY_HEADERS)
        if user_id is None:
            logger_api.warning(
                "Rate limiter skipped: could not identify an unauthenticated caller."
            )
            return

    is_limited = await is_rate_limited(
        app=request.app,
        user_id=user_id,
        path=redis_path,
        limit=limit,
        period=period,
    )
    if is_limited:
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
