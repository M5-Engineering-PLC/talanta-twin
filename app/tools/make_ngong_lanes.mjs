import { readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const plan = JSON.parse(await readFile(resolve(ROOT, 'blender/data/site_plan.json'))).ngong;
const roads = JSON.parse(await readFile(resolve(ROOT, 'blender/data/road_lines.json')));
const ledger = (await readFile(resolve(ROOT, 'gis/parameter_ledger.csv'), 'utf8')).split('\n');
const width = Number(ledger.find((r) => r.startsWith('ngong.lane_w,')).split(',')[1]);
assert.equal(width, plan.lane_w, 'Mesh ledger width differs from site plan');
const distance = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
const normal = (pts, i) => {
  const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)];
  const d = distance(a, b); return [-(b[1] - a[1]) / d, (b[0] - a[0]) / d];
};
const offset = (pts, d) => pts.map((p, i) => { const n = normal(pts, i); return [p[0] + n[0] * d, p[1] + n[1] * d]; });
const length = (pts) => pts.slice(1).reduce((s, p, i) => s + distance(p, pts[i]), 0);
const dot = (a, b) => a[0] * b[0] + a[1] * b[1];
function segmentDistance(p, a, b) {
  const v = [b[0] - a[0], b[1] - a[1]], t = Math.max(0, Math.min(1, dot([p[0] - a[0], p[1] - a[1]], v) / (dot(v, v) || 1)));
  return distance(p, [a[0] + v[0] * t, a[1] + v[1] * t]);
}
function extend(pts) {
  const end = (a, b) => { const d = distance(a, b); return [a[0] + (a[0] - b[0]) / d * 3000, a[1] + (a[1] - b[1]) / d * 3000]; };
  return [end(pts[0], pts[1]), ...pts, end(pts.at(-1), pts.at(-2))];
}
/** Clip a horizontal polyline to the 1500 m disc. */
function clip(pts) {
  const parts = []; let part = [];
  for (let i = 1; i < pts.length; i++) {
    const a = pts[i - 1], b = pts[i], v = [b[0] - a[0], b[1] - a[1]];
    const A = dot(v, v), B = 2 * dot(a, v), C = dot(a, a) - 1500 ** 2, disc = B * B - 4 * A * C;
    if (A < 1e-12 || disc < 0) { if (part.length > 1) parts.push(part); part = []; continue; }
    const lo = Math.max(0, (-B - Math.sqrt(disc)) / (2 * A)), hi = Math.min(1, (-B + Math.sqrt(disc)) / (2 * A));
    if (lo > hi) { if (part.length > 1) parts.push(part); part = []; continue; }
    const at = (t) => [a[0] + v[0] * t, a[1] + v[1] * t];
    if (!part.length || distance(part.at(-1), at(lo)) > .02) { if (part.length > 1) parts.push(part); part = [at(lo)]; }
    if (distance(part.at(-1), at(hi)) > .001) part.push(at(hi));
    if (hi < 1) { if (part.length > 1) parts.push(part); part = []; }
  }
  if (part.length > 1) parts.push(part);
  return parts.filter((p) => length(p) > 30);
}
function join(items) {
  const pending = items.map((x) => x.pts), result = [];
  while (pending.length) {
    let p = pending.pop(), changed = true;
    while (changed) {
      changed = false;
      for (let i = 0; i < pending.length && !changed; i++) for (const reverse of [false, true]) {
        const q = reverse ? [...pending[i]].reverse() : pending[i];
        if (distance(p.at(-1), q[0]) < 1.5) { p = [...p, ...q.slice(1)]; pending.splice(i, 1); changed = true; break; }
        if (distance(q.at(-1), p[0]) < 1.5) { p = [...q.slice(0, -1), ...p]; pending.splice(i, 1); changed = true; break; }
      }
    }
    result.push(p);
  }
  return result;
}
const lane = (pts, off, reverse, index, mesh = false) => {
  let points = offset(pts, off);
  if (mesh) points = extend(points);
  if (reverse) points.reverse();
  return { claim: 'derived layout; estimated dimensions; Visualization', direction: reverse ? 'reverse' : 'forward', keepLeft: true, indexFromMedian: index, leftLane: index === (mesh ? plan.lanes_per_dir - 1 : 0), offset: off, width: mesh ? width : 3.5, app: points, blender: points.map(([x, z]) => [x, -z]) };
};
const ngong = { name: 'Ngong Road', class: 'secondary', divided: true, centralReserve: plan.median_w, lanes: [] };
for (const side of [1, -1]) for (let k = 0; k < plan.lanes_per_dir; k++) {
  // App z points south, so the mesh positive normal is right of forward travel.
  ngong.lanes.push(lane(plan.mid, side * (plan.median_w / 2 + (k + .5) * width), side > 0, k, true));
}
const groups = new Map();
for (const r of roads.filter((r) => r.name !== 'Ngong Road')) {
  const key = r.name || `unnamed-${roads.indexOf(r)}`;
  if (!groups.has(key)) groups.set(key, []);
  groups.get(key).push(r);
}
const other = []; let suppressed = 0;
for (const [name, items] of groups) {
  const accepted = [];
  for (const p of join(items).sort((a, b) => length(b) - length(a))) {
    // Source strips direction tags. Suppress a parallel mapped carriageway rather than duplicate both directions.
    const twin = accepted.some((q) => {
      const aligned = Math.abs(dot(normal(p, Math.floor(p.length / 2)), normal(q, Math.floor(q.length / 2)))) > .95;
      return aligned && p.filter((a) => Math.min(...q.slice(1).map((b, i) => segmentDistance(a, q[i], b))) < 30).length / p.length > .8;
    });
    if (twin) { suppressed++; continue; }
    accepted.push(p);
    other.push({ name: items[0].name || name, class: items[0].class, divided: false, lanes: [lane(p, -1.75, false, 0), lane(p, 1.75, true, 0)] });
  }
}
const output = { claim: 'derived lane layout; estimated dimensions; Visualization', source: 'blender/data/site_plan.json ngong.mid; gis/parameter_ledger.csv ngong.lane_w', units: 'metres', coordinates: { app: 'x east, z south', blender: 'x east, y north', origin: 'pitch centre' }, layout: { lanesPerDirection: plan.lanes_per_dir, laneWidth: width, medianWidth: plan.median_w, meshPointCount: plan.mid.length, boundaryExtension: 'estimated tangent continuation to 1500 m disc' }, suppressedParallelChains: suppressed, roads: [ngong, ...other] };
if (process.argv[1] === fileURLToPath(import.meta.url) && process.argv.includes('--check')) {
  const saved = JSON.parse(await readFile(resolve(ROOT, 'blender/data/ngong_lanes.json')));
  assert.deepEqual(saved, output, 'Regenerate shared lanes');
  let error = 0, left = Infinity, separation = Infinity;
  const ng = saved.roads[0];
  for (const l of ng.lanes) {
    const pts = (l.direction === 'reverse' ? [...l.app].reverse() : l.app).slice(1, -1);
    for (let i = 0; i < pts.length; i++) {
      const n = normal(plan.mid, i), delta = [pts[i][0] - plan.mid[i][0], pts[i][1] - plan.mid[i][1]];
      error = Math.max(error, Math.abs(dot(delta, n) - l.offset));
      left = Math.min(left, dot(delta, n) * (l.direction === 'forward' ? -1 : 1));
      const next = l.blender[Math.min(l.blender.length - 1, (l.direction === 'forward' ? i + 1 : l.app.length - i - 2) + 1)];
      const here = l.blender[l.direction === 'forward' ? i + 1 : l.app.length - i - 2];
      const radial = [here[0] - plan.mid[i][0], here[1] + plan.mid[i][1]];
      assert((next[0] - here[0]) * radial[1] - (next[1] - here[1]) * radial[0] > 0, 'Physical left-hand side failed');
      assert.deepEqual(l.blender[l.direction === 'forward' ? i + 1 : l.app.length - i - 2], [pts[i][0], -pts[i][1]]);
    }
  }
  for (let i = 0; i < ng.lanes.length; i++) for (let j = i + 1; j < ng.lanes.length; j++) {
    const a = ng.lanes[i], b = ng.lanes[j];
    separation = Math.min(separation, Math.abs(a.offset - b.offset));
    const pa = a.direction === 'forward' ? a.app : [...a.app].reverse(), pb = b.direction === 'forward' ? b.app : [...b.app].reverse();
    let min = Infinity;
    for (const p of pa.slice(1, -1)) for (let k = 2; k < pb.length - 1; k++) min = Math.min(min, segmentDistance(p, pb[k - 1], pb[k]));
    assert(min > 3, 'Lane center polylines overlap');
  }
  assert(error < .3 && left > plan.median_w / 2 && separation >= width - 1e-9);
  for (const road of saved.roads) for (const l of road.lanes) assert(l.keepLeft && l.offset * (l.direction === 'forward' ? -1 : 1) > 0);
  const web = JSON.parse(await readFile(resolve(ROOT, 'app/public/data/traffic_lines.json'))).roads.find((r) => r.name === 'Ngong Road');
  assert.equal(web.lanes.length, ng.lanes.length);
  for (const raw of ng.lanes) {
    const actual = web.lanes.find((l) => l.direction === raw.direction && l.indexFromMedian === raw.indexFromMedian);
    const expected = clip(raw.app)[0];
    assert.equal(actual.points.length, expected.length);
    actual.points.forEach(([x, , z], i) => assert(distance([x, z], expected[i]) < .002, 'Web export differs from shared center'));
    for (const [x, , z] of [actual.points[0], actual.points.at(-1)]) assert(Math.abs(Math.hypot(x, z) - 1500) < .002);
  }
  console.log('PASS web export: 8 lanes match shared centers within 0.002 m; 16 endpoints on the 1500 m boundary.');
  const clipped = saved.roads.flatMap((r) => r.lanes.flatMap((l) => clip(l.app)));
  console.log(`PASS: ${ng.lanes.length} Ngong lanes; maximum mesh center error ${error.toFixed(6)} m; minimum left offset ${left.toFixed(2)} m; separation ${separation.toFixed(2)} m; no overlapping centers; all directions keep-left; ${clipped.length} clipped lane parts.`);
} else if (process.argv[1] === fileURLToPath(import.meta.url)) {
  await writeFile(resolve(ROOT, 'blender/data/ngong_lanes.json'), JSON.stringify(output) + '\n');
  console.log(`Shared source: ${output.roads.length} road chains; ${ngong.lanes.length} Ngong lanes; ${suppressed} parallel chains suppressed.`);
}
export { clip };
