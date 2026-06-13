# Built-in Dependencies
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from math import ceil, floor

# Third-Party Dependencies
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

# Local Dependencies
from src.core.config import EnvironmentOption, settings
from src.core.logger import logger_postgres

# Define the database connections URI
DATABASE_URI = str(settings.POSTGRES_ASYNC_URI)
DATABASE_API_SESSION_URI = DATABASE_URI

# For 'local_session', we need to connect to the database using the standard PostgreSQL port (5432)
# instead of the PgBouncer port (6432) to ensure direct database connections for operations
# like schema modifications or administrative tasks.
DATABASE_LOCAL_SESSION_URI = DATABASE_URI.replace("6432", "5432")

# Define connection pool settings
TOTAL_DB_POOL_SIZE = settings.POSTGRES_POOL_SIZE * 0.95
WEB_CONCURRENCY = settings.WEB_CONCURRENCY

# Calculate 'POOL_SIZE_INSTANCE' and 'MAX_OVERFLOW_INSTANCE' to distribute connections among the 'WEB_CONCURRENCY' (uvicorn workers)
# 1. 'MAX_OVERFLOW_RATIO' is previously defined
# 2. 'MAX_INSTACE_CONNECTIONS' is calculated as 'TOTAL_DB_POOL_SIZE' divided by 'WEB_CONCURRENCY'
# 3. 'POOL_SIZE_INSTANCE' is calculated as (1 - MAX_OVERFLOW_RATIO) of 'MAX_INSTACE_CONNECTIONS'
# 4. 'MAX_OVERFLOW_INSTANCE' is calculated as 'MAX_OVERFLOW_RATIO' of 'MAX_INSTACE_CONNECTIONS'
MAX_OVERFLOW_RATIO = 0.3
MAX_INSTACE_CONNECTIONS = TOTAL_DB_POOL_SIZE // WEB_CONCURRENCY
POOL_SIZE_INSTANCE = max(ceil(MAX_INSTACE_CONNECTIONS * (1 - MAX_OVERFLOW_RATIO)), 10)
MAX_OVERFLOW_INSTANCE = max(floor(MAX_INSTACE_CONNECTIONS * MAX_OVERFLOW_RATIO), 5)

# Define if NullPool should be used based on environment settings (PgBouncer usage or test environment)
USE_NULL_POOL = settings.ENVIRONMENT == EnvironmentOption.TEST or settings.POSTGRES_PORT == 6432

# Create an async database engine
if USE_NULL_POOL:
    # Create an async database engine without connection pooling
    async_engine = create_async_engine(
        DATABASE_API_SESSION_URI,
        echo=False,
        poolclass=NullPool,  # Disables connection pooling
        connect_args={
            "statement_cache_size": 0,
            "command_timeout": 60,
            "timeout": 30,
            "server_settings": {
                "application_name": f"{settings.PROJECT_NAME} - api_database_connection_without_pool"
            },
        },  # Additional connection arguments
    )
else:
    # Create an async database engine with connection pooling
    async_engine = create_async_engine(
        DATABASE_API_SESSION_URI,
        echo=False,
        echo_pool=False,  # Set to 'debug' to observe pool usage
        poolclass=AsyncAdaptedQueuePool,  # SQLAlchemy's default async pool for PostgreSQL
        pool_size=POOL_SIZE_INSTANCE,  # Number of connections to maintain in the pool
        pool_timeout=15,  # Timeout for obtaining a connection from the pool
        pool_recycle=3600,  # Time (in seconds) before a connection is recycled
        max_overflow=max(
            MAX_OVERFLOW_INSTANCE, 0
        ),  # Maximum number of connections to allow beyond pool_size
        connect_args={
            "statement_cache_size": 1000,
            "command_timeout": 60,
            "timeout": 30,
            "server_settings": {
                "application_name": f"{settings.PROJECT_NAME} - api_database_connection_with_pool"
            },
        },  # Additional connection arguments
    )


# Create an async database engine for 'local_session'
async_local_session_engine = create_async_engine(
    DATABASE_LOCAL_SESSION_URI,
    future=True,
    echo=False,
    pool_pre_ping=True,
    poolclass=NullPool,
    connect_args={
        "statement_cache_size": 0,  # Disables prepared statement caching
        "command_timeout": 60,
        "timeout": 30,
        "server_settings": {
            "application_name": f"{settings.PROJECT_NAME} - local_session_database_connection_without_pool"
        },
    },
)


# Session factories bound to their respective engines
_api_session_factory = sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)
_local_session_factory = sessionmaker(bind=async_local_session_engine, class_=AsyncSession, expire_on_commit=False)  # fmt: skip


# Session for background operations (Celery tasks, scripts, etc.)
@asynccontextmanager
async def local_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides an asynchronous database session outside of FastAPI routes.

    This function creates a database session for use cases such as Celery tasks,
    seed scripts, and other background operations that don't run within the context of FastAPI routes.

    Yields
    ------
    AsyncSession
        The database session.

    Raises
    ------
    SQLAlchemyError
        If a database error occurs, the transaction is rolled back, and the error is logged before being re-raised.
    """

    db_session = None
    try:
        async with _local_session_factory() as db_session:
            yield db_session
    except SQLAlchemyError as e:
        if db_session:
            await db_session.rollback()
        logger_postgres.error(f"Database error: {e}")
        raise
    finally:
        if db_session:
            await db_session.close()


# Session dependency for FastAPI routes
async def async_get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides an asynchronous database session for FastAPI routes.

    This function generates a database session configured for use within FastAPI routes
    and other request-scoped contexts.

    Note:
    - Commits must be performed explicitly in the application code where necessary.

    Yields
    ------
    AsyncSession
        The database session.

    Raises
    ------
    SQLAlchemyError
        If a database error occurs, the transaction is rolled back, and the error is logged before being re-raised.
    """

    async with _api_session_factory() as db_session:
        try:
            yield db_session
        except SQLAlchemyError as e:
            await db_session.rollback()
            logger_postgres.error(f"Database error: {e}")
            raise
