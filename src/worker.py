import asyncio
import platform
from arq.connections import RedisSettings
from arq.worker import Worker
from typing import Any

from src.core.config import settings

if platform.system() == "Linux":
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


# -------- background tasks --------
async def sample_background_task(ctx: Worker, name: str) -> str:
    await asyncio.sleep(30)
    return f"Task {name} is complete!"


# -------- base functions --------
async def startup(ctx: Worker) -> None:
    print("Worker started")


async def shutdown(ctx: Worker) -> None:
    print("Worker shutdown")


# -------- class --------
class WorkerSettings:
    redis_settings = RedisSettings(
        host=settings.REDIS_QUEUE_HOST, 
        port=settings.REDIS_QUEUE_PORT,
        username=settings.REDIS_QUEUE_USERNAME,
        password=settings.REDIS_QUEUE_PASSWORD        
        )
    on_startup = startup
    on_shutdown = shutdown
    handle_signals = False
    functions = [
        sample_background_task
        ]