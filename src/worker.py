# Built-in Dependencies
import asyncio
import platform

# Third-Party Dependencies
from arq.connections import RedisSettings
from arq.worker import Worker

# Local Dependencies
from src.core.config import settings

# Conditional Dependencies
if platform.system() == "Linux":
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# Worker Functions
# --------------------------------------
# ---------- BACKGROUND TASKS ----------
# --------------------------------------
async def sample_background_task(ctx: Worker, name: str) -> str:
    await asyncio.sleep(30)
    return f"Task {name} is complete!"


# --------------------------------------
# ----------- BASE FUNCTION ------------
# --------------------------------------
async def startup(ctx: Worker) -> None:
    print("Worker started")

async def shutdown(ctx: Worker) -> None:
    print("Worker shutdown")


# Worker Class Configuration
# --------------------------------------
# --------------- CLASS ----------------
# --------------------------------------
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
