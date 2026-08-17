# Built-in Dependencies
from uuid import UUID

# Third-Party Dependencies
from sqlmodel import select

# Local Dependencies
from src._overrides.celery.async_task import async_task
from src.apps.example.items.models import Item
from src.core.db.session import local_session
from src.core.logger import logger_worker
from src.worker import app

# Template only: copy with the subapp if you need background work, then add
# "src.apps.<app>.<subapp>.tasks" to include=[...] in backend/src/worker.py.
# Do not register this .agents/ path on the worker.


@async_task(app, name="notify_item_created", bind=True, max_retries=3)
async def notify_item_created(self, item_id: UUID) -> dict:
    logger_worker.info(f"[notify_item_created] Starting for item {item_id}")

    try:
        async with local_session() as session:
            result = await session.exec(select(Item).where(Item.id == item_id))
            item = result.first()

            if item is None:
                logger_worker.warning(f"[notify_item_created] Item {item_id} not found")
                return {"status": "skipped", "item_id": str(item_id)}

            logger_worker.info(
                f"[notify_item_created] Item {item_id} title={item.title!r}"
            )
            return {"status": "success", "item_id": str(item_id)}

    except Exception as exc:
        logger_worker.error(f"[notify_item_created] Failed for item {item_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)
