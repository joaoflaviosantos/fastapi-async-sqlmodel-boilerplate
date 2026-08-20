# Built-in Dependencies
import asyncio

# Third-Party Dependencies
from sqlmodel import select

# Local Dependencies
from src.core.db.session import AsyncSession, local_session
from src.apps.blog.posts.models import Post
from src.apps.blog.posts_tags_assoc.models import PostTagAssoc
from src.apps.blog.tags.models import Tag
from src.apps.blog.tags._management.commands.create_example_tags import SEED_TAG_NAMES
from src.apps.system.users.models import User
from src.core.config import settings


async def create_first_post(session: AsyncSession) -> None:
    test_post = {
        "title": "This is my first post",
        "text": "This is the content of my first post.",
        "media_url": "https://www.imageurl.com/first_post.jpg",
    }

    query = select(Post).where(
        Post.title == test_post["title"],
        Post.text == test_post["text"],
        Post.media_url == test_post["media_url"],
    )
    result = await session.exec(query)
    post = result.one_or_none()

    if post is None:
        query = select(User).where(User.username == settings.USER_FIRST_ADMIN_USERNAME)
        result = await session.exec(query)
        user = result.one_or_none()

        if user is None:
            raise Exception("Admin user not found")

        post = Post(
            title=test_post["title"],
            text=test_post["text"],
            media_url=test_post["media_url"],
            user_id=user.id,
        )
        session.add(post)
        await session.flush()

    tag_result = await session.exec(select(Tag).where(Tag.name == SEED_TAG_NAMES[0]))
    tag = tag_result.one_or_none()
    if tag is None:
        raise Exception(f"Seed tag '{SEED_TAG_NAMES[0]}' not found")

    assoc_result = await session.exec(
        select(PostTagAssoc).where(
            PostTagAssoc.post_id == post.id,
            PostTagAssoc.tag_id == tag.id,
        )
    )
    if assoc_result.one_or_none() is None:
        session.add(PostTagAssoc(post_id=post.id, tag_id=tag.id))

    await session.commit()


async def main() -> None:
    async with local_session() as session:
        await create_first_post(session=session)


if __name__ == "__main__":
    asyncio.run(main())
