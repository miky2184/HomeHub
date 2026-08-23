"""Interfaccia comune per gli adapter: ogni fonte esterna (Google, Bring!, le web
app esistenti, ...) espone la stessa forma, così aggiungere una nuova fonte o
una nuova azione di scrittura non tocca il resto del backend (vedi ARCHITECTURE.md §7.3)."""

from abc import ABC, abstractmethod
from typing import Any


class SourceAdapter(ABC):
    """Adapter di sola lettura verso una fonte esterna."""

    #: tempo di validità della cache in secondi, sovrascritto dalle sottoclassi
    cache_ttl: int = 300

    @abstractmethod
    async def fetch(self) -> Any:
        """Recupera i dati grezzi dalla fonte (chiamata HTTP/API reale)."""

    @abstractmethod
    def normalize(self, raw: Any) -> Any:
        """Converte i dati grezzi nello schema unificato HomeHub (app.schemas.common)."""


class WritableSourceAdapter(SourceAdapter):
    """Adapter che supporta anche azioni di scrittura (spuntare, aggiungere, ...)."""

    @abstractmethod
    async def perform_action(self, action: str, payload: dict) -> Any:
        """Esegue un'azione (es. "toggle_item", "add_item") e ne ritorna l'esito."""
