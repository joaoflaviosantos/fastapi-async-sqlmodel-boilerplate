# Built-in Dependencies
import math


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
