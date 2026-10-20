// Small SVG line charts with a cursor, in the style of the reference timeline.
const NS = 'http://www.w3.org/2000/svg';

export function lineChart(svg, { xs, ys, xmin, xmax, ymin, ymax, xticks = [], yticks = [], fill = true, color = '#b3261e', dashedAfter = null }) {
  const W = svg.clientWidth || 300, H = svg.clientHeight || 108;
  const L = 30, R = 6, T = 8, B = 16;
  const sx = (x) => L + ((x - xmin) / (xmax - xmin)) * (W - L - R);
  const sy = (y) => T + (1 - (y - ymin) / (ymax - ymin)) * (H - T - B);
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  svg.innerHTML = '';
  const el = (tag, attrs, parent = svg) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); parent.appendChild(e); return e; };
  for (const t of yticks) {
    el('line', { x1: L, x2: W - R, y1: sy(t), y2: sy(t), stroke: '#e3dbcd', 'stroke-width': 1 });
    el('text', { x: L - 4, y: sy(t) + 3, 'text-anchor': 'end' }).textContent = t;
  }
  for (const [x, label] of xticks) el('text', { x: sx(x), y: H - 3, 'text-anchor': 'middle' }).textContent = label;
  const pts = xs.map((x, i) => `${sx(x).toFixed(1)},${sy(ys[i]).toFixed(1)}`);
  if (fill) el('path', { d: `M${sx(xs[0])},${sy(ymin)} L${pts.join(' L')} L${sx(xs.at(-1))},${sy(ymin)} Z`, fill: color, 'fill-opacity': 0.12 });
  el('polyline', { points: pts.join(' '), fill: 'none', stroke: color, 'stroke-width': 1.6 });
  const cur = el('g', {});
  el('line', { y1: T, y2: H - B, stroke: '#2a2723', 'stroke-width': 1 }, cur);
  const dot = el('circle', { r: 3.5, fill: '#fff', stroke: '#2a2723', 'stroke-width': 1.5 }, cur);
  return (x, y) => {
    cur.setAttribute('transform', `translate(${sx(x) - 0},0)`);
    cur.firstChild.setAttribute('x1', 0); cur.firstChild.setAttribute('x2', 0);
    dot.setAttribute('cx', 0); dot.setAttribute('cy', sy(y));
  };
}
