import { clip } from './make_ngong_lanes.mjs';
import { readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const DATA = resolve(ROOT, 'app/public/data');
const manifest = JSON.parse(await readFile(resolve(DATA, 'manifest.json'), 'utf8'));
const source = JSON.parse(await readFile(resolve(ROOT, 'blender/data/ngong_lanes.json'), 'utf8'));
const terrainMeta = manifest.terrain[0];
const terrainBuffer = await readFile(resolve(DATA, terrainMeta.file));
const terrain = Array.from({ length: terrainBuffer.length / 4 }, (_, i) => terrainBuffer.readFloatLE(i * 4));
const round = (n) => Math.round(n * 1000) / 1000;
function terrainAt(x, z) {
  const { nx, nz, x0, z0, dx, dz } = terrainMeta;
  const fc = (x - x0) / dx - 0.5, fr = (z - z0) / dz - 0.5;
  const c = Math.max(0, Math.min(nx - 2, Math.floor(fc))), r = Math.max(0, Math.min(nz - 2, Math.floor(fr)));
  const tx = Math.max(0, Math.min(1, fc - c)), tz = Math.max(0, Math.min(1, fr - r));
  const at = (rr, cc) => terrain[rr * nx + cc];
  const h = (at(r, c) * (1 - tx) + at(r, c + 1) * tx) * (1 - tz) + (at(r + 1, c) * (1 - tx) + at(r + 1, c + 1) * tx) * tz;
  return h - (x * x + z * z) / (2 * 6371000);
}

const roads = source.roads.map((road) => ({ ...road, lanes: road.lanes.flatMap((lane) => clip(lane.app).map((points) => ({
  direction: lane.direction, keepLeft: lane.keepLeft, leftLane: lane.leftLane, indexFromMedian: lane.indexFromMedian,
  width: lane.width, claim: lane.claim, boundaryEntry: Math.abs(Math.hypot(...points[0]) - 1500) < .1,
  boundaryExit: Math.abs(Math.hypot(...points.at(-1)) - 1500) < .1,
  points: points.map(([x, z]) => [round(x), round(terrainAt(x, z)), round(z)]),
}))) })).filter((r) => r.lanes.some((l) => l.direction === 'forward') && r.lanes.some((l) => l.direction === 'reverse'));
const output = { claim: 'Visualization', layoutClaim: source.claim, units: 'metres', coordinates: { x: 'east', y: 'up', z: 'south', origin: 'pitch centre', padY: manifest.features.site_pad_y }, roads };
await writeFile(resolve(DATA, 'traffic_lines.json'), JSON.stringify(output) + '\n');
console.log(`Traffic: ${roads.length} road sections; ${roads.reduce((s, r) => s + r.lanes.length, 0)} lanes; Ngong ${source.layout.lanesPerDirection} x ${source.layout.laneWidth} m each way; median ${source.layout.medianWidth} m.`);
