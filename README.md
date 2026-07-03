# Personal API + Status Dashboard

[![CI](https://github.com/shaqa3/personal-api-dashboard/actions/workflows/ci.yml/badge.svg)](https://github.com/shaqa3/personal-api-dashboard/actions/workflows/ci.yml)

An API that aggregates *my* data from third-party services (GitHub, Spotify,
WakaTime, Strava) behind a single cached endpoint, with a live React dashboard
and an embeddable "now playing" widget for a portfolio site.

Built with **FastAPI** (auto OpenAPI docs), **httpx**, **APScheduler**, and a
**Vite + React** frontend.

```
┌────────────┐   scheduled    ┌─────────────┐   /api/stats   ┌──────────────┐
│ GitHub     │◀── refresh ────│  FastAPI    │◀───────────────│  React       │
│ Spotify    │   (cron)       │  in-memory  │   (cached,     │  dashboard   │
│ WakaTime   │──── data ─────▶│  cache      │────fast)──────▶│  + widgets   │
└────────────┘                └─────────────┘                └──────────────┘
```

## Why this design

- **Requests never block on an upstream.** The scheduler refreshes every source
  in the background on an interval; `/api/stats` just serves the warm cache.
- **Graceful degradation is first-class.** Every source reports one of four
  states, so one dead API never takes down the dashboard:
  | status | meaning |
  |---|---|
  | `ok` | fresh data fetched this cycle |
  | `degraded` | live fetch failed → serving last-known-good data |
  | `down` | fetch failed and there's no cached data to fall back on |
  | `disabled` | no credentials configured for this source |
- **Distinct auth patterns, on purpose.** GitHub (optional bearer token),
  WakaTime (HTTP Basic with a base64 API key), and Spotify + Strava (OAuth
  refresh-token grant) — the connectors cover the real-world token stories.

## Features

- Connectors for GitHub, Spotify, WakaTime, and Strava (`backend/app/connectors/`).
- Scheduled refresh + server-side caching so you don't hit rate limits.
- Unified `GET /api/stats` endpoint your portfolio calls.
- "Now playing" hero widget + a GitHub activity heatmap.
- Auto-generated OpenAPI docs at `/docs`.

### GitHub activity heatmap

The heatmap has two modes, chosen automatically:

- **With `GITHUB_TOKEN`** — queries the GraphQL `contributionsCollection` API for
  the accurate full-year contribution calendar (real per-day counts + yearly
  total), rendered as a 53-week grid.
- **Without a token** — derives a ~90-day window from the public events feed.
  This is a fallback: GitHub returns stripped `PushEvent` payloads for some
  accounts, so it counts pushes rather than exact commits.

The response exposes `heatmap_source` (`graphql` | `events`) and
`contributions_last_year` so you can tell which mode produced the data.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/stats` | Every source at once (the one your portfolio calls) |
| GET | `/api/stats/{source}` | A single source (`github` \| `spotify` \| `wakatime` \| `strava`) |
| GET | `/api/now-playing` | Shortcut for the Spotify hero widget |
| GET | `/api/heatmap` | `{date: count}` for the activity heatmap |
| POST | `/api/refresh` | Force an immediate refresh of all sources |
| GET | `/healthz` | Liveness + per-source status |
| GET | `/docs` | Interactive OpenAPI docs |
| GET | `/static/now-playing.js` | Embeddable portfolio widget (see below) |

## Running it

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in whatever credentials you have
uvicorn app.main:app --reload --port 8000
```

Every credential is optional — with an empty `.env`, all sources report
`disabled` and the app still runs. The fastest way to see live data is to set
`GITHUB_USERNAME` (no token required).

### Frontend

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173, proxies /api to :8000
```

`npm run build` emits a static bundle to `frontend/dist/` you can serve from
your portfolio; point it at the API with `VITE_API_BASE` if it's on another
origin (and set `CORS_ORIGINS` on the backend accordingly).

### With Docker

Runs the API + an nginx-served frontend that proxies `/api` to it:

```bash
cp backend/.env.example backend/.env   # optional; edit in your credentials
docker compose up --build
# dashboard  -> http://localhost:8080
# API + docs -> http://localhost:8080/docs
```

## Embeddable "now playing" widget

The API serves a zero-dependency widget you can drop into any site (your
portfolio hero, a blog). It self-styles, polls every 20s, and links to the
track. See [`embed-example.html`](./embed-example.html) for a full page.

```html
<div id="now-playing"></div>
<script
  src="https://YOUR-API/static/now-playing.js"
  data-api="https://YOUR-API"
  data-target="#now-playing"
  data-interval="20000"
></script>
```

Make sure your portfolio's origin is in the backend's `CORS_ORIGINS`.

## Configuration (`backend/.env`)

| Var | Notes |
|---|---|
| `REFRESH_INTERVAL_SECONDS` | How often the scheduler refreshes (default 300) |
| `CORS_ORIGINS` | Comma-separated allowed origins (`*` in dev) |
| `GITHUB_USERNAME` | Required to enable GitHub; public data needs no token |
| `GITHUB_TOKEN` | Optional. Raises rate limit 60 → 5000 req/hour **and** unlocks the accurate full-year contribution heatmap (see below). A classic PAT with `repo` scope or a fine-grained read-only token is plenty. |
| `WAKATIME_API_KEY` | From WakaTime → Settings → API Key |
| `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` / `SPOTIFY_REFRESH_TOKEN` | See below |
| `STRAVA_CLIENT_ID` / `STRAVA_CLIENT_SECRET` / `STRAVA_REFRESH_TOKEN` | OAuth app with scope `activity:read` |

### Getting a Spotify refresh token

1. Create an app at <https://developer.spotify.com/dashboard>; add
   `http://localhost:8888/callback` as a redirect URI.
2. Authorize with scope `user-read-currently-playing user-read-recently-played`:
   `https://accounts.spotify.com/authorize?client_id=<ID>&response_type=code&redirect_uri=http://localhost:8888/callback&scope=user-read-currently-playing%20user-read-recently-played`
3. Exchange the `code` you get back for tokens:
   ```bash
   curl -X POST https://accounts.spotify.com/api/token \
     -u "$CLIENT_ID:$CLIENT_SECRET" \
     -d grant_type=authorization_code \
     -d code=<CODE> \
     -d redirect_uri=http://localhost:8888/callback
   ```
4. Put the `refresh_token` from the response into `.env`. The backend swaps it
   for a short-lived access token on every fetch.

## Adding a connector

Subclass `Connector` in `backend/app/connectors/`, implement `enabled` and
`async fetch(client) -> SourceResult`, and add it to `build_connectors()` in
`app/main.py`. Caching, scheduling, and degradation are handled for you.

## Project layout

```
docker-compose.yml     # backend + nginx frontend
embed-example.html     # demo page for the now-playing widget
backend/
  Dockerfile
  app/
    main.py            # FastAPI app, routes, lifespan (scheduler + client)
    config.py          # env-driven settings
    store.py           # in-memory per-source cache
    scheduler.py       # refresh + graceful-degradation rules
    models.py          # Pydantic response schemas (drive OpenAPI docs)
    connectors/        # github, spotify, strava, wakatime + base class
    static/
      now-playing.js   # embeddable widget, served at /static/now-playing.js
frontend/
  Dockerfile
  nginx.conf           # serves the SPA, proxies /api -> backend
  src/
    App.jsx            # polling + layout
    api.js             # fetch helpers
    components/        # NowPlaying, GitHub/WakaTime/Strava cards, Heatmap, ...
```
