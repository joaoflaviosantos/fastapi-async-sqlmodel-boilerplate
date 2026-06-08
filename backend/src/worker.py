# Built-in Dependencies
import platform
import asyncio

# Third-Party Dependencies
from celery.signals import celeryd_init, celeryd_after_setup
from sqlalchemy.pool import NullPool
from celery import Celery

# Local Dependencies
from src.core.logger import logger_worker
from src.core.utils.log import log_system_info
from src.core.config import settings

# Conditional Dependencies (if using Linux)
if platform.system() == "Linux":
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


# ----------------------------------------
# ---------- CELERY APPLICATION ----------
# ----------------------------------------
app = Celery(
    "worker",
    broker=str(settings.REDIS_BROKER_URL),
    backend=str(settings.POSTGRES_CELERY_URI),
    include=[
        "src.apps.system.tasks",
        "src.apps.system.users.tasks",
        "src.core.common.tasks",
    ],
)

# Automatically discover tasks
app.autodiscover_tasks()

# Timezone Configuration
app.conf.timezone = "UTC"

# Concurrency Configuration
app.conf.worker_concurrency = 4

# Queue Configuration
app.conf.task_default_queue = "default"

# Retry broker connection on startup (Celery 6.0+ compatibility)
app.conf.broker_connection_retry_on_startup = True

# Database (Result Backend) Configuration
app.conf.database_engine_options = {
    "echo": False,
    "poolclass": NullPool,
    "connect_args": {
        "sslmode": "disable",
        "sslrootcert": "",
        "application_name": f"{settings.PROJECT_NAME} - celery_worker",
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
    },
}
app.conf.database_table_schemas = {
    "task": "public",
    "group": "public",
}
app.conf.database_table_names = {
    "task": "sys_task_meta",
    "group": "sys_taskset_meta",
}
# Task tracking and result settings
app.conf.task_track_started = True
app.conf.result_extended = True
app.conf.result_backend_always_retry = True
app.conf.result_expires = 24 * 3600 * 7  # 7 days


# ----------------------------------------
# ------------ CELERY BEAT ---------------
# ----------------------------------------
app.conf.beat_schedule = {
    "check-database-and-redis-health-every-30-seconds": {
        "task": "check_database_and_redis_health",
        "schedule": 30.0,
        "options": {"queue": "default"},
    },
}


# ----------------------------------------
# ------- WORKER STARTUP SIGNALS ---------
# ----------------------------------------
@celeryd_init.connect
def configure_worker(sender=None, instance=None, conf=None, options=None, **kwargs):
    logger_worker.info(f"Worker setup started: {sender}")
    log_system_info(logger=logger_worker)


@celeryd_after_setup.connect
def setup_direct_queue(sender, instance, conf, **kwargs):
    logger_worker.info(f"Worker setup complete: {sender}")
