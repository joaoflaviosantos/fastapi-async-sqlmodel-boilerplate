from src.core.common.crud import CRUDBase
from src.apps.system.tiers.models import Tier
from src.apps.system.tiers.schemas import (
    TierCreateInternal, 
    TierUpdate, 
    TierUpdateInternal, 
    TierDelete)

CRUDTier = CRUDBase[Tier, TierCreateInternal, TierUpdate, TierUpdateInternal, TierDelete]
crud_tiers = CRUDTier(Tier)
