# Built-in Dependencies
from typing import Optional, List, Tuple

# Third-Party Dependencies
from fastapi import Query

# Local Dependencies
from src.apps.blog.tags.services import TagService, tag_service
from src.core.utils.api_params import parse_sort_order


async def get_tag_service() -> TagService:
    return tag_service


def tag_filters(
    name: Optional[str] = Query(None, description="Tag name"),
) -> dict:
    filters_dict = {
        "name": name,
    }

    return {key: value for key, value in filters_dict.items() if value is not None}


def tag_sort_order(
    sort_by: Optional[List[str]] = Query(None, description="Sort fields"),
) -> List[Tuple[str, str]] | None:
    allowed_sort_fields = [
        "name",
        "created_at",
        "updated_at",
    ]
    sort_order_result = parse_sort_order(
        sort_by=sort_by,
        allowed_sort_fields=allowed_sort_fields,
    )
    return sort_order_result if len(sort_order_result) > 0 else None
