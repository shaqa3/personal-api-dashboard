import { useCallback, useEffect, useState } from "react";
import { fetchStats, fetchNowPlaying } from "./api.js";
import NowPlaying from "./components/NowPlaying.jsx";
import GitHubCard from "./components/GitHubCard.jsx";
import WakaTimeCard from "./components/WakaTimeCard.jsx";
import StravaCard from "./components/StravaCard.jsx";
import Heatmap from "./components/Heatmap.jsx";
import StatusBar from "./components/StatusBar.jsx";

const STATS_INTERVAL = 60_000;
const NOW_PLAYING_INTERVAL = 20_000;

export default function App() {
  const [stats, setStats] = useState(null);
  const [nowPlaying, setNowPlaying] = useState(null);
  const [error, setError] = useState(null);

  const loadStats = useCallback(async () => {
    try {
      setStats(await fetchStats());
      setError(null);
    } catch (e) {
      setError(e.message);
    }
  }, []);

  const loadNowPlaying = useCallback(async () => {
    try {
      setNowPlaying(await fetchNowPlaying());
    } catch {
      /* now-playing is best-effort; the poll will retry */
    }
  }, []);

  useEffect(() => {
    loadStats();
    loadNowPlaying();
    const a = setInterval(loadStats, STATS_INTERVAL);
    const b = setInterval(loadNowPlaying, NOW_PLAYING_INTERVAL);
    return () => {
      clearInterval(a);
      clearInterval(b);
    };
  }, [loadStats, loadNowPlaying]);

  const sources = stats?.sources ?? {};
  const github = sources.github;
  const wakatime = sources.wakatime;
  const strava = sources.strava;

  return (
    <div className="page">
      <header className="hero">
        <div className="hero-heading">
          <h1>Personal API</h1>
          <p className="subtitle">
            My data — GitHub, Spotify &amp; WakaTime — behind one cached endpoint.
          </p>
        </div>
        <NowPlaying source={sources.spotify} live={nowPlaying} />
      </header>

      {error && (
        <div className="banner error">Couldn’t reach the API: {error}</div>
      )}

      <StatusBar sources={sources} generatedAt={stats?.generated_at} />

      <main className="grid">
        <GitHubCard source={github} />
        <WakaTimeCard source={wakatime} />
        <StravaCard source={strava} />
        <Heatmap source={github} />
      </main>

      <footer className="footer">
        <a href="/docs">API docs</a>
        <span>·</span>
        <a href="/api/stats">/api/stats</a>
        <span>·</span>
        <span>refreshes on a schedule, cached server-side</span>
      </footer>
    </div>
  );
}
