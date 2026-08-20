# Third-Party Dependencies
from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession

# Local Dependencies
from src.apps.system.health.schemas import HealthRead, ReadyRead
from src.core.exceptions.http_exceptions import ServiceUnavailableException
from src.core.logger import logger_api
from src.core.utils import cache


class HealthService:
    async def liveness(self) -> HealthRead:
        return HealthRead(status="ok")

    async def readiness(self, db: AsyncSession) -> ReadyRead:
        database_ok = await self._database_is_ready(db)
        redis_ok = await self._redis_is_ready()
        if not database_ok or not redis_ok:
            raise ServiceUnavailableException(detail="Service unavailable.")

        return ReadyRead(status="ok", database="ok", redis="ok")

    async def _database_is_ready(self, db: AsyncSession) -> bool:
        try:
            result = await db.exec(text("SELECT 1"))  # type: ignore[arg-type]
            result.one()
            return True
        except Exception:
            logger_api.warning("Readiness probe: database check failed.")
            return False

    async def _redis_is_ready(self) -> bool:
        if cache.client is None:
            logger_api.warning("Readiness probe: Redis client is not initialized.")
            return False
        try:
            await cache.client.ping()
            return True
        except Exception:
            logger_api.warning("Readiness probe: Redis check failed.")
            return False


health_service = HealthService()
