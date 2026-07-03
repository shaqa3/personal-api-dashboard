import Card from "./Card.jsx";

const DAY = 86_400_000;

function isoDate(d) {
  return d.toISOString().slice(0, 10);
}

// Build a `weeks`-wide grid ending today. Columns are weeks (Sun-started),
// rows are weekdays. Returns { columns, max }.
function buildGrid(heatmap, weeks) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  // Walk back to the Sunday that starts the earliest visible week.
  const start = new Date(today.getTime() - (weeks * 7 - 1) * DAY);
  start.setDate(start.getDate() - start.getDay());

  const columns = [];
  let max = 0;
  let cursor = new Date(start);
  for (let w = 0; w < weeks + 1; w++) {
    const col = [];
    for (let dow = 0; dow < 7; dow++) {
      const key = isoDate(cursor);
      const count = cursor <= today ? heatmap[key] || 0 : -1; // -1 = future
      if (count > max) max = count;
      col.push({ key, count });
      cursor = new Date(cursor.getTime() + DAY);
    }
    columns.push(col);
  }
  return { columns, max };
}

function level(count, max) {
  if (count < 0) return "future";
  if (count === 0) return "l0";
  if (max <= 0) return "l1";
  const r = count / max;
  if (r > 0.66) return "l4";
  if (r > 0.33) return "l3";
  if (r > 0.1) return "l2";
  return "l1";
}

export default function Heatmap({ source }) {
  const data = source?.data ?? {};
  const heatmap = data.heatmap ?? {};
  const isGraphql = data.heatmap_source === "graphql";

  // Full contribution year (53 weeks) with a token; ~90-day window otherwise.
  const weeks = isGraphql ? 53 : 13;
  const { columns, max } = buildGrid(heatmap, weeks);

  const caption = isGraphql
    ? `${data.contributions_last_year ?? 0} contributions in the last year`
    : `${Object.values(heatmap).reduce((a, b) => a + b, 0)} pushes in the last ~90 days`;

  return (
    <Card title="Activity" icon="▦" source={source}>
      <p className="hm-caption">{caption}</p>
      <div className="heatmap">
        {columns.map((col, i) => (
          <div key={i} className="hm-col">
            {col.map((cell) => (
              <div
                key={cell.key}
                className={`hm-cell ${level(cell.count, max)}`}
                title={cell.count >= 0 ? `${cell.key}: ${cell.count}` : ""}
              />
            ))}
          </div>
        ))}
      </div>
      <div className="hm-legend">
        <span>less</span>
        <span className="hm-cell l0" />
        <span className="hm-cell l1" />
        <span className="hm-cell l2" />
        <span className="hm-cell l3" />
        <span className="hm-cell l4" />
        <span>more</span>
      </div>
    </Card>
  );
}
