# Local Dependencies
from src.apps.system.health.services import HealthService, health_service


async def get_health_service() -> HealthService:
    return health_service
