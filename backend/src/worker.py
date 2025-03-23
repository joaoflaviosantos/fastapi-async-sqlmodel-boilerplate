# Built-in Dependencies
import platform
import asyncio

# Third-Party Dependencies
from arq.connections import RedisSettings
from arq.worker import Worker

# Local Dependencies
from src.core.logger import logger_worker
from src.core.config import settings
from src.core.utils.log import log_system_info

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
    logger_worker.info(f"Task {name} is complete!")
    return f"Task {name} is complete!"


# --------------------------------------
# ----------- BASE FUNCTION ------------
# --------------------------------------
async def startup(ctx: Worker) -> None:
    # Log system information
    log_system_info(logger=logger_worker)


async def shutdown(ctx: Worker) -> None:
    logger_worker.info("Worker shutdown")


# Worker Class Configuration
# --------------------------------------
# --------------- CLASS ----------------
# --------------------------------------
class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(
        dsn=settings.REDIS_QUEUE_URL,
    )
    on_startup = startup
    on_shutdown = shutdown
    handle_signals = False
    functions = [sample_background_task]
