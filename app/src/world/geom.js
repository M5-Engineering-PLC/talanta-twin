import * as THREE from 'three/webgpu';

// Distance from the origin to a closed polygon along a direction (x, z unit vector).
export function rayRadius(poly, ux, uz) {
  let best = 0;
  for (let i = 0; i < poly.length - 1; i++) {
    const [ax, az] = poly[i], [bx, bz] = poly[i + 1];
    const ex = bx - ax, ez = bz - az;
    const den = ux * ez - uz * ex;
    if (Math.abs(den) < 1e-9) continue;
    const t = (ax * ez - az * ex) / den;
    const s = (ax * uz - az * ux) / den;
    if (t > 0 && s >= 0 && s <= 1) best = Math.max(best, t);
  }
  return best;
}

export function roundedRect(halfLong, halfWide, r, bearingDeg, steps = 8) {
  const pts = [];
  const corners = [[halfWide - r, -(halfLong - r), -Math.PI / 2], [halfWide - r, halfLong - r, 0], [-(halfWide - r), halfLong - r, Math.PI / 2], [-(halfWide - r), -(halfLong - r), Math.PI]];
  for (const [cx, cz, a0] of corners) for (let k = 0; k <= steps; k++) {
    const a = a0 + (k / steps) * Math.PI / 2;
    pts.push([cx + r * Math.cos(a), cz + r * Math.sin(a)]);
  }
  pts.push(pts[0]);
  return rotate(pts, bearingDeg);
}

export function rotate(pts, bearingDeg) {
  const b = (bearingDeg * Math.PI) / 180, c = Math.cos(b), s = Math.sin(b);
  // Clockwise rotation seen from above, with x east and z south.
  return pts.map(([x, z]) => [x * c - z * s, x * s + z * c]);
}

export function centroid(ring) {
  let x = 0, z = 0; const n = ring.length - 1;
  for (let i = 0; i < n; i++) { x += ring[i][0]; z += ring[i][1]; }
  return [x / n, z / n];
}

// Flat ribbon along a polyline for highlights and outlines.
export function ribbon(points, width, y, closed = true, dashed = false) {
  const pos = [], idx = [];
  const P = closed && (points[0][0] !== points.at(-1)[0] || points[0][1] !== points.at(-1)[1]) ? [...points, points[0]] : points;
  let n = 0;
  for (let i = 0; i < P.length - 1; i++) {
    if (dashed && i % 2) continue;
    const [ax, az] = P[i], [bx, bz] = P[i + 1];
    const dx = bx - ax, dz = bz - az, L = Math.hypot(dx, dz) || 1;
    const nx = (-dz / L) * width / 2, nz = (dx / L) * width / 2;
    const ya = typeof y === 'function' ? y(ax, az) : y, yb = typeof y === 'function' ? y(bx, bz) : y;
    pos.push(ax + nx, ya, az + nz, ax - nx, ya, az - nz, bx + nx, yb, bz + nz, bx - nx, yb, bz - nz);
    idx.push(n, n + 2, n + 1, n + 1, n + 2, n + 3);
    n += 4;
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setIndex(idx);
  return g;
}

export function circlePts(cx, cz, r, n = 64) {
  const pts = [];
  for (let i = 0; i <= n; i++) { const a = (i / n) * Math.PI * 2; pts.push([cx + r * Math.cos(a), cz + r * Math.sin(a)]); }
  return pts;
}

export function shapeMesh(ring, y, material, holes = []) {
  const s = new THREE.Shape(ring.map(([x, z]) => new THREE.Vector2(x, -z)));
  for (const h of holes) s.holes.push(new THREE.Path(h.map(([x, z]) => new THREE.Vector2(x, -z))));
  const g = new THREE.ShapeGeometry(s);
  g.rotateX(-Math.PI / 2);
  g.translate(0, y, 0);
  return new THREE.Mesh(g, material);
}
