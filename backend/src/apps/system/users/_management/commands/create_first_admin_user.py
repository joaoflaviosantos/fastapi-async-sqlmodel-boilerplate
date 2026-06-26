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


async def create_first_admin_user(session: AsyncSession) -> None:
    # First user/admin data
    id = settings.USER_FIRST_ADMIN_ID
    name = settings.USER_FIRST_ADMIN_NAME
    email = settings.USER_FIRST_ADMIN_EMAIL
    username = settings.USER_FIRST_ADMIN_USERNAME
    hashed_password = get_password_hash(settings.USER_FIRST_ADMIN_PASSWORD)

    # Checking if user already exists (by id OR email)
    query = select(User).where(or_(User.id == id, User.email == email))
    result = await session.exec(query)
    user = result.one_or_none()

    # Creating admin user if it doesn't exist
    if user is None:
        # Getting default tier to assign to first user/admin
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

        # Creating first user/admin
        session.add(db_user)
        await session.commit()


async def main():
    async with local_session() as session:
        await create_first_admin_user(session=session)


if __name__ == "__main__":
    asyncio.run(main())
