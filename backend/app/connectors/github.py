from __future__ import annotations

from typing import Optional

import httpx

from .base import Connector, SourceResult

API = "https://api.github.com"


class GitHubConnector(Connector):
    """Public GitHub profile + recent activity. Works without a token;
    a token just raises the rate limit from 60 to 5000 req/hour."""

    name = "github"

    def __init__(self, username: Optional[str], token: Optional[str] = None):
        self.username = username
        self.token = token

    @property
    def enabled(self) -> bool:
        return bool(self.username)

    def _headers(self):
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "personal-api-dashboard",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def fetch(self, client: httpx.AsyncClient) -> SourceResult:
        headers = self._headers()

        user_resp = await client.get(
            f"{API}/users/{self.username}", headers=headers, timeout=10
        )
        user_resp.raise_for_status()
        user = user_resp.json()

        events_resp = await client.get(
            f"{API}/users/{self.username}/events/public?per_page=100",
            headers=headers,
            timeout=10,
        )
        events_resp.raise_for_status()
        events = events_resp.json()

        heatmap: dict[str, int] = {}
        push_commits = 0
        latest_commit = None

        for ev in events:
            if ev.get("type") != "PushEvent":
                continue
            commits = ev.get("payload", {}).get("commits", [])
            n = len(commits)
            if n == 0:
                continue
            date = ev["created_at"][:10]
            heatmap[date] = heatmap.get(date, 0) + n
            push_commits += n
            if latest_commit is None and commits:
                latest_commit = {
                    "message": commits[-1]["message"].splitlines()[0],
                    "repo": ev["repo"]["name"],
                    "at": ev["created_at"],
                }

        data = {
            "username": self.username,
            "name": user.get("name"),
            "avatar": user.get("avatar_url"),
            "bio": user.get("bio"),
            "followers": user.get("followers"),
            "following": user.get("following"),
            "public_repos": user.get("public_repos"),
            "profile_url": user.get("html_url"),
            "recent_push_commits": push_commits,
            "latest_commit": latest_commit,
            "heatmap": heatmap,
        }
        return self.ok(data)
