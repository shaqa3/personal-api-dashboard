const LABELS = {
  ok: "live",
  degraded: "cached",
  down: "down",
  disabled: "off",
};

function relative(seconds) {
  if (seconds == null) return "—";
  if (seconds < 60) return `${Math.round(seconds)}s ago`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m ago`;
  return `${Math.round(seconds / 3600)}h ago`;
}

export default function StatusBar({ sources, generatedAt }) {
  const entries = Object.values(sources);
  return (
    <div className="statusbar">
      <div className="pills">
        {entries.map((s) => (
          <span key={s.source} className={`pill ${s.status}`} title={s.error || ""}>
            <span className="dot" />
            {s.source}
            <span className="pill-state">{LABELS[s.status] ?? s.status}</span>
            <span className="pill-age">{relative(s.age_seconds)}</span>
          </span>
        ))}
        {entries.length === 0 && <span className="pill loading">loading…</span>}
      </div>
    </div>
  );
}
