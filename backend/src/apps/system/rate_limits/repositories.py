# Local Dependencies
from src.core.common.repository import RepositoryBase
from src.apps.system.rate_limits.models import RateLimit
from src.apps.system.rate_limits.schemas import (
    RateLimitCreateInternal,
    RateLimitUpdate,
    RateLimitUpdateInternal,
    RateLimitDelete,
)

# Repository operations for RateLimit model
RateLimitRepository = RepositoryBase[
    RateLimit,
    RateLimitCreateInternal,
    RateLimitUpdate,
    RateLimitUpdateInternal,
    RateLimitDelete,
]

# Create an instance of RateLimitRepository for the 'RateLimit' model
rate_limit_repository = RateLimitRepository(RateLimit)
