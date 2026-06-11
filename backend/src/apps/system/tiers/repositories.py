# Local Dependencies
from src.core.common.repository import RepositoryBase
from src.apps.system.tiers.models import Tier
from src.apps.system.tiers.schemas import (
    TierCreateInternal,
    TierUpdate,
    TierUpdateInternal,
    TierDelete,
)

# Repository operations for the 'Tier' model
TierRepository = RepositoryBase[
    Tier, TierCreateInternal, TierUpdate, TierUpdateInternal, TierDelete
]

# Create an instance of TierRepository for the 'Tier' model
tier_repository = TierRepository(Tier)
