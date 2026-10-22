import { BOWL_EST } from '../world/bowl.js';
import { rayRadius, roundedRect } from '../world/geom.js';

// Pure reproduction of bowl.js seat places, including its metre-based aisle rule.
// Blender can replace this result with [{ x, y, z, facing_deg, tier, row }].
export function generateSeats(features, estimate = BOWL_EST) {
  const E = estimate, N = E.N;
  const inner = roundedRect(E.seatStart.halfLong, E.seatStart.halfWide, E.seatStart.r, features.pitch_bearing_deg);
  const dirs = Array.from({ length: N + 1 }, (_, i) => [Math.cos(i / N * Math.PI * 2), Math.sin(i / N * Math.PI * 2)]);
  const rIn = dirs.map(([x, z]) => rayRadius(inner, x, z));
  const outer = dirs.map(([x, z]) => rayRadius(features.bowl_outer, x, z));
  const rBack = outer.map((_, i) => {
    let sum = 0;
    for (let k = -3; k <= 3; k++) sum += outer[(i + k + N) % N];
    return sum / 7 - E.backSetback;
  });
  rBack[N] = rBack[0];
  const seats = [];
  for (let tier = 0; tier < E.tiers.length; tier++) {
    const T = E.tiers[tier];
    for (let row = 0; row < T.rows; row++) {
      const t = T.t0 + (T.t1 - T.t0) * (row + 0.5) / T.rows;
      const points = dirs.map(([x, z], i) => {
        const r = rIn[i] + (rBack[i] - rIn[i]) * t;
        return [x * r, z * r];
      });
      const lengths = points.slice(1).map((p, i) => Math.hypot(p[0] - points[i][0], p[1] - points[i][1]));
      const perimeter = lengths.reduce((a, b) => a + b, 0);
      let segment = 0, acc = 0;
      for (let d = E.seatPitch / 2; d < perimeter; d += E.seatPitch) {
        if (d % E.aisleEvery < E.aisleW) continue;
        while (acc + lengths[segment] < d) acc += lengths[segment++];
        const f = (d - acc) / lengths[segment];
        const x = points[segment][0] * (1 - f) + points[segment + 1][0] * f;
        const z = points[segment][1] * (1 - f) + points[segment + 1][1] * f;
        seats.push({ x, y: T.y0 + (T.y1 - T.y0) * row / T.rows, z,
          facing_deg: (-Math.atan2(z, x) - Math.PI / 2) * 180 / Math.PI, tier, row });
      }
    }
  }
  return seats;
}
