from fastapi import APIRouter

from .login import router as login_router
from .logout import router as logout_router
from .users import router as users_router
from .posts import router as posts_router
from .tasks import router as tasks_router
from .tiers import router as tiers_router
from .rate_limits import router as rate_limits_router

router = APIRouter(prefix="/v1")
router.include_router(login_router)
router.include_router(logout_router)
router.include_router(users_router)
router.include_router(posts_router)
router.include_router(tasks_router)
router.include_router(tiers_router)
router.include_router(rate_limits_router)
