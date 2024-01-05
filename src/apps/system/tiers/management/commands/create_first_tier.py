# Built-in Dependencies
import asyncio

# Third-Party Dependencies
from sqlalchemy import select

# Local Dependencies
from src.core.db.session import AsyncSession, local_session
from src.apps.system.tiers.models import Tier
from src.core.config import settings

async def create_first_tier(session: AsyncSession) -> None:
    tier_name = settings.TIER_NAME
    
    query = select(Tier).where(Tier.name == tier_name)
    result = await session.execute(query)
    tier = result.scalar_one_or_none()
    
    if tier is None:
        session.add(
            Tier(name=tier_name)
        )
        
        await session.commit()


async def main():
    async with local_session() as session:
        await create_first_tier(session)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
