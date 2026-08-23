"""Adapter verso la web app "menu di casa" già esistente (per il menu della sera,
distinto dal menu scolastico che invece è inserito a mano — vedi app.db.models).

Auth: API key statica per-servizio (MENU_APP_API_KEY), come da ARCHITECTURE.md §9.

TODO: adattare i path/campi reali dell'endpoint una volta noti; per ora il
mapping in `normalize` è indicativo.
"""

import httpx

from app.adapters.base import SourceAdapter
from app.core.config import get_settings

settings = get_settings()

_MOCK_TODAY_MEAL = "Pollo al forno con patate"


class HomeMenuAdapter(SourceAdapter):
    cache_ttl = settings.cache_ttl_apps

    @property
    def is_configured(self) -> bool:
        return bool(settings.menu_app_base_url and settings.menu_app_api_key)

    async def fetch(self) -> dict:
        if not self.is_configured:
            return {"today_meal": _MOCK_TODAY_MEAL}
        async with httpx.AsyncClient(base_url=settings.menu_app_base_url, timeout=5.0) as client:
            # TODO: endpoint reale, es. GET /api/menu/today
            response = await client.get(
                "/api/menu/today",
                headers={"Authorization": f"Bearer {settings.menu_app_api_key}"},
            )
            response.raise_for_status()
            return response.json()

    def normalize(self, raw: dict) -> str | None:
        return raw.get("today_meal")
