# Built-in Dependencies
from typing import Union, Dict, Any
import subprocess
import platform
import socket
import os

# Third-Party Dependencies
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi import FastAPI, APIRouter, Depends
from fastapi.openapi.utils import get_openapi
from arq.connections import RedisSettings
from arq import create_pool
import redis.asyncio as redis
import fastapi
import psutil
import anyio

# Local Dependencies
from src.core.middlewares.client_cache_middleware import ClientCacheMiddleware
from src.apps.system.users.management.commands import create_first_superuser
from src.apps.system.tiers.management.commands import create_first_tier
from src.apps.blog.posts.management.commands import create_first_post
from src.core.api.dependencies import get_current_superuser
from src.core.db.session import async_engine as engine
from src.core.utils import cache, rate_limit
from src.core.common.models import Base
from src.core.config import settings
from src.core.logger import logging
from src.core.utils import queue
from src.core.config import (
    DatabaseSettings,
    RedisCacheSettings,
    AppSettings,
    ClientSideCacheSettings,
    RedisQueueSettings,
    RedisRateLimiterSettings,
    EnvironmentOption,
    EnvironmentSettings,
)

# Logger instance for the current module
logger = logging.getLogger(__name__)

# --------------------------------------
# -------------- LOGGING ---------------
# --------------------------------------
# Function to configure logging during startup
async def startup_logging() -> None:
    # Obtain username and machine IP
    user_name = os.getenv("USER") or os.getenv("LOGNAME") or os.getenv("USERNAME")
    ip_address = socket.gethostbyname(socket.gethostname())

    try:
        # Run 'lscpu' command to get detailed CPU information
        cpu_info_process = subprocess.run(["lscpu"], capture_output=True, text=True)
        cpu_info_output = cpu_info_process.stdout

        # Extract relevant CPU information
        relevant_info = [
            "Architecture",
            "CPU op-mode(s)",
            "Model name",
            "CPU family",
            "Model",
            "Thread(s) per core",
            "Core(s) per socket",
            "Socket(s)",
            "BogoMIPS",
            "Virtualization",
        ]

        relevant_cpu_info = {
            info.strip(): line.split(":", 1)[1].strip()
            for line in cpu_info_output.splitlines()
            if (info := line.split(":", 1)[0].strip()) in relevant_info
        }

        # Log with detailed information, including relevant CPU details
        logger.info(
            f"API started on machine: system={platform.system()}, user={user_name}, IP={ip_address}, "
            f"RAM_available={psutil.virtual_memory().available / (1024 ** 3):.2f} GB, "
            f"machine_model_name='{relevant_cpu_info.get('Model name', '')}', "
            f"threads_per_core={int(relevant_cpu_info.get('Thread(s) per core', 1))}, "
            f"cores_per_socket={int(relevant_cpu_info.get('Core(s) per socket', 1))}, "
            f"sockets={int(relevant_cpu_info.get('Socket(s)', 1))}, "
            f"virtualization='{relevant_cpu_info.get('Virtualization', '')}', "
            f"CPU_cores={psutil.cpu_count(logical=False)}, CPU_speed={psutil.cpu_freq().max:.2f} MHz"
        )
    except Exception as e:
        # Log an error if there's an issue retrieving CPU information
        logger.error(f"Error getting CPU information: {e}")


# Function to configure logging during shutdown
async def shutdown_logging() -> None:
    logger.info("API shutdown")


# --------------------------------------
# -------------- DATABASE --------------
# --------------------------------------
# Function to create database tables during startup
async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def run_seed_scripts() -> None:
    # Function to run seed scripts during startup
    await create_first_tier.main()
    await create_first_superuser.main()
    await create_first_post.main()


# --------------------------------------
# --------------- CACHE ----------------
# --------------------------------------
# Function to create Redis cache pool during startup
async def create_redis_cache_pool() -> None:
    cache.pool = redis.ConnectionPool.from_url(
        settings.REDIS_CACHE_URL,
        encoding="utf8",
        decode_responses=True,
    )
    cache.client = redis.Redis.from_pool(cache.pool)  # type: ignore


# Function to close Redis cache pool during shutdown
async def close_redis_cache_pool() -> None:
    await cache.client.aclose()  # type: ignore


# --------------------------------------
# --------------- QUEUE ----------------
# --------------------------------------
# Function to create Redis queue pool during startup
async def create_redis_queue_pool() -> None:
    queue.pool = await create_pool(
        RedisSettings(
            host=settings.REDIS_QUEUE_HOST,
            port=settings.REDIS_QUEUE_PORT,
            username=settings.REDIS_QUEUE_USERNAME,
            password=settings.REDIS_QUEUE_PASSWORD,
        )
    )


# Function to close Redis queue pool during shutdown
async def close_redis_queue_pool() -> None:
    await queue.pool.aclose()  # type: ignore


# --------------------------------------
# ------------- RATE LIMIT -------------
# --------------------------------------
# Function to create Redis rate limit pool during startup
async def create_redis_rate_limit_pool() -> None:
    rate_limit.pool = redis.ConnectionPool.from_url(settings.REDIS_RATE_LIMIT_URL)
    rate_limit.client = redis.Redis.from_pool(rate_limit.pool)  # type: ignore


# Function to close Redis rate limit pool during shutdown
async def close_redis_rate_limit_pool() -> None:
    await rate_limit.client.aclose()  # type: ignore


