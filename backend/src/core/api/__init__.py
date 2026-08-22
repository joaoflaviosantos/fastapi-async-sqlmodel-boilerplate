# Third-Party Dependencies
from fastapi import APIRouter

# Local Dependencies
from src.apps.system.health.routers.v1 import router as health_router
from src.core.api.v1 import api_v1_router as v1_router

# Step 1: root router — the only export consumed by ``main.py``.
router = APIRouter()

# Step 2: mount probes at the app root (not under /api/v1).
router.include_router(health_router)

# Step 3: versioned REST parent under /api.
api_router = APIRouter(prefix="/api")

# Step 4: attach v1 so domain routes live at /api + /v1 → /api/v1/...
api_router.include_router(v1_router)

# Step 5: mount the versioned API on the root.
router.include_router(api_router)
