from __future__ import annotations

from typing import Optional

import httpx

from .base import Connector, SourceResult

TOKEN_URL = "https://accounts.spotify.com/api/token"
NOW_PLAYING_URL = "https://api.spotify.com/v1/me/player/currently-playing"
RECENT_URL = "https://api.spotify.com/v1/me/player/recently-played?limit=1"


class SpotifyConnector(Connector):
    """Spotify 'now playing'. Uses the Authorization Code refresh-token flow:
    we exchange a long-lived refresh token for a short-lived access token on
    every fetch. If nothing is playing, falls back to the last played track."""

    name = "spotify"

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
            data={"grant_type": "refresh_token", "refresh_token": self.refresh_token},
            auth=(self.client_id, self.client_secret),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    @staticmethod
    def _track(item: dict, is_playing: bool) -> dict:
        album = item.get("album", {}) or {}
        images = album.get("images") or [{}]
        return {
            "is_playing": is_playing,
            "track": item.get("name"),
            "artist": ", ".join(a["name"] for a in item.get("artists", [])),
            "album": album.get("name"),
            "album_art": images[0].get("url"),
            "url": (item.get("external_urls") or {}).get("spotify"),
            "duration_ms": item.get("duration_ms"),
        }

    async def fetch(self, client: httpx.AsyncClient) -> SourceResult:
        token = await self._access_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.get(NOW_PLAYING_URL, headers=headers, timeout=10)
        if resp.status_code == 200 and resp.content:
            payload = resp.json()
            item = payload.get("item")
            if item:
                data = self._track(item, payload.get("is_playing", False))
                data["progress_ms"] = payload.get("progress_ms")
                return self.ok(data)

        # Nothing playing (204) -> show most recently played, marked not playing.
        recent = await client.get(RECENT_URL, headers=headers, timeout=10)
        recent.raise_for_status()
        items = recent.json().get("items", [])
        if items:
            data = self._track(items[0]["track"], is_playing=False)
            data["played_at"] = items[0].get("played_at")
            return self.ok(data)

        return self.ok({"is_playing": False, "track": None})
