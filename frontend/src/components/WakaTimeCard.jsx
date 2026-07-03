import Card from "./Card.jsx";

export default function WakaTimeCard({ source }) {
  const d = source?.data ?? {};
  const languages = d.languages ?? [];

  return (
    <Card title="WakaTime" icon="▲" source={source}>
      <div className="stat-row">
        <div className="stat">
          <span className="stat-value">{d.total ?? "—"}</span>
          <span className="stat-label">{d.range || "last 7 days"}</span>
        </div>
        <div className="stat">
          <span className="stat-value">{d.daily_average ?? "—"}</span>
          <span className="stat-label">daily avg</span>
        </div>
      </div>

      <div className="lang-list">
        {languages.map((l) => (
          <div key={l.name} className="lang-row">
            <span className="lang-name">{l.name}</span>
            <div className="lang-bar">
              <div className="lang-fill" style={{ width: `${l.percent}%` }} />
            </div>
            <span className="lang-pct">{Math.round(l.percent)}%</span>
          </div>
        ))}
        {languages.length === 0 && <div className="muted">No language data.</div>}
      </div>
    </Card>
  );
}
