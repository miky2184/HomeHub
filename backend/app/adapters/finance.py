"""Adapter verso la web app "finanze" (python-finanze-api).

⚠️ PRIVACY: HomeHub gira su un monitor in cucina visibile anche dagli
ospiti. Questo adapter non deve MAI restituire importi assoluti (saldi,
budget o spesa in euro) — solo percentuali/stati derivati (vedi
`aggregate_by_category`). Gli importi assoluti restituiti dall'API della
web app finanze restano solo in memoria qui dentro, il tempo di calcolare
le percentuali: non attraversano mai `normalize()` né gli schemi Pydantic
verso il frontend. Vedi anche la "modalità ospiti" (app_config, gestita in
services/aggregator.py) che nasconde l'intera sezione su richiesta.

Auth: login utente/password (stesso account personale usato sulla web app
— scelta esplicita dell'utente, non un account dedicato), JWT valido 8h
lato server: qui lo cachiamo con un margine di sicurezza e rifacciamo
login automaticamente se scade o se una richiesta torna 403.

Le percentuali vengono dall'endpoint `/budget-forecast-all` di
quell'app, che calcola già lì la logica di business (proiezione lineare
sui giorni del mese, eccezione per le spese fisse) — replicarla qui
sarebbe fragile e duplicato. `aggregate_by_category` riaggrega solo le
sottocategorie/conti in un unico valore per categoria, con le stesse
formule usate in quell'app per calcolare percentuale/alert_level.
"""

from datetime import date, datetime, timedelta

import httpx

from app.adapters.base import SourceAdapter
from app.core.config import get_settings
from app.schemas.common import FinanceCategoryStatus

settings = get_settings()


def aggregate_by_category(rows: list[dict]) -> list[FinanceCategoryStatus]:
    """Somma budget/speso/proiezione (importi assoluti, SOLO qui in
    memoria) per categoria — righe multiple per la stessa categoria
    arrivano da sottocategorie diverse e/o conti diversi. Poi calcola le
    percentuali con le stesse formule di /budget-forecast-all: mai un
    euro nel valore di ritorno."""
    totals: dict[str, dict[str, float]] = {}
    for row in rows:
        label = row.get("categoria_label")
        if not label:
            continue
        agg = totals.setdefault(label, {"budget_mese": 0.0, "speso_mese": 0.0, "proiezione_mese": 0.0})
        agg["budget_mese"] += float(row.get("budget_mese") or 0)
        agg["speso_mese"] += float(row.get("speso_mese") or 0)
        agg["proiezione_mese"] += float(row.get("proiezione_mese") or 0)

    result = []
    for label, agg in totals.items():
        budget, speso, proiezione = agg["budget_mese"], agg["speso_mese"], agg["proiezione_mese"]
        if budget == 0 or speso >= 0:
            perc_speso, perc_proiezione, alert_level = 0.0, 0.0, 0
        else:
            perc_speso = round(abs(speso) / abs(budget) * 100, 1)
            perc_proiezione = round(abs(proiezione) / abs(budget) * 100, 1)
            alert_level = 2 if abs(proiezione) > abs(budget) else (1 if abs(proiezione) > abs(budget) * 0.8 else 0)
        result.append(
            FinanceCategoryStatus(
                label=label, perc_speso=perc_speso, perc_proiezione=perc_proiezione, alert_level=alert_level
            )
        )
    return sorted(result, key=lambda c: (-c.alert_level, -c.perc_proiezione))


class FinanceAdapter(SourceAdapter):
    cache_ttl = 900  # 15 minuti, coerente con le altre web app esistenti

    def __init__(self) -> None:
        self._token: str | None = None
        self._id_db: int | None = None
        self._token_expires_at: datetime | None = None
        self._login_failed_until: datetime | None = None

    @property
    def is_configured(self) -> bool:
        return bool(settings.finance_app_base_url and settings.finance_username and settings.finance_password)

    async def _login(self, client: httpx.AsyncClient) -> None:
        response = await client.post(
            "/login", json={"username": settings.finance_username, "pwd": settings.finance_password}
        )
        response.raise_for_status()
        data = response.json()
        self._token = data["access_token"]
        self._id_db = data["res"]["id_db"]
        # Il token dura 8h lato server (core/auth_config.py in quel repo):
        # margine di sicurezza per non arrivarci vicini.
        self._token_expires_at = datetime.now() + timedelta(hours=7)

    async def _ensure_session(self, client: httpx.AsyncClient) -> None:
        if self._token and self._token_expires_at and datetime.now() < self._token_expires_at:
            return
        if self._login_failed_until and datetime.now() < self._login_failed_until:
            raise RuntimeError("Login finanze fallito di recente, nuovo tentativo tra poco")
        try:
            await self._login(client)
        except Exception:
            self._token = None
            self._login_failed_until = datetime.now() + timedelta(seconds=60)
            raise

    async def _post(self, client: httpx.AsyncClient, path: str, payload: dict) -> dict | list:
        body = {**payload, "id_db": self._id_db}
        response = await client.post(path, json=body, headers={"Authorization": f"Bearer {self._token}"})
        if response.status_code == 403:
            # Token scaduto lato server nonostante la nostra cache locale.
            self._token = None
            await self._ensure_session(client)
            response = await client.post(path, json=body, headers={"Authorization": f"Bearer {self._token}"})
        response.raise_for_status()
        return response.json()

    async def fetch(self) -> list[dict]:
        """Righe grezze (categoria + importi assoluti) da /budget-forecast-all,
        per tutti i conti dell'utente, mese corrente. MAI restituite così
        come sono a valle: passano da normalize()/aggregate_by_category
        prima di uscire da questo adapter. Il chiamante (get_finance_summary)
        controlla già is_configured prima di invocare fetch: qui non c'è un
        fallback mock, a differenza degli altri adapter — niente dati,
        nemmeno finti, finché l'integrazione non è configurata per davvero."""
        async with httpx.AsyncClient(base_url=settings.finance_app_base_url, timeout=10.0) as client:
            await self._ensure_session(client)
            conti = await self._post(client, "/conto", {})
            conto_ids = [c["id"] for c in conti]
            if not conto_ids:
                return []
            today = date.today()
            forecast = await self._post(
                client, "/budget-forecast-all", {"anno": today.year, "mese": today.month, "conti": conto_ids}
            )
            rows: list[dict] = []
            for conto_rows in forecast.values():
                rows.extend(conto_rows)
            return rows

    def normalize(self, raw: list[dict]) -> list[FinanceCategoryStatus]:
        return aggregate_by_category(raw)
