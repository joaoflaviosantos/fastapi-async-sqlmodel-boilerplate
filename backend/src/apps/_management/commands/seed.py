# Built-in Dependencies
import asyncio

# Local Dependencies
from src.apps.system.tiers._management.commands import create_default_tier
from src.apps.system.users._management.commands import create_system_superuser
from src.apps.system.users._management.commands import create_first_admin_user
from src.apps.blog.posts._management.commands import create_first_post
from src.apps.blog.tags._management.commands import create_example_tags


async def main() -> None:
    """Main seed script - run all seed functions."""
    print("=" * 50)
    print("Running Seed Scripts")
    print("=" * 50)

    print("\n--- Creating Default Tier ---")
    await create_default_tier.main()

    print("\n--- Creating System Superuser ---")
    await create_system_superuser.main()

    print("\n--- Creating Admin Superuser ---")
    await create_first_admin_user.main()

    print("\n--- Creating Example Tags ---")
    await create_example_tags.main()

    print("\n--- Creating First Post ---")
    await create_first_post.main()

    print("\n" + "=" * 50)
    print("Seeding Complete!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
