// Hero "now playing" widget. Prefers the fast /api/now-playing poll, falls
// back to the spotify entry from /api/stats.
export default function NowPlaying({ source, live }) {
  const data = live && live.status !== "disabled" ? live : source?.data;
  const status = live?.status ?? source?.status;

  if (!status || status === "disabled") {
    return (
      <div className="nowplaying disabled">
        <div className="np-art placeholder" />
        <div className="np-meta">
          <span className="np-eyebrow">now playing</span>
          <span className="np-track">Spotify not connected</span>
          <span className="np-artist">add credentials to light this up</span>
        </div>
      </div>
    );
  }

  if (!data || !data.track) {
    return (
      <div className="nowplaying">
        <div className="np-art placeholder" />
        <div className="np-meta">
          <span className="np-eyebrow">now playing</span>
          <span className="np-track">Nothing playing</span>
        </div>
      </div>
    );
  }

  const playing = data.is_playing;
  return (
    <a
      className="nowplaying"
      href={data.url || "#"}
      target="_blank"
      rel="noreferrer"
    >
      {data.album_art ? (
        <img className="np-art" src={data.album_art} alt={data.album || ""} />
      ) : (
        <div className="np-art placeholder" />
      )}
      <div className="np-meta">
        <span className="np-eyebrow">
          {playing ? (
            <>
              <span className="equalizer">
                <i /><i /><i />
              </span>
              now playing
            </>
          ) : (
            "last played"
          )}
        </span>
        <span className="np-track">{data.track}</span>
        <span className="np-artist">{data.artist}</span>
      </div>
    </a>
  );
}
