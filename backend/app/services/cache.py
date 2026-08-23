"""Cache in memoria molto semplice, con TTL per singola chiave.

Sufficiente per uno scaffold single-instance sul NUC. Se in futuro servisse
condividere la cache tra più processi/repliche, questa è il punto in cui
sostituirla con Redis mantenendo la stessa interfaccia (get_or_set).
"""

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any

_store: dict[str, tuple[float, Any]] = {}
_locks: dict[str, asyncio.Lock] = {}


async def get_or_set(key: str, ttl_seconds: int, loader: Callable[[], Awaitable[Any]]) -> Any:
    now = time.monotonic()
    cached = _store.get(key)
    if cached and cached[0] > now:
        return cached[1]

    lock = _locks.setdefault(key, asyncio.Lock())
    async with lock:
        # ricontrolla: un'altra richiesta potrebbe aver già ripopolato la cache
        cached = _store.get(key)
        if cached and cached[0] > now:
            return cached[1]
        value = await loader()
        _store[key] = (now + ttl_seconds, value)
        return value


def invalidate(key: str) -> None:
    _store.pop(key, None)
