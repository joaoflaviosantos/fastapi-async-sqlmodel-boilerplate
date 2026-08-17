# Built-in Dependencies
import asyncio

# Third-Party Dependencies
from sqlmodel import select

# Local Dependencies
from src.core.db.session import AsyncSession, local_session
from src.apps.example.items.models import Item
from src.apps.system.users.models import User
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
        query = select(User).where(User.username == settings.USER_FIRST_ADMIN_USERNAME)
        result = await session.exec(query)
        user = result.one_or_none()

        if user is None:
            raise Exception("Admin user not found")

        session.add(
            Item(
                title=test_item["title"],
                text=test_item["text"],
                media_url=test_item["media_url"],
                user_id=user.id,
            )
        )

        await session.commit()


async def main():
    async with local_session() as session:
        await create_first_item(session=session)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
