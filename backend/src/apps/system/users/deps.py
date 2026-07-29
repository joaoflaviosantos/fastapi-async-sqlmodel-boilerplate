# Built-in Dependencies
from typing import Optional, List, Tuple
from uuid import UUID

# Third-Party Dependencies
from fastapi import Query

# Local Dependencies
from src.apps.system.users.services import UserService, user_service
from src.core.utils.api_params import parse_sort_order


async def get_user_service() -> UserService:
    return user_service


def user_filters(
    name: Optional[str] = Query(None, description="User name"),
    username: Optional[str] = Query(None, description="Username"),
    email: Optional[str] = Query(None, description="User email"),
    tier_id: Optional[UUID] = Query(None, description="User tier ID"),
    is_active: Optional[bool] = Query(None, description="Whether the user is active"),
    is_superuser: Optional[bool] = Query(None, description="Whether the user is a superuser"),
) -> dict:
    filters_dict = {
        "name": name,
        "username": username,
        "email": email,
        "tier_id": tier_id,
        "is_active": is_active,
        "is_superuser": is_superuser,
    }

    return {key: value for key, value in filters_dict.items() if value is not None}


def user_sort_order(
    sort_by: Optional[List[str]] = Query(None, description="Sort fields"),
) -> List[Tuple[str, str]] | None:
    allowed_sort_fields = [
        "name",
        "username",
        "email",
        "profile_image_url",
        "tier_id",
    ]
    sort_order_result = parse_sort_order(
        sort_by=sort_by,
        allowed_sort_fields=allowed_sort_fields,
    )
    return sort_order_result if len(sort_order_result) > 0 else None
