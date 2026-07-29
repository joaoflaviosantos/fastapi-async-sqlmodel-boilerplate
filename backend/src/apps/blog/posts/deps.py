# Built-in Dependencies
from typing import Optional, List, Tuple

# Third-Party Dependencies
from fastapi import Query

# Local Dependencies
from src.apps.blog.posts.services import PostService, post_service
from src.core.utils.api_params import parse_sort_order


async def get_post_service() -> PostService:
    return post_service


def post_filters(
    title: Optional[str] = Query(None, description="Post title"),
    text: Optional[str] = Query(None, description="Post text"),
    media_url: Optional[str] = Query(None, description="Post media URL"),
) -> dict:
    filters_dict = {
        "title": title,
        "text": text,
        "media_url": media_url,
    }

    return {key: value for key, value in filters_dict.items() if value is not None}


def post_sort_order(
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
