# Built-in Dependencies
from datetime import datetime, UTC
import asyncio
import uuid

# Third-Party Dependencies
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import (
    select, 
    Table, 
    MetaData, 
    Column, 
    Integer, 
    String, 
    insert, 
    ForeignKey, 
    DateTime, 
    Boolean
)

# Local Dependencies
from src.core.db.session import AsyncSession, local_session
from src.core.db.session import async_engine
from src.core.security import get_password_hash
from src.apps.system.users.models import User
from src.core.config import settings


async def create_first_user(session: AsyncSession) -> None:
    name = settings.ADMIN_NAME
    email = settings.ADMIN_EMAIL
    username = settings.ADMIN_USERNAME
    hashed_password = get_password_hash(settings.ADMIN_PASSWORD)

    query = select(User).filter_by(email=email)
    result = await session.execute(query)
    user = result.scalar_one_or_none()
    
    if user is None:
        metadata = MetaData()
        user_table = Table(
            "user", metadata,
            Column("id", Integer, primary_key=True, autoincrement=True, nullable=False),
            Column("name", String(30), nullable=False),
            Column("username", String(20), nullable=False, unique=True, index=True),
            Column("email", String(50), nullable=False, unique=True, index=True),
            Column("hashed_password", String, nullable=False),
            Column("profile_image_url", String, default="https://www.imageurl.com/first_user.jpg"),
            Column("uuid", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True),
            Column("created_at", DateTime(timezone=True), default=lambda:  datetime.now(UTC), nullable=False),
            Column("updated_at", DateTime),
            Column("deleted_at", DateTime),
            Column("is_deleted", Boolean, default=False, index=True),
            Column("is_superuser", Boolean, default=False),
            Column("tier_id", Integer, ForeignKey("tier.id"), index=True)
        )

        data = {
            'name': name,
            'email': email,
            'username': username,
            'hashed_password': hashed_password,
            'is_superuser': True
        }

        stmt = insert(user_table).values(data)
        async with async_engine.connect() as conn:
            await conn.execute(stmt)
            await conn.commit()

async def main():
    async with local_session() as session:
        await create_first_user(session)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
