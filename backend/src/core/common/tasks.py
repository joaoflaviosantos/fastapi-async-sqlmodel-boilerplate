# Built-in Dependencies
from datetime import datetime, timezone

# Third-Party Dependencies
from sqlalchemy import text
import redis.asyncio as aioredis

# Local Dependencies
from src.core.utils.requests import make_get_request
from src._overrides.celery.async_task import async_task
from src.core.db.session import local_session
from src.core.logger import logger_worker
from src.core.config import settings
from src.worker import app


@async_task(app, name="check_application_health", bind=True, max_retries=1)
async def check_application_health(self) -> dict:
    """
    Scheduled health check task that verifies connectivity to PostgreSQL, Redis, and API.
    Runs every 30 seconds via Celery Beat.

    Returns
    -------
    dict
        A dictionary with the health check results for each service.
    """
    health_status: dict = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "database": "unknown",
        "redis": "unknown",
        "api": "unknown",
    }

    # Check PostgreSQL connectivity
    try:
        async with local_session() as session:
            result = await session.exec(text("SELECT 1"))
            if result.scalar() == 1:
                health_status["database"] = "healthy"
                logger_worker.info("[health_check] PostgreSQL is healthy.")
            else:
                health_status["database"] = "unhealthy"
    except Exception as exc:
        health_status["database"] = "unhealthy"
        logger_worker.error(f"[health_check] PostgreSQL failed: {exc}")

    # Check Redis connectivity
    try:
        redis_client = aioredis.from_url(
            str(settings.REDIS_CACHE_URL),
            encoding="utf-8",
            decode_responses=True,
        )
        try:
            if await redis_client.ping():
                health_status["redis"] = "healthy"
                logger_worker.info("[health_check] Redis is healthy.")
            else:
                health_status["redis"] = "unhealthy"
        finally:
            await redis_client.aclose()
    except Exception as exc:
        health_status["redis"] = "unhealthy"
        logger_worker.error(f"[health_check] Redis failed: {exc}")

    # Check API connectivity
    try:
        api_url = f"{settings.API_BASE_URL}/api/v1/system/tasks/queue-health"
        response = await make_get_request(
            url=api_url,
            params={"queue_name": "default"},
            timeout=10,
        )
        # Any response from API means it's healthy
        health_status["api"] = "healthy"
        logger_worker.info(f"[health_check] API is healthy (status {response.status_code}).")
    except Exception as exc:
        health_status["api"] = "unhealthy"
        logger_worker.error(f"[health_check] API failed: {exc}")

    # Summary log
    logger_worker.info(
        f"[health_check] Summary: database={health_status['database']}, "
        f"redis={health_status['redis']}, api={health_status['api']}"
    )

    return health_status
