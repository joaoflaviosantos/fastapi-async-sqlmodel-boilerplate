from src.core.common.crud import CRUDBase
from src.apps.system.rate_limits.models import RateLimit

from src.apps.system.rate_limits.schemas import (
    RateLimitCreateInternal,
    RateLimitUpdate,
    RateLimitUpdateInternal,
    RateLimitDelete
)

CRUDRateLimit = CRUDBase[RateLimit, RateLimitCreateInternal, RateLimitUpdate, RateLimitUpdateInternal, RateLimitDelete]
crud_rate_limits = CRUDRateLimit(RateLimit)
