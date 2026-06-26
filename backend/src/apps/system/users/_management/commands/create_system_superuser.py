# Built-in Dependencies
import asyncio

# Third-Party Dependencies
from sqlmodel import select, or_

# Local Dependencies
from src.core.db.session import AsyncSession, local_session
from src.core.security import get_password_hash
from src.apps.system.users.models import User
from src.apps.system.tiers.models import Tier
from src.core.config import settings


async def create_system_superuser(session: AsyncSession) -> None:
    # System superuser data
    id = settings.USER_SYSTEM_ID
    name = settings.USER_SYSTEM_NAME
    email = settings.USER_SYSTEM_EMAIL
    username = settings.USER_SYSTEM_USERNAME
    hashed_password = get_password_hash(settings.USER_SYSTEM_PASSWORD)

    # Checking if user already exists (by id OR email)
    query = select(User).where(or_(User.id == id, User.email == email))
    result = await session.exec(query)
    user = result.one_or_none()

    # Creating system user if it doesn't exist
    if user is None:
        # Getting default tier to assign to first user/system
        query = select(Tier).where(Tier.name == settings.TIER_NAME_DEFAULT)
        result = await session.exec(query)
        tier = result.one_or_none()

        if tier is None:
            raise Exception("Default tier not found")

        # Validating user data
        # See: https://github.com/tiangolo/sqlmodel/issues/52#issuecomment-1311987732
        db_user = User.model_validate(
            {
                "id": id,
                "name": name,
                "email": email,
                "username": username,
                "hashed_password": hashed_password,
                "is_superuser": True,
                "profile_image_url": "https://www.imageurl.com/first_user.jpg",
                "tier_id": tier.id,
            }
        )

        # Creating system superuser
        session.add(db_user)
        await session.commit()


async def main():
    async with local_session() as session:
        await create_system_superuser(session=session)


if __name__ == "__main__":
    asyncio.run(main())
