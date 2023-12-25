from src.core.common.crud import CRUDBase
from src.apps.system.users.models import User
from src.apps.system.users.schemas import UserCreateInternal, UserUpdate, UserUpdateInternal, UserDelete

CRUDUser = CRUDBase[User, UserCreateInternal, UserUpdate, UserUpdateInternal, UserDelete]
crud_users = CRUDUser(User)
