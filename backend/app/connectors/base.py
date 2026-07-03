from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

import httpx


class SourceStatus(str, Enum):
    OK = "ok"            # fresh data fetched successfully
    DEGRADED = "degraded"  # live fetch failed, serving last-known-good data
    DOWN = "down"        # live fetch failed and no cached data to fall back on
    DISABLED = "disabled"  # no credentials configured for this source


@dataclass
class SourceResult:
    source: str
    status: SourceStatus
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    fetched_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        age = None
        if self.fetched_at is not None:
            age = round(time.time() - self.fetched_at, 1)
        return {
            "source": self.source,
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "fetched_at": self.fetched_at,
            "age_seconds": age,
        }


class Connector:
    """Base class for a data source. Subclasses set `name` and implement `fetch`."""

    name: str = "base"

    @property
    def enabled(self) -> bool:
        """Whether credentials/config are present for this source."""
        return True

    async def fetch(self, client: httpx.AsyncClient) -> SourceResult:
        raise NotImplementedError

    def ok(self, data: Dict[str, Any]) -> SourceResult:
        return SourceResult(self.name, SourceStatus.OK, data=data, fetched_at=time.time())
