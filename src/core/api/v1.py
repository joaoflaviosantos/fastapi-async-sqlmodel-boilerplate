# External Dependencies
from fastapi_cache.decorator import cache
from datetime import datetime
from fastapi import APIRouter

# Local Dependencies
from src.apps.system.auth.routers.v1 import router as auth_router
from src.apps.system.users.routers.v1 import router as users_router
from src.apps.system.tiers.routers.v1 import router as tiers_router
from src.apps.system.rate_limits.routers.v1 import router as rate_limits_router
from src.apps.blog.posts.routers.v1 import router as posts_router
from src.apps.system.tasks.routers.v1 import router as tasks_router


api_v1_router = APIRouter(prefix="/v1")

api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(tiers_router)
api_v1_router.include_router(rate_limits_router)
api_v1_router.include_router(tasks_router)
api_v1_router.include_router(posts_router)
