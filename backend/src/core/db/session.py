# Third-Party Dependencies
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

# Local Dependencies
from src.core.config import settings
from src.core.logger import logging

# Logger instance for the current module
logger = logging.getLogger(__name__)

# Define the database URI and URL based on the application settings
DATABASE_URI = f"{settings.POSTGRES_ASYNC_URI}"
DATABASE_URL = DATABASE_URI

# Create an async database engine
async_engine = create_async_engine(DATABASE_URL, echo=False, future=True)

# Create a local session class using the async engine
local_session = sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)


# Define an async function to get the database session
async def async_get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides an async database session for use within application logic.

    This function yields a database session from the session factory and ensures
    that any errors during execution trigger a rollback to maintain database consistency.

    Note
    ----
    - Commits must be performed explicitly in the application code where necessary.

    Yields
    ------
    AsyncSession
        The database session to be used for database operations.

    Raises
    ------
    SQLAlchemyError
        If a database error occurs, the transaction is rolled back,
        and the error is logged before being re-raised.
    """

    async_session = local_session

    async with async_session() as db:
        try:
            yield db
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Database error: {e}")
            raise
