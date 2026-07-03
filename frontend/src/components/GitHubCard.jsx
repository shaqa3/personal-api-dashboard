import Card from "./Card.jsx";

export default function GitHubCard({ source }) {
  const d = source?.data ?? {};
  const commit = d.latest_commit;

  return (
    <Card title="GitHub" icon="◆" source={source}>
      <div className="gh-head">
        {d.avatar && <img className="gh-avatar" src={d.avatar} alt="" />}
        <div>
          <a className="gh-name" href={d.profile_url} target="_blank" rel="noreferrer">
            {d.name || d.username}
          </a>
          {d.bio && <p className="gh-bio">{d.bio}</p>}
        </div>
      </div>

      <div className="stat-row">
        <Stat label="repos" value={d.public_repos} />
        <Stat label="followers" value={d.followers} />
        <Stat label="recent commits" value={d.recent_push_commits} />
      </div>

      {commit && (
        <div className="latest-commit">
          <span className="lc-label">latest push</span>
          <span className="lc-msg">{commit.message}</span>
          <span className="lc-repo">{commit.repo}</span>
        </div>
      )}
    </Card>
  );
}

function Stat({ label, value }) {
  return (
    <div className="stat">
      <span className="stat-value">{value ?? "—"}</span>
      <span className="stat-label">{label}</span>
    </div>
  );
}
