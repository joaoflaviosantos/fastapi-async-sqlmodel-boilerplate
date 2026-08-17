# Built-in Dependencies
from typing import Optional, List, Tuple

# Third-Party Dependencies
from fastapi import Query

# Local Dependencies
from src.apps.example.items.services import ItemService, item_service
from src.core.utils.api_params import parse_sort_order


async def get_item_service() -> ItemService:
    return item_service


def item_filters(
    title: Optional[str] = Query(None, description="Item title"),
    text: Optional[str] = Query(None, description="Item text"),
    media_url: Optional[str] = Query(None, description="Item media URL"),
) -> dict:
    filters_dict = {
        "title": title,
        "text": text,
        "media_url": media_url,
    }

    return {key: value for key, value in filters_dict.items() if value is not None}


def item_sort_order(
    sort_by: Optional[List[str]] = Query(None, description="Sort fields"),
) -> List[Tuple[str, str]] | None:
    allowed_sort_fields = [
        "title",
        "text",
        "media_url",
        "created_at",
        "updated_at",
    ]
    sort_order_result = parse_sort_order(
        sort_by=sort_by,
        allowed_sort_fields=allowed_sort_fields,
    )
    return sort_order_result if len(sort_order_result) > 0 else None
