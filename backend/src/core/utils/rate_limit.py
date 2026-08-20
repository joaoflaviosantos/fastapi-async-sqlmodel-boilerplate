# Built-in Dependencies
from datetime import datetime, UTC
from typing import Any

# Third-Party Dependencies
from redis.asyncio import Redis, ConnectionPool
from fastapi import FastAPI, Request

# Local Dependencies
from src.core.exceptions.cache_exceptions import MissingClientError
from src.core.logger import logger_redis, logger_api

# Redis connection pool and client instances
pool: ConnectionPool | None = None
client: Redis | None = None


def normalize_route_path(route_path: str) -> str:
    """
    Normalize a route path by removing any query parameters.

    Args:
        route_path (str): The route path to be normalized.

    Returns:
        str: The normalized route path.

    Example:
        >>> normalize_route_path("/users?name=john")
        "/users"
    """
    return route_path.split("?")[0]


def sanitize_path(path: str) -> str:
    """
    Sanitizes a given path by normalizing it and replacing any forward slashes with underscores.

    Parameters:
        path (str): The path to be sanitized.

    Returns:
        str: The sanitized path.
    """
    normalized_path = normalize_route_path(path)
    return normalized_path.strip("/").replace("/", "_")


def _join_route_paths(prefix: str, route_path: str) -> str:
    if not prefix:
        return route_path
    if not route_path or route_path == "/":
        return prefix
    return f"/{prefix.strip('/')}/{route_path.strip('/')}".replace("//", "/")


def request_route_template(request: Request) -> str:
    """
    Return the matched FastAPI route template, including parent router prefixes.

    FastAPI 0.141+ keeps included routers as ``_IncludedRouter`` wrappers, so
    ``scope["route"].path`` is often the inner path (``/system/tasks/{task_id}``)
    while the URL still has ``/api/v1``. Prefixes are recovered from the URL
    by substituting ``path_params`` into that inner template.

    Path parameters stay as ``{param}`` so one endpoint shares a single bucket.
    """
    url_path = request.url.path
    route = request.scope.get("route")
    template = getattr(route, "path", None)
    if not isinstance(template, str) or not template:
        return url_path

    instantiated = template
    path_params = request.path_params
    if isinstance(path_params, dict):
        for name, value in path_params.items():
            instantiated = instantiated.replace("{" + str(name) + "}", str(value), 1)

    if url_path == instantiated:
        return template

    if instantiated != "/" and url_path.endswith(instantiated):
        prefix = url_path[: -len(instantiated)]
        return _join_route_paths(prefix, template)

    return url_path


def is_path_prefix_match(route_template: str, rule_path: str) -> bool:
    """True if a sanitized rule covers this sanitized route template (exact or grouping prefix)."""
    return route_template == rule_path or route_template.startswith(rule_path + "_")


def match_longest_prefix(route_template: str, rules: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Pick the most specific matching rule (longest sanitized path wins)."""
    matched: dict[str, Any] | None = None
    for rule in rules:
        rule_path = rule.get("path")
        if not isinstance(rule_path, str):
            continue
        if not is_path_prefix_match(route_template, rule_path):
            continue
        if matched is None or len(rule_path) > len(str(matched["path"])):
            matched = rule
    return matched


def collect_route_paths(routes: list[Any], prefix: str = "") -> list[str]:
    route_paths: list[str] = []
    for route in routes:
        original_router = getattr(route, "original_router", None)
        if original_router is not None:
            router_prefix = getattr(original_router, "prefix", None) or ""
            nested_prefix = _join_route_paths(prefix, router_prefix) if router_prefix else prefix
            route_paths.extend(collect_route_paths(list(original_router.routes), nested_prefix))
            continue

        route_path = getattr(route, "path", None)
        if route_path is not None:
            route_paths.append(_join_route_paths(prefix, route_path) if prefix else route_path)

        nested_routes = getattr(route, "routes", None)
        if nested_routes:
            nested_prefix = prefix
            router_prefix = getattr(route, "prefix", None)
            if router_prefix:
                nested_prefix = (
                    _join_route_paths(prefix, router_prefix) if prefix else router_prefix
                )
            route_paths.extend(collect_route_paths(list(nested_routes), nested_prefix))

    return route_paths


def is_valid_path(path: str, app: FastAPI) -> bool:
    """
    Checks if a given path is a valid route in the FastAPI application.

    The path parameter can be either:
    - A non-sanitized path: "/api/v1/system/tasks"
    - A sanitized path: "api_v1_system_tasks"

    Prefix matches are allowed so one rule can group endpoints under the same path.
    """
    all_routes_sanitized = [
        sanitize_path(route_path) for route_path in collect_route_paths(app.routes)
    ]

    if path.startswith("/"):
        path_to_check = sanitize_path(path)
    else:
        path_to_check = path

    for sanitized_route in all_routes_sanitized:
        if path_to_check == sanitized_route or sanitized_route.startswith(path_to_check + "_"):
            return True

    return False


def caller_identifier(request: Request, trust_proxy_headers: bool) -> str | None:
    """
    Identify an unauthenticated caller.

    When ``trust_proxy_headers`` is True (Compose/Caddy/PaaS), use the first
    ``X-Forwarded-For`` hop or ``X-Real-IP``. Otherwise use ``request.client.host``.
    """
    if trust_proxy_headers:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            first_hop = forwarded_for.split(",")[0].strip()
            if first_hop:
                return first_hop
        real_ip = request.headers.get("x-real-ip")
        if real_ip and real_ip.strip():
            return real_ip.strip()

    client = request.client
    if client is not None and client.host:
        return client.host
    return None


async def is_rate_limited(
    app: FastAPI,
    user_id: int | str,
    path: str,
    limit: int,
    period: int,
) -> bool:
    """
    Check if the user with the given ID is rate limited for the specified path.

    ``path`` is a sanitized route template or a matching rule path used as the Redis key.
    """
    if client is None:
        logger_redis.error("Redis client is not initialized.")
        raise MissingClientError("Redis client is not initialized.")

    if period < 1:
        raise ValueError("Rate limit period must be at least 1 second")

    current_timestamp = int(datetime.now(UTC).timestamp())
    window_start = current_timestamp - (current_timestamp % period)

    user_id = str(user_id)

    if not is_valid_path(path=path, app=app):
        logger_api.warning(f"Rate limit check for user_id '{user_id}' on invalid route '{path}'")
        return False

    sanitized_path = sanitize_path(path) if path.startswith("/") else path
    key = f"ratelimit:{user_id}:{sanitized_path}:{window_start}"

    try:
        pipe = client.pipeline()
        pipe.incr(key)
        pipe.expire(key, period, nx=True)
        incr_result, _expire_result = await pipe.execute()
        current_count = int(incr_result)
        return current_count > limit
    except Exception as e:
        logger_redis.exception(f"Error checking rate limit for user {user_id} on path {path}: {e}")
        raise
