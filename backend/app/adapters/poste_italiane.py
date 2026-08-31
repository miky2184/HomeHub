"""Adapter Poste Italiane — tracking spedizioni tramite l'endpoint non
ufficiale usato dalla pagina "Dove Quando" del sito poste.it (nessuna API
pubblica documentata esiste per sviluppatori terzi). Contratto ricostruito
osservando il progetto community
https://github.com/danieleriso/Poste-italiane-tracking:

    POST https://www.poste.it/online/dovequando/DQ-REST/ricercamultipla
    Content-Type: application/json;charset=UTF-8
    body: {"tipoRichiedente": "WEB", "listaCodici": ["<tracking1>", ...]}

Risposta: lista di spedizioni con `idTracciatura` (il codice richiesto),
`sintesiStato` (stato sintetico) e `listaMovimenti` (storico eventi:
`dataOra` epoch ms, `statoLavorazione` descrizione, `luogo`), o
`descrizioneErrore` se il codice non è valido/non trovato.

Nessuna credenziale richiesta (endpoint pubblico, senza login) — a
differenza di Bring!/Garmin non serve nulla in Impostazioni/.env.

Essendo reverse-engineered e non documentato, può cambiare forma senza
preavviso: ogni parsing è difensivo (un singolo tracking number con un
formato inatteso non deve far fallire l'intero batch, vedi track()), e non
c'è alcuna certezza sui valori esatti di sintesiStato/statoLavorazione usati
da Poste per segnalare la consegna — l'euristica in _is_delivered va
verificata/affinata contro una risposta reale (vedi ARCHITECTURE.md)."""

from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

TRACKING_URL = "https://www.poste.it/online/dovequando/DQ-REST/ricercamultipla"

_HEADERS = {
    "Content-Type": "application/json;charset=UTF-8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Referer": "https://www.poste.it/cerca/index.html",
    "Origin": "https://www.poste.it",
}

# Sottostringhe (case-insensitive) che, se presenti nello stato sintetico o
# nell'ultimo evento, indicano una spedizione consegnata. Best-effort: Poste
# non pubblica un elenco ufficiale di stati possibili.
_DELIVERED_HINTS = ("consegnat", "recapitat")


class PosteItalianeError(Exception):
    """Errore nel recupero/parsing dello stato di una spedizione Poste."""


@dataclass
class PosteEvent:
    at: datetime
    description: str
    location: str | None


@dataclass
class PosteTrackingResult:
    status: str | None
    delivered: bool
    events: list[PosteEvent]  # ordine cronologico, più recente per ultimo


def _parse_event(raw: dict) -> PosteEvent | None:
    try:
        millis = raw["dataOra"]
        return PosteEvent(
            at=datetime.fromtimestamp(millis / 1000, tz=timezone.utc),
            description=raw.get("statoLavorazione") or "",
            location=raw.get("luogo") or None,
        )
    except (KeyError, TypeError, ValueError):
        # Un singolo evento mal formato non deve far perdere tutto lo
        # storico: lo si salta, il resto degli eventi resta valido.
        return None


def _is_delivered(status: str | None, events: list[PosteEvent]) -> bool:
    haystack = " ".join(filter(None, [status, events[-1].description if events else None])).lower()
    return any(hint in haystack for hint in _DELIVERED_HINTS)


def _parse_shipment(raw: dict) -> PosteTrackingResult:
    if raw.get("descrizioneErrore"):
        raise PosteItalianeError(raw["descrizioneErrore"])
    events = sorted(
        (e for e in (_parse_event(m) for m in raw.get("listaMovimenti") or []) if e is not None),
        key=lambda e: e.at,
    )
    status = raw.get("sintesiStato")
    return PosteTrackingResult(status=status, delivered=_is_delivered(status, events), events=events)


class PosteItalianeAdapter:
    """Nessuno stato/sessione da mantenere (l'endpoint non richiede login),
    a differenza di BringAdapter/GarminAdapter."""

    async def track(self, tracking_numbers: list[str]) -> dict[str, PosteTrackingResult | PosteItalianeError]:
        """Una chiamata batch per tutti i tracking number in input. Il dict
        di ritorno ha una entry per ciascun codice richiesto: un
        PosteTrackingResult se il parsing è andato a buon fine, l'eccezione
        (non sollevata, restituita come valore) se quel singolo codice ha
        fallito — così un tracking number rotto/non trovato non impedisce di
        leggere gli altri nello stesso batch. Solleva PosteItalianeError solo
        per un fallimento dell'intera chiamata (rete, HTTP, risposta non
        interpretabile come lista)."""
        if not tracking_numbers:
            return {}
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    TRACKING_URL,
                    headers=_HEADERS,
                    json={"tipoRichiedente": "WEB", "listaCodici": tracking_numbers},
                )
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            raise PosteItalianeError(f"Poste Italiane non raggiungibile: {exc}") from exc
        except ValueError as exc:
            raise PosteItalianeError(f"Risposta non valida da Poste Italiane: {exc}") from exc

        # La forma esatta della risposta (lista diretta vs. wrapper con
        # chiave tipo "risultati") non è documentata: si prova la lista
        # diretta e, se non è tale, si cerca la prima lista tra i valori.
        shipments = payload if isinstance(payload, list) else next(
            (v for v in payload.values() if isinstance(v, list)), []
        )

        results: dict[str, PosteTrackingResult | PosteItalianeError] = {}
        by_code = {s.get("idTracciatura"): s for s in shipments if isinstance(s, dict)}
        for code in tracking_numbers:
            raw = by_code.get(code)
            if raw is None:
                results[code] = PosteItalianeError("Nessuna informazione trovata per questo tracking number")
                continue
            try:
                results[code] = _parse_shipment(raw)
            except PosteItalianeError as exc:
                results[code] = exc
            except Exception as exc:  # formato imprevisto: non deve far fallire l'intero batch
                results[code] = PosteItalianeError(f"Formato di risposta inatteso: {exc}")
        return results
