from src.core.common.crud import CRUDBase
from src.core.db.token_blacklist import TokenBlacklist
from src.core.common.schemas import TokenBlacklistCreate, TokenBlacklistUpdate

CRUDTokenBlacklist = CRUDBase[TokenBlacklist, TokenBlacklistCreate, TokenBlacklistUpdate, TokenBlacklistUpdate, None]
crud_token_blacklist = CRUDTokenBlacklist(TokenBlacklist)
