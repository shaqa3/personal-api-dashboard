from __future__ import annotations

import asyncio
import time
from typing import List

import httpx

from .connectors.base import Connector, SourceResult, SourceStatus
from .store import SourceStore


async def refresh_source(
    connector: Connector, client: httpx.AsyncClient, store: SourceStore
) -> SourceResult:
    """Refresh a single source, applying graceful-degradation rules:
    - no credentials       -> DISABLED
    - fetch raises          -> DEGRADED (serve last-known-good) or DOWN
    """
    if not connector.enabled:
        result = SourceResult(connector.name, SourceStatus.DISABLED, fetched_at=time.time())
        store.update(result)
        return result

    try:
        result = await connector.fetch(client)
    except Exception as exc:  # noqa: BLE001 - we want to catch any upstream failure
        prev = store.get(connector.name)
        if prev and prev.data:
            result = SourceResult(
                connector.name,
                SourceStatus.DEGRADED,
                data=prev.data,
                error=f"{type(exc).__name__}: {exc}",
                fetched_at=prev.fetched_at,
            )
        else:
            result = SourceResult(
                connector.name,
                SourceStatus.DOWN,
                error=f"{type(exc).__name__}: {exc}",
                fetched_at=time.time(),
            )

    if result.fetched_at is None:
        result.fetched_at = time.time()
    store.update(result)
    return result


async def refresh_all(
    connectors: List[Connector], client: httpx.AsyncClient, store: SourceStore
) -> None:
    await asyncio.gather(*(refresh_source(c, client, store) for c in connectors))
