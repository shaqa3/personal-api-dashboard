from __future__ import annotations

import time
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .connectors import (
    GitHubConnector,
    SpotifyConnector,
    StravaConnector,
    WakaTimeConnector,
)
from .connectors.base import SourceStatus
from .models import Health, SourceState, StatsResponse
from .scheduler import refresh_all
from .store import SourceStore


def build_connectors(settings):
    return [
        GitHubConnector(settings.github_username, settings.github_token),
        SpotifyConnector(
            settings.spotify_client_id,
            settings.spotify_client_secret,
            settings.spotify_refresh_token,
        ),
        StravaConnector(
            settings.strava_client_id,
            settings.strava_client_secret,
            settings.strava_refresh_token,
        ),
        WakaTimeConnector(settings.wakatime_api_key),
    ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    store = SourceStore()
    client = httpx.AsyncClient()
    connectors = build_connectors(settings)

    app.state.store = store
    app.state.client = client
    app.state.connectors = connectors

    # Warm the cache once on startup, then keep it warm on a schedule.
    await refresh_all(connectors, client, store)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        refresh_all,
        "interval",
        seconds=settings.refresh_interval_seconds,
        args=[connectors, client, store],
        id="refresh_all",
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    app.state.scheduler = scheduler

    try:
        yield
    finally:
        scheduler.shutdown(wait=False)
        await client.aclose()


settings = get_settings()

app = FastAPI(
    title="Personal API + Status Dashboard",
    version="1.0.0",
    description=(
        "Aggregates my data from third-party APIs (GitHub, Spotify, WakaTime) "
        "behind a single cached endpoint. Sources refresh on a schedule and "
        "degrade gracefully when upstream is down or unconfigured."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Serves the embeddable widget at /static/now-playing.js
app.mount(
    "/static",
    StaticFiles(directory=Path(__file__).parent / "static"),
    name="static",
)


def _stats_payload(store: SourceStore) -> StatsResponse:
    sources = {
        name: SourceState(**result.to_dict()) for name, result in store.all().items()
    }
    healthy = any(
        s.status in (SourceStatus.OK.value, SourceStatus.DEGRADED.value)
        for s in sources.values()
    )
    return StatsResponse(generated_at=time.time(), healthy=healthy, sources=sources)


@app.get("/api/stats", response_model=StatsResponse, tags=["stats"])
async def get_stats():
    """Unified endpoint your portfolio calls. Returns every source at once."""
    return _stats_payload(app.state.store)


@app.get("/api/stats/{source}", response_model=SourceState, tags=["stats"])
async def get_source(source: str):
    """A single source's state (github | spotify | wakatime)."""
    result = app.state.store.get(source)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Unknown source '{source}'")
    return SourceState(**result.to_dict())


@app.get("/api/now-playing", tags=["widgets"])
async def now_playing():
    """Convenience shortcut for the 'now playing' hero widget."""
    result = app.state.store.get("spotify")
    if result is None:
        return {"is_playing": False, "status": "disabled"}
    payload = dict(result.data)
    payload["status"] = result.status.value
    return payload


@app.get("/api/heatmap", tags=["widgets"])
async def heatmap():
    """Contribution/activity heatmap: {date: count} from recent GitHub pushes."""
    result = app.state.store.get("github")
    data = result.data if result else {}
    return {"heatmap": data.get("heatmap", {}), "status": result.status.value if result else "disabled"}


@app.post("/api/refresh", tags=["stats"])
async def refresh_now():
    """Force an immediate refresh of every source (bypasses the schedule)."""
    await refresh_all(app.state.connectors, app.state.client, app.state.store)
    return {"refreshed": True, "at": time.time()}


@app.get("/healthz", response_model=Health, tags=["ops"])
async def healthz():
    sources = {name: r.status.value for name, r in app.state.store.all().items()}
    return Health(status="ok", sources=sources)
