"""Adapter verso la web app "finanze" già esistente (tab opzionale).

Auth: API key statica per-servizio (FINANCE_APP_API_KEY).
TODO: definire cosa esporre davvero (saldo? prossime spese?) e i path reali
una volta chiariti con l'app esistente.
"""

import httpx

from app.adapters.base import SourceAdapter
from app.core.config import get_settings

settings = get_settings()

_MOCK_SUMMARY = {"balance": 0.0, "note": "Integrazione finanze non ancora configurata"}


class FinanceAdapter(SourceAdapter):
    cache_ttl = settings.cache_ttl_apps

    @property
    def is_configured(self) -> bool:
        return bool(settings.finance_app_base_url and settings.finance_app_api_key)

    async def fetch(self) -> dict:
        if not self.is_configured:
            return _MOCK_SUMMARY
        async with httpx.AsyncClient(base_url=settings.finance_app_base_url, timeout=5.0) as client:
            # TODO: endpoint reale, es. GET /api/summary
            response = await client.get(
                "/api/summary",
                headers={"Authorization": f"Bearer {settings.finance_app_api_key}"},
            )
            response.raise_for_status()
            return response.json()

    def normalize(self, raw: dict) -> dict:
        return raw