# --------------------------------------
# ------------ APPLICATION -------------
# --------------------------------------
# Function to set thread pool tokens
async def set_threadpool_tokens(number_of_tokens: int = 100) -> None:
    # TODO: Perform tests in the future, locally and on EC2, by increasing 'number_of_tokens'.
    limiter = anyio.to_thread.current_default_thread_limiter()
    limiter.total_tokens = number_of_tokens


# --------------------------------------
# --------------- SETUP ----------------
# --------------------------------------
# Function to create and configure a FastAPI application
def create_application(
    router: APIRouter,
    settings: Union[
        DatabaseSettings,
        RedisCacheSettings,
        AppSettings,
        ClientSideCacheSettings,
        RedisQueueSettings,
        RedisRateLimiterSettings,
        EnvironmentSettings,
    ],
    **kwargs: Any,
) -> FastAPI:
    """
    Creates and configures a FastAPI application based on the provided settings.

    This function initializes a FastAPI application, then conditionally configures
    it with various settings and handlers. The specific configuration is determined
    by the type of the `settings` object provided.

    Parameters
    ----------
    router : APIRouter
        The APIRouter object that contains the routes to be included in the FastAPI application.

    settings
        An instance representing the settings for configuring the FastAPI application. It determines the configuration applied:

        - AppSettings: Configures basic app metadata like name, description, contact, and license info.
        - DatabaseSettings: Adds event handlers for initializing database tables during startup.
        - RedisCacheSettings: Sets up event handlers for creating and closing a Redis cache pool.
        - ClientSideCacheSettings: Integrates middleware for client-side caching.
        - RedisQueueSettings: Sets up event handlers for creating and closing a Redis queue pool.
        - EnvironmentSettings: Conditionally sets documentation URLs and integrates custom routes for API documentation based on environment type.

    **kwargs
        Extra keyword arguments passed directly to the FastAPI constructor.

    Returns
    ----------
    FastAPI
        A fully configured FastAPI application instance.
    """
    # --------------------------------------
    # ---- BEFORE CREATING APPLICATION -----
    # --------------------------------------
    if isinstance(settings, AppSettings):
        # Update FastAPI application metadata with AppSettings
        to_update = {
            "title": settings.PROJECT_NAME,
            "description": settings.PROJECT_DESCRIPTION,
            "contact": {
                "name": settings.CONTACT_NAME,
                "email": settings.CONTACT_EMAIL,
            },
            "license_info": {"name": settings.LICENSE_NAME},
        }
        kwargs.update(to_update)

    if isinstance(settings, EnvironmentSettings):
        # Configure documentation URLs to be None in non-production environments
        kwargs.update({"docs_url": None, "redoc_url": None, "openapi_url": None})

    # Create and configure FastAPI application
    application = FastAPI(**kwargs)

    # --------------------------------------
    # -------- APPLICATION CREATED ---------
    # --------------------------------------
    application.include_router(router)
    application.add_event_handler("startup", startup_logging)
    application.add_event_handler("shutdown", shutdown_logging)
    application.add_event_handler("startup", set_threadpool_tokens)

    if isinstance(settings, DatabaseSettings):
        # Add event handlers for database setup during startup
        application.add_event_handler("startup", create_tables)
        application.add_event_handler("startup", run_seed_scripts)

    if isinstance(settings, RedisCacheSettings):
        # Add event handlers for Redis cache pool setup and shutdown
        application.add_event_handler("startup", create_redis_cache_pool)
        application.add_event_handler("shutdown", close_redis_cache_pool)

    if isinstance(settings, ClientSideCacheSettings):
        # Add middleware for client-side caching with specified max age
        application.add_middleware(ClientCacheMiddleware, max_age=settings.CLIENT_CACHE_MAX_AGE)

    if isinstance(settings, RedisQueueSettings):
        # Add event handlers for Redis queue pool setup and shutdown
        application.add_event_handler("startup", create_redis_queue_pool)
        application.add_event_handler("shutdown", close_redis_queue_pool)

    if isinstance(settings, RedisRateLimiterSettings):
        # Add event handlers for Redis rate limiter pool setup and shutdown
        application.add_event_handler("startup", create_redis_rate_limit_pool)
        application.add_event_handler("shutdown", close_redis_rate_limit_pool)

    if isinstance(settings, EnvironmentSettings):
        if settings.ENVIRONMENT != EnvironmentOption.PRODUCTION:
            docs_router = APIRouter()
            if settings.ENVIRONMENT != EnvironmentOption.LOCAL:
                # Add dependency for accessing documentation routes only in non-local environments
                docs_router = APIRouter(dependencies=[Depends(get_current_superuser)])

            # Create custom routes for API documentation
            @docs_router.get("/docs", include_in_schema=False)
            async def get_swagger_documentation() -> fastapi.responses.HTMLResponse:
                return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")

            @docs_router.get("/redoc", include_in_schema=False)
            async def get_redoc_documentation() -> fastapi.responses.HTMLResponse:
                return get_redoc_html(openapi_url="/openapi.json", title="docs")

            @docs_router.get("/openapi.json", include_in_schema=False)
            async def openapi() -> Dict[str, Any]:
                out: dict = get_openapi(
                    title=application.title,
                    version=application.version,
                    routes=application.routes,
                )
                return out

            # Include custom routes for API documentation
            application.include_router(docs_router)

    return application
