# Built-in Dependencies
from typing import Optional, List, Tuple

# Third-Party Dependencies
from fastapi import HTTPException, Query


def parse_sort_order(
    sort_by: Optional[List[str]] = Query(None, description="Sort fields"),
    allowed_sort_fields: Optional[List[str]] = None,
) -> List[Tuple[str, str]]:
    """
    Parse sorting fields from query parameters, ensuring only valid fields are sorted.
    Each field can be prefixed with '-' to indicate descending order.
    """
    if allowed_sort_fields is None:
        allowed_sort_fields = []

    sort_fields = []

    if sort_by:
        for field in sort_by:
            # Detect ascending/descending order
            if field.startswith("-"):
                field_name = field[1:]
                direction = "desc"
            else:
                field_name = field
                direction = "asc"

            # Validate if the field is in allowed fields
            if field_name not in allowed_sort_fields:
                raise HTTPException(
                    status_code=422,
                    detail=[
                        {
                            "loc": ["query", "sort_by"],
                            "msg": f"Invalid sort field: {field_name}. Allowed fields are: {', '.join(allowed_sort_fields)}",
                            "type": "value_error.sort_field",
                        }
                    ],
                )

            # Append valid field with direction
            sort_fields.append((field_name, direction))

    return sort_fields


def paginated_response(data: dict, page: int, items_per_page: int) -> dict:
    """
    Create a paginated response based on the provided data and pagination parameters.

    Parameters
    ----------
    data : dict
        Data to be paginated, including the list of items and total count.
    page : int
        Current page number.
    items_per_page : int
        Number of items per page.

    Returns
    ----------
    dict
        A structured paginated response dict containing the list of items, total count, pagination flags, and numbers.
    """
    return {
        "data": data["data"],
        "total_count": data["total_count"],
        "has_more": (page * items_per_page) < data["total_count"],
        "page": page,
        "items_per_page": items_per_page,
    }


# Function to calculate the offset
def compute_offset(page: int, items_per_page: int) -> int:
    """
    Calculate the offset for pagination based on the given page number and items per page.

    The offset represents the starting point in a dataset for the items on a given page.
    For example, if each page displays 10 items and you want to display page 3, the offset will be 20,
    meaning the display should start with the 21st item.

    Parameters
    ----------
    page : int
        The current page number. Page numbers should start from 1.
    items_per_page : int
        The number of items to be displayed on each page.

    Returns
    ----------
    int
        The calculated offset.

    Examples
    ----------
    >>> offset(1, 10)
    0
    >>> offset(3, 10)
    20
    """
    return (page - 1) * items_per_page
