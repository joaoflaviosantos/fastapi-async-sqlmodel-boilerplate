# Third-Party Dependencies
import pytest
from fastapi import HTTPException

# Local Dependencies
from src.core.utils.api_params import compute_offset, paginated_response, parse_sort_order

pytestmark = pytest.mark.unit


def test_compute_offset_first_page() -> None:
    assert compute_offset(1, 10) == 0


def test_compute_offset_later_page() -> None:
    assert compute_offset(3, 10) == 20


def test_paginated_response_has_more() -> None:
    payload = paginated_response(
        data={"data": [1, 2], "total_count": 25},
        page=1,
        items_per_page=10,
    )
    assert payload["has_more"] is True
    assert payload["total_count"] == 25
    assert payload["page"] == 1
    assert payload["items_per_page"] == 10
    assert payload["data"] == [1, 2]


def test_paginated_response_last_page() -> None:
    payload = paginated_response(
        data={"data": [21, 22], "total_count": 22},
        page=3,
        items_per_page=10,
    )
    assert payload["has_more"] is False


def test_parse_sort_order_accepts_allowed_fields() -> None:
    assert parse_sort_order(
        sort_by=["name", "-created_at"],
        allowed_sort_fields=["name", "created_at"],
    ) == [("name", "asc"), ("created_at", "desc")]


def test_parse_sort_order_rejects_invalid_field() -> None:
    with pytest.raises(HTTPException) as exc_info:
        parse_sort_order(sort_by=["unknown"], allowed_sort_fields=["name"])

    assert exc_info.value.status_code == 422
