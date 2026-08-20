# Built-in Dependencies
import asyncio

# Third-Party Dependencies
from sqlmodel import select

# Local Dependencies
from src.core.db.session import AsyncSession, local_session
from src.apps.blog.tags.models import Tag

SEED_TAG_NAMES: tuple[str, ...] = (
    "Python",
    "FastAPI",
    "SQLModel",
    "PostgreSQL",
    "Redis",
    "Celery",
    "Testing",
    "Docker",
    "Security",
    "Performance",
)


async def create_example_tags(session: AsyncSession) -> None:
    result = await session.exec(select(Tag))
    existing_names = {tag.name for tag in result.all()}
    missing_names = [name for name in SEED_TAG_NAMES if name not in existing_names]

    if not missing_names:
        return

    for name in missing_names:
        session.add(Tag(name=name))

    await session.commit()


async def main() -> None:
    async with local_session() as session:
        await create_example_tags(session=session)


if __name__ == "__main__":
    asyncio.run(main())
