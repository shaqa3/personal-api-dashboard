// Shared card shell that renders the right empty/degraded/down state so each
// data card can focus on its own layout.
export default function Card({ title, icon, source, children }) {
  const status = source?.status;

  return (
    <section className="card">
      <div className="card-head">
        <h2>
          <span className="card-icon">{icon}</span>
          {title}
        </h2>
        {status && status !== "ok" && (
          <span className={`tag ${status}`}>{status}</span>
        )}
      </div>
      <div className="card-body">
        {!source && <div className="muted">loading…</div>}
        {source && status === "disabled" && (
          <div className="muted">Not connected. Add credentials in <code>.env</code>.</div>
        )}
        {source && status === "down" && (
          <div className="muted">Source is down and no cached data yet.</div>
        )}
        {source && (status === "ok" || status === "degraded") && children}
      </div>
    </section>
  );
}
