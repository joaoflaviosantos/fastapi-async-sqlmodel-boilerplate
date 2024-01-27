# Built-in Dependencies
import subprocess
import platform
import asyncio
import socket
import os

# Third-Party Dependencies
from arq.connections import RedisSettings
from arq.worker import Worker
import psutil

# Local Dependencies
from src.core.logger import logging, configure_logging
from src.core.config import settings

# Configure logging for the worker
configure_logging(log_file="worker")

# Logger instance for the current module
logger = logging.getLogger(__name__)

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
    # Obtain username and machine IP
    user_name = os.getenv("USER") or os.getenv("LOGNAME") or os.getenv("USERNAME")
    ip_address = socket.gethostbyname(socket.gethostname())

    try:
        # Run 'lscpu' command to get detailed CPU information
        cpu_info_process = subprocess.run(["lscpu"], capture_output=True, text=True)
        cpu_info_output = cpu_info_process.stdout

        # Extract relevant CPU information
        relevant_info = [
            "Architecture",
            "CPU op-mode(s)",
            "Model name",
            "CPU family",
            "Model",
            "Thread(s) per core",
            "Core(s) per socket",
            "Socket(s)",
            "BogoMIPS",
            "Virtualization",
        ]

        relevant_cpu_info = {
            info.strip(): line.split(":", 1)[1].strip()
            for line in cpu_info_output.splitlines()
            if (info := line.split(":", 1)[0].strip()) in relevant_info
        }

        # Log with detailed information, including relevant CPU details
        logger.info(
            f"Worker started on machine: system={platform.system()}, user={user_name}, IP={ip_address}, "
            f"RAM_available={psutil.virtual_memory().available / (1024 ** 3):.2f} GB, "
            f"machine_model_name='{relevant_cpu_info.get('Model name', '')}', "
            f"threads_per_core={int(relevant_cpu_info.get('Thread(s) per core', 1))}, "
            f"cores_per_socket={int(relevant_cpu_info.get('Core(s) per socket', 1))}, "
            f"sockets={int(relevant_cpu_info.get('Socket(s)', 1))}, "
            f"virtualization='{relevant_cpu_info.get('Virtualization', '')}', "
            f"CPU_cores={psutil.cpu_count(logical=False)}, CPU_speed={psutil.cpu_freq().max:.2f} MHz"
        )
    except Exception as e:
        # Log an error if there's an issue retrieving CPU information
        logger.error(f"Error getting CPU information: {e}")


async def shutdown(ctx: Worker) -> None:
    logger.info("Worker shutdown")


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
