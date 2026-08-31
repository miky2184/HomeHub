"""Geocoding generico (nome di un luogo -> lat/lon) via Nominatim
(OpenStreetMap, https://nominatim.org/), gratuito e senza chiave — a
differenza del geocoding di Open-Meteo (adapters/weather.py, pensato per
nomi di città), qui serve risolvere anche nomi di centri di smistamento
("Milano Roserio", "CMP Bologna"...), per cui Nominatim (ricerca libera,
non solo città) si comporta meglio.

Policy d'uso di Nominatim (https://operations.osmfoundation.org/policies/nominatim/):
massimo 1 richiesta/secondo e uno User-Agent che identifichi l'applicazione
(niente User-Agent di default/browser) — rispettata qui perché ogni
risultato viene messo in cache a lungo dal chiamante (vedi
services/aggregator.get_shipment_route) e le richieste per una spedizione
sono in sequenza, non in parallelo.

Solo per il percorso indicativo delle spedizioni (Spedizioni): Poste non
fornisce indirizzi di mittente/destinatario nel tracciamento pubblico (per
buoni motivi di privacy — chiunque veda il numero saprebbe l'indirizzo),
solo il nome del luogo/centro di ogni tappa. Il risultato è quindi un
percorso a livello di città/hub, non porta a porta."""

import httpx

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Nominatim richiede un User-Agent che identifichi l'app (vedi policy sopra),
# non un valore a caso: nessun dato personale, solo un nome + un modo di
# essere contattati in caso di abuso involontario.
_HEADERS = {"User-Agent": "HomeHub-personal-dashboard/1.0 (uso privato, no API key)"}


async def geocode_place(place: str) -> tuple[float, float] | None:
    """Coordinate approssimative di un luogo (città o centro di
    smistamento), o None se non risolvibile — mai un'eccezione verso il
    chiamante: è un arricchimento opzionale (la mappa), non deve rompere il
    resto della pagina spedizione se un nome non si geolocalizza. ", Italia"
    aggiunto alla query: i luoghi Poste sono location italiane, e senza
    questo suggerimento Nominatim a volte risolve un nome ambiguo
    all'estero."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                NOMINATIM_URL,
                params={"q": f"{place}, Italia", "format": "json", "limit": 1},
                headers=_HEADERS,
            )
            response.raise_for_status()
            results = response.json()
    except (httpx.HTTPError, ValueError):
        return None
    if not results:
        return None
    try:
        return float(results[0]["lat"]), float(results[0]["lon"])
    except (KeyError, TypeError, ValueError):
        return None
