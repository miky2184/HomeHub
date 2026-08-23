from fastapi import APIRouter

from app.adapters.inventory_app import InventoryAdapter
from app.schemas.common import InventoryAlert
from app.services import cache
from app.services.aggregator import get_inventory_alerts, inventory_adapter

router = APIRouter(prefix="/api/inventory", tags=["inventory"])


@router.get("/alerts", response_model=list[InventoryAlert])
async def list_alerts() -> list[InventoryAlert]:
    return await get_inventory_alerts()


@router.patch("/{item_id}/consume", response_model=list[InventoryAlert])
async def mark_consumed(item_id: str) -> list[InventoryAlert]:
    adapter: InventoryAdapter = inventory_adapter
    await adapter.perform_action("mark_consumed", {"item_id": item_id})
    cache.invalidate("inventory_alerts")
    return await get_inventory_alerts()
