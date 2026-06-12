# Built-in Dependencies
from typing import Union, Dict, Any, AsyncGenerator
from contextlib import asynccontextmanager

# Third-Party Dependencies
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, APIRouter, Depends
from fastapi.openapi.utils import get_openapi
import redis.asyncio as redis
import fastapi
import anyio

# Local Dependencies
from src.core.middlewares.client_cache_middleware import ClientCacheMiddleware
from src.apps.system.users._management.commands import create_first_superuser
from src.apps.system.tiers._management.commands import create_first_tier
from src.apps.blog.posts._management.commands import create_first_post
from src.core.api.dependencies import get_current_superuser
from src.core.db.session import async_engine as engine
from src.core.utils.log import log_system_info
from src.core.utils import cache, rate_limit
from src.core.common.models import Base
from src.core.config import settings
from src.core.logger import logger_api
from src.core.config import (
    PostgresSettings,
    RedisCacheSettings,
    AppSettings,
    ClientSideCacheSettings,
    CORSSettings,
    RedisBrokerSettings,
    RedisRateLimiterSettings,
    EnvironmentOption,
    EnvironmentSettings,
)


# --------------------------------------
# -------------- LOGGING ---------------
# --------------------------------------
# Function to configure logging during startup
async def startup_logging() -> None:
    # Log system information
    log_system_info(logger=logger_api)


# Function to configure logging during shutdown
async def shutdown_logging() -> None:
    logger_api.info("API shutdown")


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
# ------------- RATE LIMIT -------------
# --------------------------------------
# Function to create Redis rate limit pool during startup
async def create_redis_rate_limit_pool() -> None:
    rate_limit.pool = redis.ConnectionPool.from_url(
        settings.REDIS_RATE_LIMIT_URL,
        encoding="utf8",
        decode_responses=True,
    )
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
# Function to create lifespan context manager for FastAPI application
@asynccontextmanager
async def lifespan_context(
    application: FastAPI,
    settings_obj: Union[
        PostgresSettings,
        RedisCacheSettings,
        AppSettings,
        ClientSideCacheSettings,
        CORSSettings,
        RedisBrokerSettings,
        RedisRateLimiterSettings,
        EnvironmentSettings,
    ],
) -> AsyncGenerator:
    """
    Manages the lifespan of the FastAPI application (startup and shutdown events).
    """
    # -------- STARTUP --------
    await startup_logging()
    await set_threadpool_tokens()

    if isinstance(settings_obj, PostgresSettings):
        await create_tables()
        await run_seed_scripts()

    if isinstance(settings_obj, RedisCacheSettings):
        await create_redis_cache_pool()

    if isinstance(settings_obj, RedisRateLimiterSettings):
        await create_redis_rate_limit_pool()

    # Yield control back to the application
    yield

    # -------- SHUTDOWN --------
    await shutdown_logging()

    if isinstance(settings_obj, RedisCacheSettings):
        await close_redis_cache_pool()

    if isinstance(settings_obj, RedisRateLimiterSettings):
        await close_redis_rate_limit_pool()


# Function to create and configure a FastAPI application
def create_application(
    router: APIRouter,
    settings: Union[
        PostgresSettings,
        RedisCacheSettings,
        AppSettings,
        ClientSideCacheSettings,
        CORSSettings,
        RedisBrokerSettings,
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
        - PostgresSettings: Adds event handlers for initializing database tables during startup.
        - RedisCacheSettings: Sets up event handlers for creating and closing a Redis cache pool.
        - ClientSideCacheSettings: Integrates middleware for client-side caching.
        - CORSSettings: Configures Cross-Origin Resource Sharing (CORS) middleware.
        - RedisBrokerSettings: Configures the Redis broker connection for Celery task queue.
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
            "version": settings.APP_VERSION,
            "license_info": {"name": settings.LICENSE_NAME},
        }
        kwargs.update(to_update)

    if isinstance(settings, EnvironmentSettings):
        # Configure documentation URLs to be None in non-production environments
        kwargs.update({"docs_url": None, "redoc_url": None, "openapi_url": None})

    # Create lifespan context manager
    async def lifespan(app: FastAPI) -> AsyncGenerator:
        async with lifespan_context(app, settings):
            yield

    # Create and configure FastAPI application with lifespan
    application = FastAPI(lifespan=lifespan, **kwargs)

    # --------------------------------------
    # -------- APPLICATION CREATED ---------
    # --------------------------------------
    application.include_router(router)

    if isinstance(settings, ClientSideCacheSettings):
        # Add middleware for client-side caching with specified max age if environment is not local (development)
        if settings.ENVIRONMENT.value != settings.ENVIRONMENT.LOCAL.value:
            application.add_middleware(ClientCacheMiddleware, max_age=settings.CLIENT_CACHE_MAX_AGE)

    if isinstance(settings, CORSSettings):
        # Add middleware for CORS (Cross-Origin Resource Sharing)
        application.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ALLOW_ORIGINS,
            allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
            allow_methods=settings.CORS_ALLOW_METHODS,
            allow_headers=settings.CORS_ALLOW_HEADERS,
            expose_headers=settings.CORS_EXPOSE_HEADERS,
            max_age=settings.CORS_MAX_AGE,
        )

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
                    description=application.description,
                    contact=application.contact,
                    version=application.version,
                    routes=application.routes,
                )

                # Add license info if it exists
                if application.license_info.get("name") is not None:
                    out.update(
                        info={**out["info"], "license": application.license_info},
                    )

                return out

            # Include custom routes for API documentation
            application.include_router(docs_router)

    return application
