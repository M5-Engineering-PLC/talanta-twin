import { BOWL_EST as E } from '../world/bowl.js';
import { rayRadius, roundedRect } from '../world/geom.js';
import manifest from '../../public/data/manifest.json' with { type: 'json' };

export function fallbackFacadeLines() {
  const F = manifest.features, N = E.N, tau = Math.PI * 2;
  const raw = Array.from({ length: N }, (_, i) => rayRadius(F.bowl_outer, Math.cos(i / N * tau), Math.sin(i / N * tau)));
  const radii = raw.map((_, i) => Array.from({ length: 7 }, (_, k) => raw[(i + k - 3 + N) % N]).reduce((a, b) => a + b, 0) / 7);
  const opening = roundedRect(E.opening.halfLong, E.opening.halfWide, E.opening.r, F.pitch_bearing_deg, 12);
  const radius = a => { const t = ((a / tau % 1 + 1) % 1) * N, i = Math.floor(t); return radii[i] * (1 - t + i) + radii[(i + 1) % N] * (t - i); };
  const end = 14 + Math.round(16 * 0.45);
  const surface = (a, j) => {
    const f = j / 14, p = (j - 14) / 16 * Math.PI / 2;
    const dr = j <= 14 ? -E.facadeInset * (1 - Math.sin(f * Math.PI / 2)) : -E.shoulderW * (1 - Math.cos(p));
    const y = j <= 14 ? E.plinthH + (E.bulgeY - E.plinthH) * f : E.bulgeY + E.shoulderH * Math.sin(p);
    return [Math.cos(a) * (radius(a) + dr + 1), y, Math.sin(a) * (radius(a) + dr + 1)];
  };
  // First V point on the first shield axis, as in bowl.js.
  const v0 = (-F.pitch_bearing_deg * Math.PI) / 180 - Math.PI / 2;
  const ribs = [];
  for (let k = 0; k < 24; k++) for (const direction of [-1, 1]) {
    // Top and bottom V vertices share the same set of 24 bay angles.
    ribs.push(Array.from({ length: end + 1 }, (_, j) => surface(v0 + (k + direction * j / end) / 24 * tau, end - j)));
  }
  const fascia = Array.from({ length: 121 }, (_, i) => surface(i / 120 * tau, end));
  const hole = Array.from({ length: 121 }, (_, i) => { const a = i / 120 * tau, r = rayRadius(opening, Math.cos(a), Math.sin(a)); return [r * Math.cos(a), E.openingY, r * Math.sin(a)]; });
  const floodlights = Array.from({ length: 24 }, (_, i) => { const p = hole[i * 5]; return { pos: [p[0] * 1.025, p[1] - 2.6, p[2] * 1.025], aim: [p[0] * -0.3, 0, p[2] * -0.3] }; });
  return { frame: 'app x east, y up, z south, m', ribs, fascia, opening: hole, shields: [], floodlights };
}

export function validFacadeLines(data) {
  const point = p => Array.isArray(p) && p.length === 3 && p.every(Number.isFinite);
  const line = p => Array.isArray(p) && p.length >= 2 && p.every(point);
  return data?.frame === 'app x east, y up, z south, m' && Array.isArray(data.ribs) && data.ribs.length > 0 && data.ribs.every(line) && line(data.fascia) && line(data.opening) && Array.isArray(data.floodlights) && data.floodlights.length > 0 && data.floodlights.every(l => point(l.pos) && point(l.aim));
}
export const padY = manifest.features.site_pad_y;
