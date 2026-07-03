import Card from "./Card.jsx";

export default function StravaCard({ source }) {
  const d = source?.data ?? {};
  const runs = d.recent_runs ?? {};
  const rides = d.recent_rides ?? {};

  return (
    <Card title="Strava" icon="●" source={source}>
      <p className="muted" style={{ marginTop: 0, marginBottom: 14 }}>
        last 4 weeks
      </p>
      <div className="strava-rows">
        <ActivityRow icon="🏃" label="Runs" t={runs} />
        <ActivityRow icon="🚴" label="Rides" t={rides} />
      </div>
    </Card>
  );
}

function ActivityRow({ icon, label, t }) {
  return (
    <div className="strava-row">
      <span className="sr-icon">{icon}</span>
      <span className="sr-label">{label}</span>
      <span className="sr-metric">
        <b>{t.distance_km ?? 0}</b> km
      </span>
      <span className="sr-metric">
        <b>{t.count ?? 0}</b> activities
      </span>
      <span className="sr-metric">
        <b>{t.moving_time_hours ?? 0}</b> h
      </span>
    </div>
  );
}
