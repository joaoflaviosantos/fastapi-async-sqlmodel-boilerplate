# Built-in Dependencies
import asyncio

# Third-Party Dependencies
from sqlmodel import select

# Local Dependencies
from src.core.db.session import AsyncSession, local_session
from src.apps.example.items.models import Item
from src.core.config import settings


async def create_first_item(session: AsyncSession) -> None:
    test_item = {
        "title": "This is my first item",
        "text": "This is the content of my first item.",
        "media_url": "https://www.imageurl.com/first_item.jpg",
    }

    query = select(Item).where(
        Item.title == test_item["title"],
        Item.text == test_item["text"],
        Item.media_url == test_item["media_url"],
    )
    result = await session.exec(query)
    item = result.one_or_none()

    if item is None:
        session.add(
            Item(
                title=test_item["title"],
                text=test_item["text"],
                media_url=test_item["media_url"],
                # System actor for seeds/jobs, not a human admin.
                created_by_user_id=settings.USER_SYSTEM_ID,
                updated_by_user_id=settings.USER_SYSTEM_ID,
            )
        )

        await session.commit()


async def main():
    async with local_session() as session:
        await create_first_item(session=session)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
