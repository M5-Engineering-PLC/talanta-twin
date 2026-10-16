import * as THREE from 'three/webgpu';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { rayRadius, roundedRect } from './geom.js';

// Talanta bowl, fully built state.
// Plan: outer edge = OSM building r20072298; roof opening = rounded rectangle sized to the
// Sentinel-2 opening area (about 9,900 m2); pitch zone and bearing = W1b.
// Form (reference frames, JWNowpO44rw 12:36, 26:12, 10:28, 10:04, 10:38): one white shell.
// Louvred facade behind a diamond lattice rolls over a shoulder into a ribbed membrane roof.
// Eight Maasai shields with crossed spears. Green lower tier, red upper tiers, glass VIP band.
// All heights are ESTIMATES (press: 56 m maximum height) until W1b shadows / W3 / drawings.
export const BOWL_EST = {
  seatStart: { halfLong: 59.5, halfWide: 39.5, r: 14 },
  opening: { halfLong: 63, halfWide: 40, r: 20 },
  backSetback: 9,
  plinthH: 5.5, plinthInset: 8, facadeInset: 7,
  bulgeY: 30, shoulderW: 15, shoulderH: 24,
  openingY: 47,
  tiers: [
    { name: 'Lower tier', t0: 0.0, t1: 0.38, y0: 1.2, y1: 12.5, rows: 24, seat: ['#2c7a46', '#2c7a46'] },
    { name: 'Middle tier', t0: 0.45, t1: 0.66, y0: 20.5, y1: 29.5, rows: 13, seat: ['#b0232b', '#b0232b'] },
    { name: 'Upper tier', t0: 0.70, t1: 1.0, y0: 33.0, y1: 46.0, rows: 21, seat: ['#b0232b', '#1c1b1b'] },
  ],
  seatPitch: 0.5, aisleEvery: 16, aisleW: 1.3,
  shields: 8, shieldW: 21, shieldY0: 6.5, shieldY1: 46,
  lattice: 40,
  N: 240,
};

