from fastapi import APIRouter

from app.adapters.bring import BringAdapter
from app.schemas.common import ShoppingItem, ShoppingItemCreate
from app.services import cache
from app.services.aggregator import bring_adapter, get_shopping_items

router = APIRouter(prefix="/api/shopping", tags=["shopping"])


@router.get("", response_model=list[ShoppingItem])
async def list_items() -> list[ShoppingItem]:
    return await get_shopping_items()


@router.post("", response_model=list[ShoppingItem])
async def add_item(payload: ShoppingItemCreate) -> list[ShoppingItem]:
    adapter: BringAdapter = bring_adapter
    items = await adapter.perform_action("add_item", payload.model_dump())
    cache.invalidate("shopping_items")
    return items


@router.patch("/{item_id}/toggle", response_model=list[ShoppingItem])
async def toggle_item(item_id: str) -> list[ShoppingItem]:
    adapter: BringAdapter = bring_adapter
    items = await adapter.perform_action("toggle_item", {"item_id": item_id})
    cache.invalidate("shopping_items")
    return items


@router.delete("/{item_id}", response_model=list[ShoppingItem])
async def remove_item(item_id: str) -> list[ShoppingItem]:
    adapter: BringAdapter = bring_adapter
    items = await adapter.perform_action("remove_item", {"item_id": item_id})
    cache.invalidate("shopping_items")
    return items
