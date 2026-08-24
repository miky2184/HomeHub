"""Santo del giorno — API gratuita e non ufficiale di santodelgiorno.it,
verificata a mano prima di integrarla (nessuna chiave richiesta):
GET https://www.santodelgiorno.it/santi.json?data=YYYY-MM-DD ritorna una
lista di santi per quella data, ciascuno con un campo "default" — quello a
"1" è il santo principale del giorno (quello che si festeggia più
comunemente), gli altri sono santi minori/alternativi per la stessa data.
"""

from datetime import date

import httpx

BASE_URL = "https://www.santodelgiorno.it/santi.json"


async def fetch_saint_of_day(day: date) -> str | None:
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(BASE_URL, params={"data": day.isoformat()})
        response.raise_for_status()
        data = response.json()
    if not data:
        return None
    default_entry = next((s for s in data if s.get("default") == "1"), data[0])
    return default_entry.get("nome")