export function buildBowl(features, opts = {}) {
  const E = BOWL_EST, N = E.N;
  const group = new THREE.Group(); group.name = 'bowl';
  const bearing = features.pitch_bearing_deg;
  const seat0 = roundedRect(E.seatStart.halfLong, E.seatStart.halfWide, E.seatStart.r, bearing);
  const open0 = roundedRect(E.opening.halfLong, E.opening.halfWide, E.opening.r, bearing, 12);

  const dirs = [], rIn = [], rOut = [], rOpen = [];
  for (let i = 0; i <= N; i++) {
    const a = (i / N) * Math.PI * 2, ux = Math.cos(a), uz = Math.sin(a);
    dirs.push([ux, uz]);
    rIn.push(rayRadius(seat0, ux, uz));
    rOut.push(rayRadius(features.bowl_outer, ux, uz));
    rOpen.push(rayRadius(open0, ux, uz));
  }
  // Smooth the OSM outline a little: it is a 31-vertex trace.
  const sm = rOut.map((_, i) => { let s = 0; for (let k = -3; k <= 3; k++) s += rOut[(i + k + N) % N]; return s / 7; });
  sm[N] = sm[0]; for (let i = 0; i <= N; i++) rOut[i] = sm[i];
  const rBack = rOut.map((r) => r - E.backSetback);
  const at = (i, t) => rIn[i] + (rBack[i] - rIn[i]) * t;

  // ---------- envelope profile: (dr from rOut, y) along the shell, base to opening ----------
  // Facade: leans out from the plinth to the bulge, then a quarter-ellipse shoulder, then the roof.
  const prof = [];
  const facadeSamples = 14, shoulderSamples = 16;
  for (let k = 0; k <= facadeSamples; k++) { const f = k / facadeSamples; prof.push({ dr: -E.facadeInset * (1 - Math.sin((f * Math.PI) / 2)), y: E.plinthH + (E.bulgeY - E.plinthH) * f, zone: 'facade' }); }
  for (let k = 1; k <= shoulderSamples; k++) { const p = (k / shoulderSamples) * (Math.PI / 2); prof.push({ dr: -E.shoulderW * (1 - Math.cos(p)), y: E.bulgeY + E.shoulderH * Math.sin(p), zone: 'facade' }); }
  const topY = E.bulgeY + E.shoulderH;
  const facadeEnd = prof.length - 1;
  const louvreEnd = facadeSamples + Math.round(shoulderSamples * 0.45);
  // Roof: from the shoulder crest to the opening edge, with a gentle sag.
  const roofSamples = 10;
  for (let k = 1; k <= roofSamples; k++) prof.push({ t: k / roofSamples, zone: 'roof' });
  const P = (i, j) => {
    const p = prof[j];
    if (p.zone === 'facade') return [rOut[i] + p.dr, p.y];
    const r0 = rOut[i] - E.shoulderW, r1 = rOpen[i];
    return [r0 + (r1 - r0) * p.t, topY + (E.openingY - topY) * p.t - 1.5 * Math.sin(p.t * Math.PI)];
  };

  // Facade shell (louvres) and roof membrane as two meshes sharing the profile.
  const shell = (j0, j1, uScale, vScale) => {
    const pos = [], uv = [], idx = [];
    const cols = j1 - j0 + 1;
    let per = 0;
    for (let i = 0; i <= N; i++) {
      if (i) { const [a] = P(i - 1, j0), [b] = P(i, j0); per += Math.hypot(dirs[i][0] * b - dirs[i - 1][0] * a, dirs[i][1] * b - dirs[i - 1][1] * a); }
      let arc = 0, prev = null;
      for (let j = j0; j <= j1; j++) {
        const [r, y] = P(i, j);
        if (prev) arc += Math.hypot(r - prev[0], y - prev[1]);
        prev = [r, y];
        pos.push(dirs[i][0] * r, y, dirs[i][1] * r);
        uv.push(per / uScale, arc / vScale);
      }
    }
    for (let i = 0; i < N; i++) for (let j = 0; j < cols - 1; j++) { const a = i * cols + j, b = a + cols; idx.push(a, a + 1, b, a + 1, b + 1, b); }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
    g.setIndex(idx); g.computeVertexNormals();
    return g;
  };
  const facade = new THREE.Mesh(shell(0, louvreEnd, 12, 12), new THREE.MeshStandardMaterial({ map: louvreTexture(), roughness: 0.55, metalness: 0.05, side: THREE.DoubleSide }));
  facade.castShadow = facade.receiveShadow = true; facade.name = 'facade';
  group.add(facade);
  const roofG = shell(louvreEnd, prof.length - 1, 9.5, 40);
  const roof = new THREE.Mesh(roofG, new THREE.MeshStandardMaterial({ map: membraneTexture(), roughness: 0.6, side: THREE.DoubleSide, transparent: true, opacity: 0.97 }));
  roof.castShadow = roof.receiveShadow = true; roof.name = 'roof';
  roof.userData.indexCount = roofG.index.count;
  group.add(roof);

  // Plinth: dark glazing with white columns, and a white soffit under the facade.
  const plinth = new THREE.Mesh(ring(dirs, rOut.map((r) => r - E.plinthInset), 0, E.plinthH, N, 6), new THREE.MeshStandardMaterial({ map: plinthTexture(), roughness: 0.25, metalness: 0.4 }));
  plinth.receiveShadow = true; group.add(plinth);
  group.add(new THREE.Mesh(flatRing(dirs, rOut.map((r) => r - E.plinthInset), rOut.map((r) => r - E.facadeInset), E.plinthH, N), new THREE.MeshStandardMaterial({ color: '#efede8', roughness: 0.6, side: THREE.DoubleSide })));

  // ---------- diamond lattice: white members spiralling over the facade ----------
  const tubes = [];
  const K = E.lattice, segs = louvreEnd;
  const surf = (theta, j, off) => {
    const i = ((theta / (Math.PI * 2)) * N + N * 4) % N, i0 = Math.floor(i), f = i - i0;
    const [r0, y0] = P(i0, j), [r1] = P(Math.min(N, i0 + 1), j);
    const r = r0 + (r1 - r0) * f + off;
    return new THREE.Vector3(Math.cos(theta) * r, y0, Math.sin(theta) * r);
  };
  for (let k = 0; k < K; k++) for (const s of [1, -1]) {
    const th0 = (k / K) * Math.PI * 2, d = (s * Math.PI * 2) / K;
    const pts = [];
    for (let j = 0; j <= segs; j++) pts.push(surf(th0 + d * (j / segs), j, 0.55));
    tubes.push(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), segs * 2, 0.42, 5, false));
  }
  // horizontal rings at the plinth top, the bulge and the crest
  for (const j of [0, facadeSamples, louvreEnd]) {
    const pts = []; for (let i = 0; i <= N; i += 2) pts.push(surf((i / N) * Math.PI * 2, j, 0.6));
    tubes.push(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts, true), N, 0.5, 5, true));
  }
  // radial roof ribs (cable/rib lines on the membrane) and the opening ring beam
  for (let i = 0; i < N; i += 4) {
    const pts = []; for (let j = louvreEnd; j < prof.length; j++) { const [r, y] = P(i, j); pts.push(new THREE.Vector3(dirs[i][0] * r, y + 0.35, dirs[i][1] * r)); }
    tubes.push(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 12, 0.22, 4, false));
  }
  { const pts = []; for (let i = 0; i <= N; i += 2) { const [r, y] = P(i, prof.length - 1); pts.push(new THREE.Vector3(dirs[i][0] * r, y, dirs[i][1] * r)); } tubes.push(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts, true), N, 0.9, 6, true)); }
  const lattice = new THREE.Mesh(mergeGeometries(tubes), new THREE.MeshStandardMaterial({ color: '#f4f3ef', roughness: 0.35, metalness: 0.25 }));
  lattice.castShadow = true; lattice.name = 'lattice';
  group.add(lattice);

  // ---------- shields with crossed spears ----------
  const shields = new THREE.Group(); shields.name = 'shields';
  const shieldTex = shieldTexture();
  const shieldMat = new THREE.MeshStandardMaterial({ map: shieldTex, alphaTest: 0.5, roughness: 0.45, side: THREE.DoubleSide, emissive: '#ffffff', emissiveMap: shieldTex, emissiveIntensity: 0 });
  const spearMat = new THREE.MeshStandardMaterial({ color: '#f6f5f1', roughness: 0.35, metalness: 0.2 });
  const axisA = ((-bearing) * Math.PI) / 180; // rotate placements with the long axis
  for (let s = 0; s < E.shields; s++) {
    const theta = axisA - Math.PI / 2 + (s / E.shields) * Math.PI * 2;
    const iC = Math.round((((theta % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI)) / (2 * Math.PI) * N) % N;
    const halfAng = E.shieldW / 2 / rOut[iC];
    const pos = [], uv = [], idx = [];
    const nu = 10, nv = 18;
    for (let a = 0; a <= nu; a++) for (let b = 0; b <= nv; b++) {
      const th = theta - halfAng + (2 * halfAng * a) / nu;
      const y = E.shieldY0 + ((E.shieldY1 - E.shieldY0) * b) / nv;
      const j = profileIndexAtY(prof, y);
      const p = surf(th, j, 1.6);
      pos.push(p.x, y, p.z); uv.push(a / nu, b / nv);
    }
    for (let a = 0; a < nu; a++) for (let b = 0; b < nv; b++) { const k0 = a * (nv + 1) + b, k1 = k0 + nv + 1; idx.push(k0, k0 + 1, k1, k0 + 1, k1 + 1, k1); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); g.setIndex(idx); g.computeVertexNormals();
    const m = new THREE.Mesh(g, shieldMat); m.castShadow = true; shields.add(m);
    // spears: from low outside to high outside, crossing behind the shield centre
    for (const sgn of [1, -1]) {
      const a0 = theta + sgn * halfAng * 1.25, a1 = theta - sgn * halfAng * 1.25;
      const y0 = E.shieldY0 + 2, y1 = E.shieldY1 + 4;
      const pts = [];
      for (let q = 0; q <= 16; q++) { const f = q / 16, th = a0 + (a1 - a0) * f, y = y0 + (y1 - y0) * f; pts.push(surf(th, profileIndexAtY(prof, y), 1.1).setY(y)); }
      shields.add(new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 24, 0.6, 8, false), spearMat));
      const dirT = pts.at(-1).clone().sub(pts.at(-3)).normalize();
      const tip = new THREE.Mesh(new THREE.SphereGeometry(1, 16, 10), spearMat);
      tip.scale.set(1.6, 4.8, 0.7);
      tip.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dirT);
      tip.position.copy(pts.at(-1)).addScaledVector(dirT, 4.2);
      tip.castShadow = true; shields.add(tip);
    }
  }
  group.add(shields);

  // ---------- seating bowl (concrete steps) ----------
  const pos = [], col = [], idx = [];
  let n = 0;
  const quad = (p, c) => { pos.push(...p); for (let k = 0; k < 4; k++) col.push(c.r, c.g, c.b); idx.push(n, n + 1, n + 2, n, n + 2, n + 3); n += 4; };
  const concrete = new THREE.Color('#c9c4bb'), tread = new THREE.Color('#d6d1c8');
  const seatSpots = [];
  for (const T of E.tiers) {
    for (let k = 0; k < T.rows; k++) {
      const f0 = k / T.rows, f1 = (k + 1) / T.rows;
      const t0 = T.t0 + (T.t1 - T.t0) * f0, t1 = T.t0 + (T.t1 - T.t0) * f1;
      const y0 = T.y0 + (T.y1 - T.y0) * f0, y1 = T.y0 + (T.y1 - T.y0) * f1;
      for (let i = 0; i < N; i++) {
        const [ax, az] = dirs[i], [bx, bz] = dirs[i + 1];
        const ra0 = at(i, t0), ra1 = at(i, t1), rb0 = at(i + 1, t0), rb1 = at(i + 1, t1);
        quad([ax * ra0, y0, az * ra0, ax * ra1, y0, az * ra1, bx * rb1, y0, bz * rb1, bx * rb0, y0, bz * rb0], tread);
        quad([ax * ra1, y0, az * ra1, ax * ra1, y1, az * ra1, bx * rb1, y1, bz * rb1, bx * rb1, y0, bz * rb1], concrete);
      }
      seatSpots.push({ tier: T, k, f0, t: (t0 + t1) / 2, y: y0 });
    }
  }
  const glass = new THREE.Color('#2a3138'), wall = new THREE.Color('#e3dfd8');
  const band = (t, yA, yB, c) => { for (let i = 0; i < N; i++) { const [ax, az] = dirs[i], [bx, bz] = dirs[i + 1]; const ra = at(i, t), rb = at(i + 1, t); quad([ax * ra, yA, az * ra, bx * rb, yA, bz * rb, bx * rb, yB, bz * rb, ax * ra, yB, az * ra], c); } };
  const slab = (tA, tB, y, c) => { for (let i = 0; i < N; i++) { const [ax, az] = dirs[i], [bx, bz] = dirs[i + 1]; const ra0 = at(i, tA), ra1 = at(i, tB), rb0 = at(i + 1, tA), rb1 = at(i + 1, tB); quad([ax * ra0, y, az * ra0, ax * ra1, y, az * ra1, bx * rb1, y, bz * rb1, bx * rb0, y, bz * rb0], c); } };
  band(0, 0, 1.2, wall);
  band(0.38, 12.5, 14.5, wall); slab(0.38, 0.45, 14.5, wall); band(0.45, 14.5, 20.5, glass);
  band(0.66, 29.5, 31.0, wall); slab(0.66, 0.70, 31.0, wall); band(0.70, 31.0, 33.0, wall);
  for (let i = 0; i < N; i++) { const [ax, az] = dirs[i], [bx, bz] = dirs[i + 1]; quad([ax * rBack[i], 0, az * rBack[i], ax * rBack[i], 46, az * rBack[i], bx * rBack[i + 1], 46, bz * rBack[i + 1], bx * rBack[i + 1], 0, bz * rBack[i + 1]], new THREE.Color('#d2ccc2')); }
  const sg = new THREE.BufferGeometry();
  sg.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  sg.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  sg.setIndex(idx); sg.computeVertexNormals();
  const seating = new THREE.Mesh(sg, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.9, side: THREE.DoubleSide }));
  seating.castShadow = seating.receiveShadow = true; seating.name = 'seating';
  group.add(seating);

  // ---------- individual seats (instanced) with aisles ----------
  const cum = [0];
  for (let i = 1; i <= N; i++) cum.push(0);
  const seatList = [];
  for (const S of seatSpots) {
    let len = 0; const segL = [];
    for (let i = 0; i < N; i++) { const ra = at(i, S.t), rb = at(i + 1, S.t); const l = Math.hypot(dirs[i + 1][0] * rb - dirs[i][0] * ra, dirs[i + 1][1] * rb - dirs[i][1] * ra); segL.push(l); len += l; }
    let i = 0, acc = 0;
    for (let d = E.seatPitch / 2; d < len; d += E.seatPitch) {
      const inAisle = (d % E.aisleEvery) < E.aisleW;
      if (inAisle) continue;
      while (acc + segL[i] < d) { acc += segL[i]; i++; }
      const f = (d - acc) / segL[i];
      const ra = at(i, S.t), rb = at(i + 1, S.t);
      const x = dirs[i][0] * ra * (1 - f) + dirs[i + 1][0] * rb * f, z = dirs[i][1] * ra * (1 - f) + dirs[i + 1][1] * rb * f;
      const g = S.tier.name === 'Upper tier' ? Math.max(0, (S.f0 - 0.62) / 0.38) : 0;
      seatList.push({ x, z, y: S.y, ang: Math.atan2(z, x), g, tier: S.tier });
    }
  }
  const seatGeo = seatGeometry();
  const seats = new THREE.InstancedMesh(seatGeo, new THREE.MeshStandardMaterial({ roughness: 0.6 }), seatList.length);
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), one = new THREE.Vector3(1, 1, 1), v3 = new THREE.Vector3(), yAx = new THREE.Vector3(0, 1, 0);
  const cA = new THREE.Color(), cB = new THREE.Color();
  seatList.forEach((s, k) => {
    q.setFromAxisAngle(yAx, -s.ang - Math.PI / 2);
    m4.compose(v3.set(s.x, s.y, s.z), q, one); seats.setMatrixAt(k, m4);
    cA.set(s.tier.seat[0]).lerp(cB.set(s.tier.seat[1]), s.g); seats.setColorAt(k, cA);
  });
  seats.castShadow = false; seats.receiveShadow = true; seats.name = 'seats';
  group.add(seats);

  // ---------- roof trusses under the membrane, and the floodlight ring ----------
  const nT = N / 4;
  const truss = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1), new THREE.MeshStandardMaterial({ color: '#eceae5', roughness: 0.4, metalness: 0.35 }), nT);
  const A = new THREE.Vector3(), B = new THREE.Vector3(), D = new THREE.Vector3(), X = new THREE.Vector3(1, 0, 0), M = new THREE.Vector3();
  for (let k = 0; k < nT; k++) {
    const i = k * 4, [r0, y0] = P(i, facadeEnd), [r1, y1] = P(i, prof.length - 1);
    A.set(dirs[i][0] * r0, y0 - 2.4, dirs[i][1] * r0); B.set(dirs[i][0] * r1, y1 - 1.8, dirs[i][1] * r1);
    D.subVectors(B, A); const L = D.length(); D.normalize(); M.addVectors(A, B).multiplyScalar(0.5);
    q.setFromUnitVectors(X, D); m4.compose(M, q, v3.set(L, 2.4, 0.6)); truss.setMatrixAt(k, m4);
  }
  truss.castShadow = true; truss.name = 'trusses'; truss.userData.count = nT;
  group.add(truss);
  const lightsMat = new THREE.MeshStandardMaterial({ color: '#fffbe8', emissive: '#fff4cf', emissiveIntensity: 0 });
  { const pts = []; for (let i = 0; i <= N; i += 2) { const [r, y] = P(i, prof.length - 1); pts.push(new THREE.Vector3(dirs[i][0] * (r + 2), y - 2.6, dirs[i][1] * (r + 2))); } const lights = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts, true), N, 0.55, 6, true), lightsMat); lights.name = 'floodlights'; group.add(lights); }
  // LED crest ring (night colour)
  const ledMat = new THREE.MeshStandardMaterial({ color: '#d9d6f0', emissive: '#9b5cff', emissiveIntensity: 0 });
  { const pts = []; for (let i = 0; i <= N; i += 2) pts.push(surf((i / N) * Math.PI * 2, facadeSamples + 4, 0.9)); group.add(new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts, true), N, 0.35, 5, true), ledMat)); }

  // concourse floor
  group.add(new THREE.Mesh(flatRing(dirs, rBack, rOut.map((r) => r + 6), 0.15, N), new THREE.MeshStandardMaterial({ color: '#d9d2c6', roughness: 0.9, side: THREE.DoubleSide })));

  const rHole = rOpen;
  return { group, seating, seats, seatCount: seatList.length, facade, roof, truss, lattice, shields, shieldMat, lightsMat, ledMat, dirs, rIn, rOut, rHole, rBack, at, tierMeta: E.tiers, P, profLen: prof.length, topY };
}

