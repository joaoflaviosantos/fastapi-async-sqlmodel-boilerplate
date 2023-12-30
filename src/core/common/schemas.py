# Built-in Dependencies
from typing import Any, Generic, TypeVar
from collections.abc import Sequence
from datetime import datetime, UTC
import uuid as uuid_pkg
from math import ceil

# Third-Party Dependencies
from fastapi_pagination.bases import AbstractPage, AbstractParams
from pydantic import Field, field_serializer, BaseModel
from fastapi_pagination import Params, Page

DataType = TypeVar("DataType")
T = TypeVar("T")

class PageBase(Page[T], Generic[T]):
    """
    Base class for paginated responses. Adds previous and next page numbers.
    """
    previous_page: int | None = Field(
        None, description="Page number of the previous page"
    )
    next_page: int | None = Field(None, description="Page number of the next page")


class IResponseBase(BaseModel, Generic[T]):
    """
    Base class for API response. Contains message, metadata, and data.
    """
    message: str = ""
    meta: dict = {}
    data: T | None


class IGetResponsePaginated(AbstractPage[T], Generic[T]):
    """
    API response class for paginated GET requests. Extends IResponseBase with pagination details.
    """
    message: str | None = ""
    meta: dict = {}
    data: PageBase[T]

    __params_type__ = Params  # Set params related to Page

    @classmethod
    def create(
        cls,
        items: Sequence[T],
        total: int,
        params: AbstractParams,
    ) -> PageBase[T] | None:
        """
        Create paginated response based on provided items, total count, and request params.
        """
        if params.size is not None and total is not None and params.size != 0:
            pages = ceil(total / params.size)
        else:
            pages = 0

        return cls(
            data=PageBase[T](
                items=items,
                page=params.page,
                size=params.size,
                total=total,
                pages=pages,
                next_page=params.page + 1 if params.page < pages else None,
                previous_page=params.page - 1 if params.page > 1 else None,
            )
        )


class IGetResponseBase(IResponseBase[DataType], Generic[DataType]):
    """
    API response class for basic GET requests.
    """
    message: str | None = "Data got correctly"


class IPostResponseBase(IResponseBase[DataType], Generic[DataType]):
    """
    API response class for POST requests.
    """
    message: str | None = "Data created correctly"


class IPutResponseBase(IResponseBase[DataType], Generic[DataType]):
    """
    API response class for PUT requests.
    """
    message: str | None = "Data updated correctly"


class IDeleteResponseBase(IResponseBase[DataType], Generic[DataType]):
    """
    API response class for DELETE requests.
    """
    message: str | None = "Data deleted correctly"


def create_response(
    data: DataType,
    message: str | None = None,
    meta: dict | Any | None = {},
) -> (
    IResponseBase[DataType]
    | IGetResponsePaginated[DataType]
    | IGetResponseBase[DataType]
    | IPutResponseBase[DataType]
    | IDeleteResponseBase[DataType]
    | IPostResponseBase[DataType]
):
    """
    Create a generic API response based on the provided data, message, and metadata.
    """
    if isinstance(data, IGetResponsePaginated):
        data.message = "Data paginated correctly" if message is None else message
        data.meta = meta
        return data
    if message is None:
        return {"data": data, "meta": meta}
    return {"data": data, "message": message, "meta": meta}


class HealthCheck(BaseModel):
    """
    Health check response schema.
    """
    name: str
    version: str
    description: str


# --------------------------------------
# ----------- MODELS MIXINS ------------
# --------------------------------------
class UUIDSchema(BaseModel):
    """
    Pydantic schema for UUID mixin.
    """
    uuid: uuid_pkg.UUID = Field(default_factory=uuid_pkg.uuid4)


class TimestampSchema(BaseModel):
    """
    Pydantic schema for Timestamp mixin.
    """
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
    updated_at: datetime = Field(default=None)

    @field_serializer("created_at")
    def serialize_dt(self, created_at: datetime | None, _info: Any) -> str | None:
        if created_at is not None:
            return created_at.isoformat()
        
        return None

    @field_serializer("updated_at")
    def serialize_updated_at(self, updated_at: datetime | None, _info: Any) -> str | None:
        if updated_at is not None:
            return updated_at.isoformat()

        return None


class PersistentDeletion(BaseModel):
    """
    Pydantic schema for PersistentDeletion mixin.
    """
    deleted_at: datetime | None = Field(default=None)
    is_deleted: bool = False

    @field_serializer('deleted_at')
    def serialize_dates(self, deleted_at: datetime | None, _info: Any) -> str | None:
        if deleted_at is not None:
            return deleted_at.isoformat()
        
        return None
