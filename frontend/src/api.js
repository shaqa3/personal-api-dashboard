// Small fetch helpers. Same-origin in prod; proxied to :8000 in dev.
const BASE = import.meta.env.VITE_API_BASE ?? "";

export async function fetchStats() {
  const res = await fetch(`${BASE}/api/stats`);
  if (!res.ok) throw new Error(`stats ${res.status}`);
  return res.json();
}

export async function fetchNowPlaying() {
  const res = await fetch(`${BASE}/api/now-playing`);
  if (!res.ok) throw new Error(`now-playing ${res.status}`);
  return res.json();
}
