# Built-in Dependencies
import asyncio

# Local Dependencies
from src._overrides.celery.async_task import async_task
from src.worker import app


@async_task(app=app, name="sample_background_task")
async def sample_background_task(name: str) -> str:
    await asyncio.sleep(30)  # Simulate a long running task
    return f"Task {name} is complete!"
