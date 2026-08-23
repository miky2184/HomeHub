"""Adapter Bring! (API non ufficiale).

TODO (integrazione reale):
- usare una libreria non ufficiale (es. `python-bring-api`) autenticandosi con
  BRING_EMAIL / BRING_PASSWORD da .env
- mappare la lista/gli articoli Bring! sullo schema ShoppingItem
- implementare le azioni "toggle_item", "add_item", "remove_item"

Finché le credenziali non sono configurate, l'adapter lavora su una lista
finta in memoria, utile per sviluppare/testare il frontend.
"""

from app.adapters.base import WritableSourceAdapter
from app.core.config import get_settings
from app.schemas.common import ShoppingItem

settings = get_settings()

_MOCK_ITEMS: list[dict] = [
    {"id": "1", "name": "Latte", "checked": False, "specification": None},
    {"id": "2", "name": "Uova", "checked": False, "specification": "6 uova"},
    {"id": "3", "name": "Pane", "checked": True, "specification": None},
]


class BringAdapter(WritableSourceAdapter):
    cache_ttl = settings.cache_ttl_bring

    @property
    def is_configured(self) -> bool:
        return bool(settings.bring_email and settings.bring_password)

    async def fetch(self) -> list[dict]:
        if not self.is_configured:
            return _MOCK_ITEMS
        # TODO: chiamata reale all'API non ufficiale di Bring!
        raise NotImplementedError("Integrazione Bring! non ancora configurata")

    def normalize(self, raw: list[dict]) -> list[ShoppingItem]:
        return [ShoppingItem(**item) for item in raw]

    async def perform_action(self, action: str, payload: dict) -> list[ShoppingItem]:
        if not self.is_configured:
            if action == "toggle_item":
                for item in _MOCK_ITEMS:
                    if item["id"] == payload["item_id"]:
                        item["checked"] = not item["checked"]
            elif action == "add_item":
                new_id = str(len(_MOCK_ITEMS) + 1)
                _MOCK_ITEMS.append(
                    {
                        "id": new_id,
                        "name": payload["name"],
                        "checked": False,
                        "specification": payload.get("specification"),
                    }
                )
            elif action == "remove_item":
                _MOCK_ITEMS[:] = [i for i in _MOCK_ITEMS if i["id"] != payload["item_id"]]
            else:
                raise ValueError(f"Azione non supportata: {action}")
            return self.normalize(_MOCK_ITEMS)
        # TODO: chiamata reale di scrittura verso l'API non ufficiale di Bring!
        raise NotImplementedError("Integrazione Bring! non ancora configurata")
