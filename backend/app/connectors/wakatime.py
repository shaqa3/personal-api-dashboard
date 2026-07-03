from __future__ import annotations

import base64
from typing import Optional

import httpx

from .base import Connector, SourceResult

STATS_URL = "https://wakatime.com/api/v1/users/current/stats/last_7_days"


class WakaTimeConnector(Connector):
    """WakaTime coding stats for the last 7 days. Auth is HTTP Basic with the
    base64-encoded API key as the username."""

    name = "wakatime"

    def __init__(self, api_key: Optional[str]):
        self.api_key = api_key

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    async def fetch(self, client: httpx.AsyncClient) -> SourceResult:
        encoded = base64.b64encode(self.api_key.encode()).decode()
        resp = await client.get(
            STATS_URL,
            headers={"Authorization": f"Basic {encoded}"},
            timeout=15,
        )
        resp.raise_for_status()
        stats = resp.json()["data"]

        data = {
            "range": stats.get("human_readable_range"),
            "total": stats.get("human_readable_total"),
            "daily_average": stats.get("human_readable_daily_average"),
            "languages": [
                {"name": l["name"], "percent": l["percent"], "text": l["text"]}
                for l in stats.get("languages", [])[:6]
            ],
            "editors": [
                {"name": e["name"], "percent": e["percent"]}
                for e in stats.get("editors", [])[:3]
            ],
        }
        return self.ok(data)
