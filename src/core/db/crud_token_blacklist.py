# Local Dependencies
from src.core.common.schemas import TokenBlacklistCreate, TokenBlacklistUpdate
from src.core.db.token_blacklist import TokenBlacklist
from src.core.common.crud import CRUDBase

# Define a CRUD (Create, Read, Update, Delete) interface for the TokenBlacklist model
CRUDTokenBlacklist = CRUDBase[TokenBlacklist, TokenBlacklistCreate, TokenBlacklistUpdate, TokenBlacklistUpdate, None]

# Create an instance of the CRUDTokenBlacklist with the TokenBlacklist model
crud_token_blacklist = CRUDTokenBlacklist(TokenBlacklist)
