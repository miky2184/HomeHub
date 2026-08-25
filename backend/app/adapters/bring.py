"""Adapter Bring! — integrazione reale tramite la libreria non ufficiale
`bring-api` (https://pypi.org/project/bring-api/), verificata contro la
versione 1.1.2: `Bring(session, email, password)`, `load_lists()` ritorna
`BringListResponse.lists` (oggetti `BringList` con `.listUuid`), `get_list()`
ritorna `BringItemsResponse.items.{purchase,recently}` (oggetti `BringPurchase`
con `.itemId`/`.specification`).

Nota sul modello dati: per Bring! l'identificativo "naturale" di un articolo
nelle azioni di scrittura (save/complete/remove) è il **nome** (`itemId`,
che nonostante il nome è la stringa del prodotto, non un id opaco), non lo
`uuid` interno — coerente con come funziona l'app Bring! stessa (non puoi
avere due articoli con lo stesso nome in corso contemporaneamente). Per
questo il nostro `ShoppingItem.id` usa il nome anche come identificativo.

Finché BRING_EMAIL/BRING_PASSWORD non sono configurate in .env, l'adapter
lavora su una lista finta in memoria, per sviluppare/testare il frontend
senza un vero account.
"""

import asyncio

import aiohttp
from bring_api import Bring, BringItemsResponse

from app.adapters.base import WritableSourceAdapter
from app.core.config import get_settings
from app.core.runtime_settings import effective_settings
from app.schemas.common import ShoppingItem

settings = get_settings()

_MOCK_ITEMS: list[dict] = [
    {"id": "Latte", "name": "Latte", "checked": False, "specification": None},
    {"id": "Uova", "name": "Uova", "checked": False, "specification": "6 uova"},
    {"id": "Pane", "name": "Pane", "checked": True, "specification": None},
]


class BringAdapter(WritableSourceAdapter):
    cache_ttl = settings.cache_ttl_bring

    def __init__(self) -> None:
        self._session: aiohttp.ClientSession | None = None
        self._bring: Bring | None = None
        self._list_uuid: str | None = None
        # Login e selezione lista sono lazy (solo alla prima chiamata) senza
        # essere idempotenti a metà: senza questo lock, due richieste quasi
        # simultanee sul client ancora "vuoto" (subito dopo l'avvio, o dopo
        # un cambio credenziali che azzera _bring, vedi aclose) vedrebbero
        # entrambe self._bring is None ed entrerebbero insieme, oppure la
        # seconda vedrebbe self._bring già assegnato dalla prima e salterebbe
        # login() usando un client non ancora autenticato.
        self._client_lock = asyncio.Lock()

    @property
    def is_configured(self) -> bool:
        es = effective_settings()
        return bool(es.bring_email and es.bring_password)

    async def _get_client(self) -> tuple[Bring, str]:
        """Login e selezione lista lazy, riutilizzate tra le chiamate (evita
        di autenticarsi ad ogni richiesta). Se le credenziali cambiano da
        Impostazioni, api/routes/settings.py chiama aclose() per farle
        rileggere qui alla prossima chiamata."""
        async with self._client_lock:
            if self._bring is None:
                es = effective_settings()
                self._session = aiohttp.ClientSession()
                self._bring = Bring(self._session, es.bring_email, es.bring_password)
                await self._bring.login()
            if self._list_uuid is None:
                lists = (await self._bring.load_lists()).lists
                if not lists:
                    raise RuntimeError("Nessuna lista Bring! trovata per questo account")
                # TODO: se in futuro serve gestire più liste, esporre una scelta
                # invece di prendere sempre la prima della famiglia
                self._list_uuid = lists[0].listUuid
            return self._bring, self._list_uuid

    async def aclose(self) -> None:
        """Chiude la sessione HTTP e azzera tutto lo stato cache (client
        autenticato + lista selezionata) — da chiamare sia allo shutdown
        dell'app sia quando le credenziali cambiano da Impostazioni (senza
        azzerare _list_uuid, dopo un cambio account resterebbe puntata alla
        lista dell'account precedente)."""
        if self._session is not None:
            await self._session.close()
            self._session = None
            self._bring = None
        self._list_uuid = None

    async def fetch(self) -> list[dict]:
        if not self.is_configured:
            return _MOCK_ITEMS
        bring, list_uuid = await self._get_client()
        response: BringItemsResponse = await bring.get_list(list_uuid)
        items = [
            {"id": item.itemId, "name": item.itemId, "specification": item.specification or None, "checked": False}
            for item in response.items.purchase
        ]
        items += [
            {"id": item.itemId, "name": item.itemId, "specification": item.specification or None, "checked": True}
            for item in response.items.recently
        ]
        return items

    def normalize(self, raw: list[dict]) -> list[ShoppingItem]:
        return [ShoppingItem(**item) for item in raw]

    async def perform_action(self, action: str, payload: dict) -> list[ShoppingItem]:
        if not self.is_configured:
            if action == "toggle_item":
                for item in _MOCK_ITEMS:
                    if item["id"] == payload["item_id"]:
                        item["checked"] = not item["checked"]
            elif action == "add_item":
                _MOCK_ITEMS.append(
                    {
                        "id": payload["name"],
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

        bring, list_uuid = await self._get_client()
        if action == "add_item":
            await bring.save_item(list_uuid, payload["name"], payload.get("specification") or "")
        elif action == "toggle_item":
            item_id = payload["item_id"]
            current = await self.fetch()
            match = next((i for i in current if i["id"] == item_id), None)
            if match is None:
                raise ValueError(f"Articolo non trovato: {item_id}")
            if match["checked"]:
                # "de-spuntare" un articolo = rimandarlo in lista da comprare
                await bring.save_item(list_uuid, item_id, match.get("specification") or "")
            else:
                await bring.complete_item(list_uuid, item_id)
        elif action == "remove_item":
            await bring.remove_item(list_uuid, payload["item_id"])
        else:
            raise ValueError(f"Azione non supportata: {action}")

        return self.normalize(await self.fetch())
