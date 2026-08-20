# Built-in Dependencies
from datetime import datetime, timezone
from typing import Any
import asyncio

# Third-Party Dependencies
import redis.asyncio as aioredis
from sqlmodel import text
import httpx

# Local Dependencies
from src._overrides.celery.async_task import async_task
from src.core.db.session import local_session
from src.core.logger import logger_worker
from src.core.config import settings
from src.worker import app


@async_task(app=app, name="sample_background_task")
async def sample_background_task(name: str) -> str:
    await asyncio.sleep(30)  # Simulate a long running task
    return f"Task {name} is complete!"


async def _check_application_health() -> dict:
    health_status: dict = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "database": "unknown",
        "redis": "unknown",
        "api": "unknown",
        "ready": "unknown",
    }

    # Check PostgreSQL connectivity
    try:
        async with local_session() as session:
            result = await session.exec(text("SELECT 1"))  # type: ignore
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
            settings.REDIS_CACHE_URL,
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
            await redis_client.aclose()  # type: ignore
    except Exception as exc:
        health_status["redis"] = "unhealthy"
        logger_worker.error(f"[health_check] Redis failed: {exc}")

    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        # Check API liveness (`GET /health`)
        try:
            response = await client.get(f"{settings.API_BASE_URL}/health")
            response.raise_for_status()
            health_status["api"] = "healthy"
            logger_worker.info(
                f"[health_check] API liveness is healthy (status {response.status_code})."
            )
        except Exception as exc:
            health_status["api"] = "unhealthy"
            logger_worker.error(f"[health_check] API liveness failed: {exc}")

        # Check API readiness (`GET /ready`)
        try:
            response = await client.get(f"{settings.API_BASE_URL}/ready")
            response.raise_for_status()
            health_status["ready"] = "healthy"
            logger_worker.info(
                f"[health_check] API readiness is healthy (status {response.status_code})."
            )
        except Exception as exc:
            health_status["ready"] = "unhealthy"
            logger_worker.error(f"[health_check] API readiness failed: {exc}")

    # Summary log
    logger_worker.info(
        f"[health_check] Summary: database={health_status['database']}, "
        f"redis={health_status['redis']}, api={health_status['api']}, "
        f"ready={health_status['ready']}"
    )

    return health_status


@async_task(app, name="check_application_health", bind=True, max_retries=1)
async def check_application_health(self: Any) -> dict:
    """
    Scheduled health check that verifies worker connectivity to PostgreSQL and Redis,
    plus the API liveness (`GET /health`) and readiness (`GET /ready`) probes.
    Runs every 30 seconds via Celery Beat.

    Returns
    -------
    dict
        A dictionary with the health check results for each service.
    """
    return await _check_application_health()
