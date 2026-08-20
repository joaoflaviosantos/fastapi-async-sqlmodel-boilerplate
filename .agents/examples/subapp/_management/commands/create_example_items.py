# Built-in Dependencies
import asyncio

# Third-Party Dependencies
from sqlmodel import select

# Local Dependencies
from src.core.db.session import AsyncSession, local_session
from src.apps.example.items.models import Item
from src.core.config import settings

# Identity is title. One SELECT of titles, then add missing — do not one_or_none() in a loop.
SEED_ITEMS: tuple[dict[str, str], ...] = (
    {
        "title": "Getting started with FastAPI",
        "text": "A short introduction to the async API stack.",
        "media_url": "https://www.imageurl.com/getting_started.jpg",
    },
    {
        "title": "SQLModel tables",
        "text": "How table=True models map to PostgreSQL.",
        "media_url": "https://www.imageurl.com/sqlmodel_tables.jpg",
    },
    {
        "title": "Async sessions",
        "text": "Use local_session() in seeds and Celery, not async_get_db.",
        "media_url": "https://www.imageurl.com/async_sessions.jpg",
    },
    {
        "title": "Redis cache",
        "text": "Item and list keys, SCAN invalidation, fail-open reads.",
        "media_url": "https://www.imageurl.com/redis_cache.jpg",
    },
    {
        "title": "Celery workers",
        "text": "Background jobs off the request path with local_session().",
        "media_url": "https://www.imageurl.com/celery_workers.jpg",
    },
    {
        "title": "Alembic revisions",
        "text": "Import table=True models in core/db before autogenerate.",
        "media_url": "https://www.imageurl.com/alembic_revisions.jpg",
    },
    {
        "title": "Pytest layout",
        "text": "HTTP tests in test_v1.py; service unit tests next to the subapp.",
        "media_url": "https://www.imageurl.com/pytest_layout.jpg",
    },
    {
        "title": "Locust TaskSets",
        "text": "Load tests live under locust/, not in the backend pytest suite.",
        "media_url": "https://www.imageurl.com/locust_tasksets.jpg",
    },
    {
        "title": "Rate limits",
        "text": "Opt-in Depends(rate_limiter) with longest-prefix matching.",
        "media_url": "https://www.imageurl.com/rate_limits.jpg",
    },
    {
        "title": "OpenAPI tags",
        "text": "Put the app prefix on each path, not on the subapp APIRouter.",
        "media_url": "https://www.imageurl.com/openapi_tags.jpg",
    },
)


async def create_example_items(session: AsyncSession) -> None:
    result = await session.exec(select(Item.title))
    existing_titles = set(result.all())
    missing = [item for item in SEED_ITEMS if item["title"] not in existing_titles]

    if not missing:
        return

    for item in missing:
        session.add(
            Item(
                title=item["title"],
                text=item["text"],
                media_url=item["media_url"],
                created_by_user_id=settings.USER_SYSTEM_ID,
                updated_by_user_id=settings.USER_SYSTEM_ID,
            )
        )

    await session.commit()


async def main() -> None:
    async with local_session() as session:
        await create_example_items(session=session)


if __name__ == "__main__":
    asyncio.run(main())
