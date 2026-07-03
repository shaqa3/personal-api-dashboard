from __future__ import annotations

from typing import Optional

import httpx

from .base import Connector, SourceResult

API = "https://api.github.com"
GRAPHQL = "https://api.github.com/graphql"

CONTRIBUTIONS_QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { date contributionCount }
        }
      }
    }
  }
}
"""


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

    async def _contribution_calendar(self, client: httpx.AsyncClient):
        """Accurate full-year contribution heatmap via the GraphQL API.
        Requires a token. Returns (heatmap dict of non-zero days, total)."""
        resp = await client.post(
            GRAPHQL,
            headers={
                "Authorization": f"Bearer {self.token}",
                "User-Agent": "personal-api-dashboard",
            },
            json={"query": CONTRIBUTIONS_QUERY, "variables": {"login": self.username}},
            timeout=15,
        )
        resp.raise_for_status()
        body = resp.json()
        if body.get("errors"):
            raise ValueError(body["errors"][0].get("message", "graphql error"))

        calendar = body["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        heatmap = {
            day["date"]: day["contributionCount"]
            for week in calendar["weeks"]
            for day in week["contributionDays"]
            if day["contributionCount"] > 0
        }
        return heatmap, calendar["totalContributions"]

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
            payload = ev.get("payload", {})
            commits = payload.get("commits", [])
            # GitHub sometimes returns a stripped PushEvent payload with no
            # `commits` array and no `size`. Fall back through: commit count ->
            # `size` -> 1 (a push happened, count it as activity).
            if commits:
                n = len(commits)
            elif payload.get("size"):
                n = payload["size"]
            else:
                n = 1
            date = ev["created_at"][:10]
            heatmap[date] = heatmap.get(date, 0) + n
            push_commits += n
            if latest_commit is None:
                latest_commit = {
                    "message": commits[-1]["message"].splitlines()[0]
                    if commits
                    else f"pushed to {ev['repo']['name'].split('/')[-1]}",
                    "repo": ev["repo"]["name"],
                    "at": ev["created_at"],
                }

        # Prefer the accurate full-year contribution calendar when we have a
        # token; fall back to the events-derived heatmap on any failure.
        heatmap_source = "events"
        contributions_last_year = None
        if self.token:
            try:
                heatmap, contributions_last_year = await self._contribution_calendar(client)
                heatmap_source = "graphql"
            except Exception:  # noqa: BLE001 - degrade to the events heatmap
                heatmap_source = "events"

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
            "heatmap_source": heatmap_source,
            "contributions_last_year": contributions_last_year,
        }
        return self.ok(data)
