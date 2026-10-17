import { readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const DATA = resolve(ROOT, 'app/public/data');
const manifest = JSON.parse(await readFile(resolve(DATA, 'manifest.json'), 'utf8'));
const source = JSON.parse(await readFile(resolve(ROOT, 'blender/data/road_lines.json'), 'utf8'));
const terrainMeta = manifest.terrain[0];
const terrainBuffer = await readFile(resolve(DATA, terrainMeta.file));
const terrain = Array.from({ length: terrainBuffer.length / 4 }, (_, i) => terrainBuffer.readFloatLE(i * 4));
const PAD = manifest.features.site_pad_y;
const LIMIT = 1500;
const ALLOWED = new Set(['trunk', 'primary', 'secondary', 'tertiary']);
const round = (n) => Math.round(n * 100) / 100;
const lengthOf = (pts) => pts.slice(1).reduce((sum, p, i) => sum + Math.hypot(p[0] - pts[i][0], p[1] - pts[i][1]), 0);

function terrainAt(x, z) {
  const { nx, nz, x0, z0, dx, dz } = terrainMeta;
  const fc = (x - x0) / dx - 0.5, fr = (z - z0) / dz - 0.5;
  const c = Math.max(0, Math.min(nx - 2, Math.floor(fc))), r = Math.max(0, Math.min(nz - 2, Math.floor(fr)));
  const tx = Math.max(0, Math.min(1, fc - c)), tz = Math.max(0, Math.min(1, fr - r));
  const at = (rr, cc) => terrain[rr * nx + cc];
  const h = (at(r, c) * (1 - tx) + at(r, c + 1) * tx) * (1 - tz) + (at(r + 1, c) * (1 - tx) + at(r + 1, c + 1) * tx) * tz;
  return h - (x * x + z * z) / (2 * 6371000);
}

function clipLine(pts) {
  const result = [];
  let current = [];
  for (let i = 1; i < pts.length; i++) {
    const a = pts[i - 1], b = pts[i];
    const dx = b[0] - a[0], dz = b[1] - a[1];
    const A = dx * dx + dz * dz, B = 2 * (a[0] * dx + a[1] * dz), C = a[0] ** 2 + a[1] ** 2 - LIMIT ** 2;
    let lo = 0, hi = 1;
    if (A > 0) {
      const disc = B * B - 4 * A * C;
      if (disc < 0) { if (C > 0 && B > 0) { if (current.length > 1) result.push(current); current = []; } continue; }
      const r0 = (-B - Math.sqrt(disc)) / (2 * A), r1 = (-B + Math.sqrt(disc)) / (2 * A);
      lo = Math.max(0, r0); hi = Math.min(1, r1);
    }
    if (lo > hi) { if (current.length > 1) result.push(current); current = []; continue; }
    const p0 = [a[0] + dx * lo, a[1] + dz * lo], p1 = [a[0] + dx * hi, a[1] + dz * hi];
    if (!current.length || Math.hypot(current.at(-1)[0] - p0[0], current.at(-1)[1] - p0[1]) > 0.02) {
      if (current.length > 1) result.push(current);
      current = [p0];
    }
    if (Math.hypot(current.at(-1)[0] - p1[0], current.at(-1)[1] - p1[1]) > 0.02) current.push(p1);
    if (hi < 1) { if (current.length > 1) result.push(current); current = []; }
  }
  if (current.length > 1) result.push(current);
  return result.filter((p) => lengthOf(p) >= 20);
}

function offsetLine(pts, offset) {
  return pts.map((p, i) => {
    const before = pts[Math.max(0, i - 1)], after = pts[Math.min(pts.length - 1, i + 1)];
    const dx = after[0] - before[0], dz = after[1] - before[1], l = Math.hypot(dx, dz) || 1;
    return [p[0] + (dz / l) * offset, p[1] - (dx / l) * offset];
  });
}

function withHeight(pts) {
  return pts.map(([x, z]) => [round(x), round(terrainAt(x, z)), round(z)]);
}

function joinSegments(segments) {
  const pending = segments.map((s) => s.pts.map((p) => [p[0], p[1]]));
  const chains = [];
  while (pending.length) {
    const chain = pending.pop();
    let changed = true;
    while (changed) {
      changed = false;
      for (const end of ['start', 'finish']) {
        const atStart = end === 'start';
        const node = atStart ? chain[0] : chain.at(-1);
        const neighbor = atStart ? chain[1] : chain.at(-2);
        const outward = atStart ? [node[0] - neighbor[0], node[1] - neighbor[1]] : [node[0] - neighbor[0], node[1] - neighbor[1]];
        const ol = Math.hypot(...outward) || 1;
        let best = null;
        pending.forEach((candidate, index) => {
          for (const reverse of [false, true]) {
            const ordered = reverse ? [...candidate].reverse() : candidate;
            const attach = ordered[0], next = ordered[1];
            const gap = Math.hypot(attach[0] - node[0], attach[1] - node[1]);
            if (gap > 1.5) continue;
            const v = [next[0] - attach[0], next[1] - attach[1]], vl = Math.hypot(...v) || 1;
            const alignment = (outward[0] * v[0] + outward[1] * v[1]) / (ol * vl);
            if (alignment < 0.5 || (best && alignment <= best.alignment)) continue;
            best = { index, ordered, alignment };
          }
        });
        if (!best) continue;
        pending.splice(best.index, 1);
        if (atStart) chain.unshift(...best.ordered.slice(1).reverse());
        else chain.push(...best.ordered.slice(1));
        changed = true;
        break;
      }
    }
    chains.push(chain);
  }
  return chains;
}

const roads = [];
const namedGroups = new Map();
for (const item of source) {
  if (!ALLOWED.has(item.class)) continue;
  const key = item.name || `unnamed-${source.indexOf(item)}`;
  if (!namedGroups.has(key)) namedGroups.set(key, []);
  namedGroups.get(key).push(item);
}
for (const [key, group] of namedGroups) {
  const item = group[0];
  const name = item.name || `${item.class} road`;
  const ngong = name.toLowerCase() === 'ngong road';
  for (const joined of joinSegments(group)) for (const center of clipLine(joined)) {
    const lanes = [];
    if (ngong) {
      for (const [direction, side] of [['outbound', 1], ['inbound', -1]]) {
        for (const offset of [3.75, 7.25]) {
          const shifted = offsetLine(center, offset * side);
          lanes.push({ direction, width: 3.5, points: withHeight(direction === 'outbound' ? shifted : shifted.reverse()) });
        }
      }
    } else {
      const out = offsetLine(center, 1.75), back = offsetLine(center, -1.75).reverse();
      lanes.push({ direction: 'forward', width: 3.5, points: withHeight(out) });
      lanes.push({ direction: 'reverse', width: 3.5, points: withHeight(back) });
    }
    roads.push({ name, class: item.class, divided: ngong, ...(ngong ? { centralReserve: 4 } : {}), lanes });
  }
}

const output = {
  claim: 'Visualization',
  units: 'metres',
  coordinates: { x: 'east', y: 'up', z: 'south', origin: 'pitch centre', padY: PAD },
  roads,
};
await writeFile(resolve(DATA, 'traffic_lines.json'), `${JSON.stringify(output)}\n`);
const laneCount = roads.reduce((n, road) => n + road.lanes.length, 0);
const totalLength = roads.reduce((n, road) => n + road.lanes.reduce((m, lane) => m + lengthOf(lane.points.map(([x, , z]) => [x, z])), 0), 0);
console.log(`Wrote ${roads.length} road sections and ${laneCount} lane polylines; ${totalLength.toFixed(1)} m total. Ngong Road has two 3.5 m lanes each way and a 4 m reserve. PAD=${PAD} m.`);
