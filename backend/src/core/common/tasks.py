# Built-in Dependencies
from datetime import datetime, timezone

# Third-Party Dependencies
from sqlalchemy import text
import redis.asyncio as aioredis

# Local Dependencies
from src._overrides.celery.async_task import async_task
from src.core.db.session import async_engine
from src.core.logger import logger_worker
from src.core.config import settings
from src.worker import app


@async_task(app, name="check_database_and_redis_health", bind=True, max_retries=1)
async def check_database_and_redis_health(self) -> dict:
    """
    Scheduled health check task that verifies connectivity to PostgreSQL and Redis.
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
    }

    # ------------------------------------------
    # Check PostgreSQL connectivity
    # ------------------------------------------
    try:
        async with async_engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            row = result.scalar()
            if row == 1:
                health_status["database"] = "healthy"
                logger_worker.info("[health_check] ✅ PostgreSQL connection is healthy.")
            else:
                health_status["database"] = "unhealthy"
                logger_worker.warning("[health_check] ⚠️ PostgreSQL returned unexpected result.")
    except Exception as exc:
        health_status["database"] = "unhealthy"
        logger_worker.error(f"[health_check] ❌ PostgreSQL connection failed: {exc}")

    # ------------------------------------------
    # Check Redis connectivity
    # ------------------------------------------
    try:
        redis_client = aioredis.from_url(
            str(settings.REDIS_CACHE_URL),
            encoding="utf-8",
            decode_responses=True,
        )
        try:
            pong = await redis_client.ping()
            if pong:
                health_status["redis"] = "healthy"
                logger_worker.info("[health_check] ✅ Redis connection is healthy (PING → PONG).")
            else:
                health_status["redis"] = "unhealthy"
                logger_worker.warning("[health_check] ⚠️ Redis PING returned unexpected result.")
        finally:
            await redis_client.aclose()
    except Exception as exc:
        health_status["redis"] = "unhealthy"
        logger_worker.error(f"[health_check] ❌ Redis connection failed: {exc}")

    # ------------------------------------------
    # Summary log
    # ------------------------------------------
    logger_worker.info(
        f"[health_check] Summary: database={health_status['database']}, "
        f"redis={health_status['redis']} "
        f"(checked at {health_status['checked_at']})"
    )

    return health_status