function profileIndexAtY(prof, y) {
  let best = 0, bd = 1e9;
  prof.forEach((p, j) => { if (p.zone === 'facade' && Math.abs(p.y - y) < bd) { bd = Math.abs(p.y - y); best = j; } });
  return best;
}

function ring(dirs, r, y0, y1, N, uScale) {
  const pos = [], uv = [], idx = []; let per = 0;
  for (let i = 0; i <= N; i++) {
    if (i) per += Math.hypot(dirs[i][0] * r[i] - dirs[i - 1][0] * r[i - 1], dirs[i][1] * r[i] - dirs[i - 1][1] * r[i - 1]);
    pos.push(dirs[i][0] * r[i], y0, dirs[i][1] * r[i], dirs[i][0] * r[i], y1, dirs[i][1] * r[i]);
    uv.push(per / uScale, 0, per / uScale, 1);
    if (i < N) { const k = i * 2; idx.push(k, k + 1, k + 2, k + 1, k + 3, k + 2); }
  }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); g.setIndex(idx); g.computeVertexNormals();
  return g;
}

function flatRing(dirs, rA, rB, y, N) {
  const pos = [], idx = [];
  for (let i = 0; i <= N; i++) { pos.push(dirs[i][0] * rA[i], y, dirs[i][1] * rA[i], dirs[i][0] * rB[i], y, dirs[i][1] * rB[i]); if (i < N) { const k = i * 2; idx.push(k, k + 2, k + 1, k + 1, k + 2, k + 3); } }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setIndex(idx); g.computeVertexNormals();
  return g;
}

