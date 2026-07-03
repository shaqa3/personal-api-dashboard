from __future__ import annotations

from typing import Dict, Optional

from .connectors.base import SourceResult


class SourceStore:
    """In-memory cache of the latest result per source. This is what the API
    serves from, so requests never block on a live upstream call — the
    scheduler keeps it warm in the background."""

    def __init__(self) -> None:
        self._results: Dict[str, SourceResult] = {}

    def update(self, result: SourceResult) -> None:
        self._results[result.source] = result

    def get(self, name: str) -> Optional[SourceResult]:
        return self._results.get(name)

    def all(self) -> Dict[str, SourceResult]:
        return dict(self._results)
