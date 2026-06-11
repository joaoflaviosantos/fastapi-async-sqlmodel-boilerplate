# Local Dependencies
from src.core.common.repository import RepositoryBase
from src.apps.system.users.models import User
from src.apps.system.users.schemas import (
    UserCreateInternal,
    UserUpdate,
    UserUpdateInternal,
    UserDelete,
)

# Repository operations for the 'User' model
UserRepository = RepositoryBase[
    User, UserCreateInternal, UserUpdate, UserUpdateInternal, UserDelete
]

# Create an instance of UserRepository for the 'User' model
user_repository = UserRepository(User)