// A stadium seat: pan and back, 0.45 m wide. Faces +z in local space (towards the pitch after rotation).
function seatGeometry() {
  const pan = new THREE.BoxGeometry(0.44, 0.06, 0.38); pan.translate(0, 0.42, 0.1);
  const back = new THREE.BoxGeometry(0.44, 0.38, 0.05); back.rotateX(-0.18); back.translate(0, 0.62, -0.1);
  const leg = new THREE.BoxGeometry(0.06, 0.4, 0.06); leg.translate(0, 0.2, 0.0);
  return mergeGeometries([pan, back, leg]);
}

function canvasTex(w, h, draw, repeat = true) {
  const cv = document.createElement('canvas'); cv.width = w; cv.height = h;
  draw(cv.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(cv);
  if (repeat) { t.wrapS = THREE.RepeatWrapping; t.wrapT = THREE.RepeatWrapping; }
  t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  return t;
}

// Horizontal white louvres with dark gaps; tile = 12 x 12 m.
function louvreTexture() {
  return canvasTex(256, 512, (x, w, h) => {
    x.fillStyle = '#a7abb0'; x.fillRect(0, 0, w, h);
    const n = 24;
    for (let i = 0; i < n; i++) {
      const y = (i / n) * h;
      const g = x.createLinearGradient(0, y, 0, y + h / n * 0.8);
      g.addColorStop(0, '#ffffff'); g.addColorStop(0.7, '#f1f0ec'); g.addColorStop(1, '#d9d7d2');
      x.fillStyle = g; x.fillRect(0, y, w, (h / n) * 0.8);
    }
    for (let k = 0; k < 4; k++) { x.fillStyle = 'rgba(120,124,130,0.25)'; x.fillRect((k * w) / 4, 0, 2, h); }
  });
}

// White PTFE membrane panels with ridge shading; tile = one rib bay (9.5 m) along the perimeter.
function membraneTexture() {
  return canvasTex(256, 512, (x, w, h) => {
    const g = x.createLinearGradient(0, 0, w, 0);
    g.addColorStop(0, '#d9d7d2'); g.addColorStop(0.08, '#f2f1ed'); g.addColorStop(0.5, '#fbfbf8'); g.addColorStop(0.92, '#eeede9'); g.addColorStop(1, '#d6d4cf');
    x.fillStyle = g; x.fillRect(0, 0, w, h);
    x.fillStyle = 'rgba(160,158,150,0.25)';
    for (let i = 1; i < 8; i++) x.fillRect(0, (i * h) / 8, w, 2);
  });
}

function plinthTexture() {
  return canvasTex(256, 64, (x, w, h) => {
    const g = x.createLinearGradient(0, 0, 0, h); g.addColorStop(0, '#3a4046'); g.addColorStop(1, '#262b30');
    x.fillStyle = g; x.fillRect(0, 0, w, h);
    x.fillStyle = 'rgba(160,190,210,0.18)'; x.fillRect(0, 6, w, h * 0.45);
    x.fillStyle = '#ecebe6'; for (let i = 0; i < 4; i++) x.fillRect((i * w) / 4, 0, 10, h);
    x.fillStyle = '#ecebe6'; x.fillRect(0, 0, w, 4);
  });
}

// Maasai shield as on the Kenyan flag: black sides, red body, white spine and lens marks.
function shieldTexture() {
  return canvasTex(512, 1024, (x, w, h) => {
    x.clearRect(0, 0, w, h);
    const lens = (cx, cy, rw, rh) => { x.beginPath(); x.moveTo(cx, cy - rh); x.bezierCurveTo(cx + rw * 1.35, cy - rh * 0.55, cx + rw * 1.35, cy + rh * 0.55, cx, cy + rh); x.bezierCurveTo(cx - rw * 1.35, cy + rh * 0.55, cx - rw * 1.35, cy - rh * 0.55, cx, cy - rh); x.closePath(); };
    lens(w / 2, h / 2, w * 0.37, h * 0.495); x.fillStyle = '#141414'; x.fill();
    x.save(); lens(w / 2, h / 2, w * 0.37, h * 0.495); x.clip();
    x.fillStyle = '#c4161f'; x.beginPath(); x.ellipse(w / 2, h / 2, w * 0.33, h * 0.56, 0, 0, Math.PI * 2); x.fill();
    x.restore();
    x.fillStyle = '#ffffff';
    x.fillRect(w / 2 - 9, h * 0.05, 18, h * 0.9);
    lens(w / 2, h / 2, w * 0.05, h * 0.06); x.fill();
    for (const s of [-1, 1]) { lens(w / 2, h / 2 + s * h * 0.22, w * 0.035, h * 0.12); x.fill(); }
    x.strokeStyle = 'rgba(255,255,255,0.9)'; x.lineWidth = 6;
    for (const s of [-1, 1]) { x.beginPath(); x.moveTo(w / 2 + s * 30, h * 0.12); x.quadraticCurveTo(w / 2 + s * 70, h / 2, w / 2 + s * 30, h * 0.88); x.stroke(); }
  }, false);
}
