# Local Dependencies
from src.core.common.repository import RepositoryBase
from src.apps.example.items.models import Item
from src.apps.example.items.schemas import (
    ItemCreateInternal,
    ItemUpdate,
    ItemUpdateInternal,
    ItemDelete,
)

ItemRepository = RepositoryBase[
    Item, ItemCreateInternal, ItemUpdate, ItemUpdateInternal, ItemDelete
]

item_repository = ItemRepository(Item)
