from __future__ import annotations

from typing import Optional

import httpx

from .base import Connector, SourceResult

TOKEN_URL = "https://www.strava.com/oauth/token"
ATHLETE_URL = "https://www.strava.com/api/v3/athlete"
STATS_URL = "https://www.strava.com/api/v3/athletes/{id}/stats"


def _meters_to_km(m: Optional[float]) -> Optional[float]:
    return round(m / 1000, 1) if m else 0.0


def _totals(block: dict) -> dict:
    return {
        "count": block.get("count", 0),
        "distance_km": _meters_to_km(block.get("distance")),
        "moving_time_hours": round((block.get("moving_time") or 0) / 3600, 1),
        "elevation_gain_m": round(block.get("elevation_gain") or 0),
    }


class StravaConnector(Connector):
    """Strava athlete stats via the OAuth refresh-token flow. Like Spotify, we
    trade a long-lived refresh token for a short-lived access token per fetch."""

    name = "strava"

    def __init__(
        self,
        client_id: Optional[str],
        client_secret: Optional[str],
        refresh_token: Optional[str],
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token

    @property
    def enabled(self) -> bool:
        return bool(self.client_id and self.client_secret and self.refresh_token)

    async def _access_token(self, client: httpx.AsyncClient) -> str:
        resp = await client.post(
            TOKEN_URL,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    async def fetch(self, client: httpx.AsyncClient) -> SourceResult:
        token = await self._access_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        athlete_resp = await client.get(ATHLETE_URL, headers=headers, timeout=10)
        athlete_resp.raise_for_status()
        athlete = athlete_resp.json()

        stats_resp = await client.get(
            STATS_URL.format(id=athlete["id"]), headers=headers, timeout=10
        )
        stats_resp.raise_for_status()
        stats = stats_resp.json()

        data = {
            "athlete": f"{athlete.get('firstname', '')} {athlete.get('lastname', '')}".strip(),
            "recent_runs": _totals(stats.get("recent_run_totals", {})),
            "recent_rides": _totals(stats.get("recent_ride_totals", {})),
            "ytd_runs": _totals(stats.get("ytd_run_totals", {})),
            "ytd_rides": _totals(stats.get("ytd_ride_totals", {})),
        }
        return self.ok(data)
