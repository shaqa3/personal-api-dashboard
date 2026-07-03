/**
 * Personal API — embeddable "now playing" widget.
 *
 * Drop this into any page (e.g. your portfolio hero):
 *
 *   <div id="now-playing"></div>
 *   <script src="https://YOUR-API/static/now-playing.js"
 *           data-api="https://YOUR-API"
 *           data-target="#now-playing"></script>
 *
 * Self-contained: no dependencies, scoped styles, polls every 20s.
 */
(function () {
  var script = document.currentScript;
  var api = (script && script.getAttribute("data-api")) || "";
  var targetSel = (script && script.getAttribute("data-target")) || "#now-playing";
  var interval = parseInt((script && script.getAttribute("data-interval")) || "20000", 10);

  var STYLE_ID = "pa-nowplaying-style";
  if (!document.getElementById(STYLE_ID)) {
    var css = [
      ".pa-np{display:inline-flex;align-items:center;gap:12px;padding:10px 14px 10px 10px;",
      "border-radius:14px;background:#12151d;border:1px solid #232838;color:#e7ebf3;",
      "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;",
      "text-decoration:none;line-height:1.2;max-width:320px}",
      ".pa-np:hover{border-color:#33405f}",
      ".pa-np img,.pa-np .pa-art{width:48px;height:48px;border-radius:8px;object-fit:cover;flex:0 0 auto}",
      ".pa-np .pa-art{background:linear-gradient(135deg,#1b2030,#262c40)}",
      ".pa-np .pa-meta{display:flex;flex-direction:column;min-width:0}",
      ".pa-np .pa-eyebrow{font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:#38d39f;",
      "display:flex;align-items:center;gap:6px}",
      ".pa-np .pa-track{font-weight:600;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}",
      ".pa-np .pa-artist{font-size:12px;color:#8b93a7;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}",
      ".pa-eq{display:inline-flex;align-items:flex-end;gap:2px;height:10px}",
      ".pa-eq i{width:3px;background:#38d39f;border-radius:2px;animation:pa-eq .9s ease-in-out infinite}",
      ".pa-eq i:nth-child(1){height:4px;animation-delay:-.2s}",
      ".pa-eq i:nth-child(2){height:10px;animation-delay:-.5s}",
      ".pa-eq i:nth-child(3){height:6px;animation-delay:-.1s}",
      "@keyframes pa-eq{0%,100%{transform:scaleY(.4)}50%{transform:scaleY(1)}}",
    ].join("");
    var style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = css;
    document.head.appendChild(style);
  }

  function esc(s) {
    var d = document.createElement("div");
    d.textContent = s == null ? "" : String(s);
    return d.innerHTML;
  }

  function render(el, d) {
    if (!d || d.status === "disabled" || !d.track) {
      el.innerHTML =
        '<span class="pa-np"><span class="pa-art"></span><span class="pa-meta">' +
        '<span class="pa-eyebrow">now playing</span>' +
        '<span class="pa-track">Nothing playing</span></span></span>';
      return;
    }
    var eyebrow = d.is_playing
      ? '<span class="pa-eq"><i></i><i></i><i></i></span>now playing'
      : "last played";
    var art = d.album_art
      ? '<img src="' + esc(d.album_art) + '" alt="">'
      : '<span class="pa-art"></span>';
    el.innerHTML =
      '<a class="pa-np" href="' + esc(d.url || "#") + '" target="_blank" rel="noreferrer">' +
      art +
      '<span class="pa-meta"><span class="pa-eyebrow">' + eyebrow + "</span>" +
      '<span class="pa-track">' + esc(d.track) + "</span>" +
      '<span class="pa-artist">' + esc(d.artist) + "</span></span></a>";
  }

  function tick(el) {
    fetch(api + "/api/now-playing")
      .then(function (r) { return r.json(); })
      .then(function (d) { render(el, d); })
      .catch(function () { /* keep last render on transient errors */ });
  }

  function init() {
    var el = document.querySelector(targetSel);
    if (!el) return;
    tick(el);
    setInterval(function () { tick(el); }, interval);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
