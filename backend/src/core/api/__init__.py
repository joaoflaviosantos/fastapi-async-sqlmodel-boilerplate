# Third-Party Dependencies
from fastapi import APIRouter

# Local Dependencies
from src.apps.system.health.routers.v1 import router as health_router
from src.core.api.v1 import api_v1_router as v1_router

router = APIRouter()

api_router = APIRouter(prefix="/api")
api_router.include_router(v1_router)

router.include_router(health_router)
router.include_router(api_router)
