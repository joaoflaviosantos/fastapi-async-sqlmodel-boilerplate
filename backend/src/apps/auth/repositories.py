# Local Dependencies
from src.apps.auth.schemas import (
    TokenBlacklistCreate,
    TokenBlacklistUpdate,
)
from src.apps.auth.models import TokenBlacklist
from src.core.common.repository import RepositoryBase

# Define a Repository interface for the TokenBlacklist model
TokenBlacklistRepository = RepositoryBase[
    TokenBlacklist,
    TokenBlacklistCreate,
    TokenBlacklistUpdate,
    TokenBlacklistUpdate,
    None,
]

# Create an instance of the TokenBlacklistRepository with the TokenBlacklist model
token_blacklist_repository = TokenBlacklistRepository(TokenBlacklist)
