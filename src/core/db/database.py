from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import DeclarativeBase, sessionmaker, MappedAsDataclass


from src.core.config import settings

class Base(DeclarativeBase, MappedAsDataclass):
    pass

DATABASE_URI = f"{settings.POSTGRES_ASYNC_URI}"
DATABASE_URL = DATABASE_URI

async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True
)

local_session = sessionmaker(
    bind=async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def async_get_db() -> AsyncSession:
    async_session = local_session
    
    async with async_session() as db:
        yield db
        await db.commit()
