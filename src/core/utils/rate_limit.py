# Built-in Dependencies
from datetime import datetime, UTC

# Third-Party Dependencies
from redis.asyncio import Redis, ConnectionPool
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import FastAPI, APIRouter

# Local Dependencies
from src.apps.system.rate_limits.schemas import sanitize_path
from src.core.logger import logging
from src.main import app

# Logger instance for the current module
logger = logging.getLogger(__name__)

# Redis connection pool and client instances
pool: ConnectionPool | None = None
client: Redis | None = None

# Function to normalize a route path, removing consultation parameters
def normalize_route_path(route_path: str) -> str:
    return route_path.split("?")[0]

# Function to verify that a path is a valid route in the FastAPI application
def is_valid_path(path: str, app: FastAPI) -> bool:
    # Obtains all application routes
    all_routes = []
    for route in app.routes:
        if isinstance(route, APIRouter):
            all_routes.extend(route.routes)
        else:
            all_routes.append(route)

    # Verifica se o caminho é uma rota válida
    return any(normalize_route_path(f"{route.path}") == normalize_route_path(path) for route in all_routes)

# Checks if a rate limit has been exceeded
async def is_rate_limited(
    db: AsyncSession,
    user_id: int,
    path: str,
    limit: int,
    period: int
) -> bool:
    if client is None:
        logger.error("Redis client is not initialized.")
        raise Exception("Redis client is not initialized.")

    # Calculate the start of the current time window
    current_timestamp = int(datetime.now(UTC).timestamp())
    window_start = current_timestamp - (current_timestamp % period)

    # Checks if the path is a valid route
    if not is_valid_path(path, app):
        logger.warning(f"Invalid route: {path}")
        return False

    # Sanitize the path for use in the key
    sanitized_path = sanitize_path(path)
    key = f"ratelimit:{user_id}:{sanitized_path}:{window_start}"

    try:
        # Increment the count for the current time window and set the expiration if it's a new window
        current_count = await client.incr(key)
        if current_count == 1:
            await client.expire(key, period)

        # Check if the current count exceeds the rate limit
        if current_count > limit:
            return True

    except Exception as e:
        logger.exception(f"Error checking rate limit for user {user_id} on path {path}: {e}")
        raise e

    return False
