# Built-in Dependencies
from typing import Annotated

# Third-Party Dependencies
from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

# Local Dependencies
from src.apps.system.health.deps import get_health_service
from src.apps.system.health.schemas import HealthRead, ReadyRead
from src.apps.system.health.services import HealthService
from src.core.db.session import async_get_db

router = APIRouter(tags=["System - Health"])


@router.get("/health", response_model=HealthRead)
async def read_liveness(
    health_service: HealthService = Depends(get_health_service),
) -> HealthRead:
    return await health_service.liveness()


@router.get("/ready", response_model=ReadyRead)
async def read_readiness(
    db: Annotated[AsyncSession, Depends(async_get_db)],
    health_service: HealthService = Depends(get_health_service),
) -> ReadyRead:
    return await health_service.readiness(db=db)
