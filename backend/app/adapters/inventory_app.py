"""Adapter verso la web app "home inventory" già esistente.

Auth: API key statica per-servizio (INVENTORY_APP_API_KEY).
TODO: adattare i path/campi reali una volta noti; per ora mapping indicativo.
"""

import httpx

from app.adapters.base import WritableSourceAdapter
from app.core.config import get_settings
from app.schemas.common import InventoryAlert

settings = get_settings()

_MOCK_ALERTS: list[dict] = [
    {"id": "1", "item_name": "Detersivo lavatrice", "quantity": 0, "unit": "pz", "reason": "low_stock"},
    {"id": "2", "item_name": "Carta igienica", "quantity": 2, "unit": "rotoli", "reason": "low_stock"},
]


class InventoryAdapter(WritableSourceAdapter):
    cache_ttl = settings.cache_ttl_apps

    @property
    def is_configured(self) -> bool:
        return bool(settings.inventory_app_base_url and settings.inventory_app_api_key)

    async def fetch(self) -> list[dict]:
        if not self.is_configured:
            return _MOCK_ALERTS
        async with httpx.AsyncClient(base_url=settings.inventory_app_base_url, timeout=5.0) as client:
            # TODO: endpoint reale, es. GET /api/inventory/low-stock
            response = await client.get(
                "/api/inventory/low-stock",
                headers={"Authorization": f"Bearer {settings.inventory_app_api_key}"},
            )
            response.raise_for_status()
            return response.json()

    def normalize(self, raw: list[dict]) -> list[InventoryAlert]:
        return [InventoryAlert(**item) for item in raw]

    async def perform_action(self, action: str, payload: dict) -> None:
        if action != "mark_consumed":
            raise ValueError(f"Azione non supportata: {action}")
        if not self.is_configured:
            _MOCK_ALERTS[:] = [a for a in _MOCK_ALERTS if a["id"] != payload["item_id"]]
            return
        async with httpx.AsyncClient(base_url=settings.inventory_app_base_url, timeout=5.0) as client:
            # TODO: endpoint reale di scrittura, es. POST /api/inventory/{id}/consume
            response = await client.post(
                f"/api/inventory/{payload['item_id']}/consume",
                headers={"Authorization": f"Bearer {settings.inventory_app_api_key}"},
            )
            response.raise_for_status()
