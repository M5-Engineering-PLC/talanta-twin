import * as THREE from 'three/webgpu';
import { rayRadius, roundedRect } from './geom.js';

// Stadium bowl from measured plan outlines:
//   outer roof edge and roof opening: OSM building r20072298 (manifest.features.bowl_outer / bowl_hole)
//   pitch zone and long-axis bearing: W1b Google Earth Pro measurement
// All heights and tier splits are ESTIMATES until W1b shadows / W3 SfM / drawings land.
export const BOWL_EST = {
  seatStart: { halfLong: 59.5, halfWide: 39.5, r: 14 }, // first row, 2 m beyond the W1b pitch zone
  backSetback: 9,     // facade zone between the top row and the roof edge (m)
  tiers: [            // t = fraction from first row to back row; y = height above pitch (m)
    { name: 'Lower tier', t0: 0.0, t1: 0.38, y0: 1.2, y1: 12.5, rows: 24, colors: ['#2e7442', '#2a6a3c'] },
    { name: 'Middle tier', t0: 0.45, t1: 0.66, y0: 20.5, y1: 29.5, rows: 13, colors: ['#a3282a', '#962326'] },
    { name: 'Upper tier', t0: 0.70, t1: 1.0, y0: 33.0, y1: 46.0, rows: 21, colors: ['#a3282a', '#1f1d1b'] },
  ],
  roofOuterY: 50, roofInnerY: 44.5, overhang: 2.5,
  N: 160,
};

export function buildBowl(features) {
  const E = BOWL_EST, N = E.N;
  const group = new THREE.Group();
  group.name = 'bowl';
  const outer = features.bowl_outer, hole = features.bowl_hole;
  const bearing = features.pitch_bearing_deg;
  const seat0 = roundedRect(E.seatStart.halfLong, E.seatStart.halfWide, E.seatStart.r, bearing);

  const dirs = [], rIn = [], rOut = [], rHole = [];
  for (let i = 0; i <= N; i++) {
    const a = (i / N) * Math.PI * 2, ux = Math.cos(a), uz = Math.sin(a);
    dirs.push([ux, uz]);
    rIn.push(rayRadius(seat0, ux, uz));
    rOut.push(rayRadius(outer, ux, uz));
    rHole.push(hole ? rayRadius(hole, ux, uz) : rIn[i] + 20);
  }
  const rBack = rOut.map((r) => r - E.backSetback);
  const at = (i, t) => rIn[i] + (rBack[i] - rIn[i]) * t;

  // ---- seating: stepped treads and risers with vertex colours ----
  const pos = [], col = [], idx = [];
  const c = new THREE.Color();
  let n = 0;
  const quad = (p, cc) => { pos.push(...p); for (let k = 0; k < 4; k++) col.push(cc.r, cc.g, cc.b); idx.push(n, n + 1, n + 2, n, n + 2, n + 3); n += 4; };
  const concrete = new THREE.Color('#bdb6aa');
  const tierMeta = [];
  for (const T of E.tiers) {
    const ca = new THREE.Color(T.colors[0]), cb = new THREE.Color(T.colors[1]);
    for (let k = 0; k < T.rows; k++) {
      const f0 = k / T.rows, f1 = (k + 1) / T.rows;
      const t0 = T.t0 + (T.t1 - T.t0) * f0, t1 = T.t0 + (T.t1 - T.t0) * f1;
      const y0 = T.y0 + (T.y1 - T.y0) * f0, y1 = T.y0 + (T.y1 - T.y0) * f1;
      // Upper tier fades from red to black in its last third (green-red-black gradient, design facts).
      const g = T.name === 'Upper tier' ? Math.max(0, (f0 - 0.66) / 0.34) : f0 * 0.3;
      c.copy(ca).lerp(cb, g).multiplyScalar(k % 2 ? 0.93 : 1);
      for (let i = 0; i < N; i++) {
        const [ax, az] = dirs[i], [bx, bz] = dirs[i + 1];
        const ra0 = at(i, t0), ra1 = at(i, t1), rb0 = at(i + 1, t0), rb1 = at(i + 1, t1);
        // tread
        quad([ax * ra0, y0, az * ra0, ax * ra1, y0, az * ra1, bx * rb1, y0, bz * rb1, bx * rb0, y0, bz * rb0], c);
        // riser up to next row
        quad([ax * ra1, y0, az * ra1, ax * ra1, y1, az * ra1, bx * rb1, y1, bz * rb1, bx * rb1, y0, bz * rb1], concrete);
      }
    }
    tierMeta.push({ name: T.name, t0: T.t0, t1: T.t1, y0: T.y0, y1: T.y1 });
  }
  // Tier fronts and the VIP band (dark glass), and the front wall of the lower tier.
  const glass = new THREE.Color('#2b3036'), wall = new THREE.Color('#d9d3c8');
  const band = (t, yA, yB, cc) => {
    for (let i = 0; i < N; i++) {
      const [ax, az] = dirs[i], [bx, bz] = dirs[i + 1];
      const ra = at(i, t), rb = at(i + 1, t);
      quad([ax * ra, yA, az * ra, bx * rb, yA, bz * rb, bx * rb, yB, bz * rb, ax * ra, yB, az * ra], cc);
    }
  };
  const slab = (tA, tB, y, cc) => {
    for (let i = 0; i < N; i++) {
      const [ax, az] = dirs[i], [bx, bz] = dirs[i + 1];
      const ra0 = at(i, tA), ra1 = at(i, tB), rb0 = at(i + 1, tA), rb1 = at(i + 1, tB);
      quad([ax * ra0, y, az * ra0, ax * ra1, y, az * ra1, bx * rb1, y, bz * rb1, bx * rb0, y, bz * rb0], cc);
    }
  };
  band(0, 0, 1.2, wall);
  band(0.38, 12.5, 14.5, wall); slab(0.38, 0.45, 14.5, wall); band(0.45, 14.5, 20.5, glass);   // VIP boxes
  band(0.66, 29.5, 31.0, wall); slab(0.66, 0.70, 31.0, wall); band(0.70, 31.0, 33.0, wall);
  // back wall behind the top row, down to the ground
  for (let i = 0; i < N; i++) {
    const [ax, az] = dirs[i], [bx, bz] = dirs[i + 1];
    const ra = rBack[i], rb = rBack[i + 1];
    quad([ax * ra, 0, az * ra, ax * ra, 46, az * ra, bx * rb, 46, bz * rb, bx * rb, 0, bz * rb], new THREE.Color('#cfc8bc'));
  }
  const sg = new THREE.BufferGeometry();
  sg.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  sg.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  sg.setIndex(idx);
  sg.computeVertexNormals();
  const seating = new THREE.Mesh(sg, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.85, side: THREE.DoubleSide }));
  seating.castShadow = seating.receiveShadow = true;
  seating.name = 'seating';
  group.add(seating);

  // ---- concourse floor between the back wall and the facade ----
  const fl = [], fi = []; let fn = 0;
  for (let i = 0; i < N; i++) {
    const [ax, az] = dirs[i], [bx, bz] = dirs[i + 1];
    fl.push(ax * rBack[i], 0.15, az * rBack[i], ax * (rOut[i] + 4), 0.15, az * (rOut[i] + 4), bx * (rOut[i + 1] + 4), 0.15, bz * (rOut[i + 1] + 4), bx * rBack[i + 1], 0.15, bz * rBack[i + 1]);
    fi.push(fn, fn + 1, fn + 2, fn, fn + 2, fn + 3); fn += 4;
  }
  const fg = new THREE.BufferGeometry(); fg.setAttribute('position', new THREE.Float32BufferAttribute(fl, 3)); fg.setIndex(fi); fg.computeVertexNormals();
  const floor = new THREE.Mesh(fg, new THREE.MeshStandardMaterial({ color: '#d8cfc0', roughness: 0.95, side: THREE.DoubleSide }));
  floor.receiveShadow = true; group.add(floor);

  // ---- facade screen with shield openings ----
  const facade = new THREE.Mesh(ringWall(dirs, rOut.map((r) => r - 1.0), 0, 47.5, N), new THREE.MeshStandardMaterial({
    map: facadeTexture(), alphaTest: 0.5, side: THREE.DoubleSide, roughness: 0.7, metalness: 0.1,
  }));
  facade.castShadow = true; facade.name = 'facade';
  group.add(facade);

  // ---- roof: membrane ring from the opening to the outer edge, plus trusses ----
  const roofG = roofRing(dirs, rHole, rOut.map((r) => r + E.overhang), E.roofInnerY, E.roofOuterY, N, 6);
  const roof = new THREE.Mesh(roofG, new THREE.MeshStandardMaterial({ color: '#f3f1ec', roughness: 0.55, side: THREE.DoubleSide, transparent: true, opacity: 0.96 }));
  roof.castShadow = true; roof.receiveShadow = true; roof.name = 'roof';
  roof.userData.indexCount = roofG.index.count;
  group.add(roof);

  const trussGeo = new THREE.BoxGeometry(1, 1, 1);
  const nT = N / 2;
  const truss = new THREE.InstancedMesh(trussGeo, new THREE.MeshStandardMaterial({ color: '#e9e6e0', roughness: 0.5, metalness: 0.3 }), nT);
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), s = new THREE.Vector3(), p = new THREE.Vector3();
  const a = new THREE.Vector3(), b = new THREE.Vector3(), d = new THREE.Vector3(), up = new THREE.Vector3(1, 0, 0);
  for (let j = 0; j < nT; j++) {
    const i = j * 2, [ux, uz] = dirs[i];
    a.set(ux * rHole[i], E.roofInnerY - 1.6, uz * rHole[i]);
    b.set(ux * (rOut[i] + E.overhang), E.roofOuterY - 1.6, uz * (rOut[i] + E.overhang));
    d.subVectors(b, a); const L = d.length(); d.normalize();
    p.addVectors(a, b).multiplyScalar(0.5);
    q.setFromUnitVectors(up, d);
    s.set(L, 2.2, 0.7);
    m.compose(p, q, s); truss.setMatrixAt(j, m);
  }
  truss.castShadow = true; truss.name = 'trusses'; truss.userData.count = nT;
  group.add(truss);

  // Edge beams and the floodlight ring under the inner roof edge.
  const edge = (r, y, rad, mat) => {
    const pts = dirs.map(([ux, uz], i) => new THREE.Vector3(ux * r[i], y, uz * r[i]));
    return new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts, true), N, rad, 6, true), mat);
  };
  group.add(edge(rHole, E.roofInnerY - 0.3, 0.9, new THREE.MeshStandardMaterial({ color: '#dedad3', metalness: 0.4, roughness: 0.4 })));
  group.add(edge(rOut.map((r) => r + E.overhang), E.roofOuterY - 0.2, 0.8, new THREE.MeshStandardMaterial({ color: '#dedad3', metalness: 0.4, roughness: 0.4 })));
  const lightsMat = new THREE.MeshStandardMaterial({ color: '#fffbe8', emissive: '#fff4cf', emissiveIntensity: 0 });
  const lights = edge(rHole.map((r) => r + 1.5), E.roofInnerY - 2.2, 0.55, lightsMat);
  lights.name = 'floodlights';
  group.add(lights);

  return { group, seating, facade, roof, truss, lights, lightsMat, dirs, rIn, rOut, rHole, rBack, tierMeta, at };
}

function ringWall(dirs, r, y0, y1, N) {
  const pos = [], uv = [], idx = [];
  let per = 0;
  for (let i = 0; i <= N; i++) {
    if (i) per += Math.hypot(dirs[i][0] * r[i] - dirs[i - 1][0] * r[i - 1], dirs[i][1] * r[i] - dirs[i - 1][1] * r[i - 1]);
    const [ux, uz] = dirs[i];
    pos.push(ux * r[i], y0, uz * r[i], ux * r[i], y1, uz * r[i]);
    uv.push(per / 9, 0, per / 9, 1);
    if (i < N) { const k = i * 2; idx.push(k, k + 2, k + 1, k + 1, k + 2, k + 3); }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx); g.computeVertexNormals();
  return g;
}

// Roof ring ordered by angle, so drawRange can reveal it as a sweep (construction replay).
function roofRing(dirs, rA, rB, yA, yB, N, M) {
  const pos = [], idx = [];
  for (let i = 0; i <= N; i++) {
    const [ux, uz] = dirs[i];
    for (let j = 0; j <= M; j++) {
      const t = j / M, r = rA[i] + (rB[i] - rA[i]) * t;
      const y = yA + (yB - yA) * Math.sin((t * Math.PI) / 2) + 1.2 * Math.sin(t * Math.PI);
      pos.push(ux * r, y, uz * r);
    }
  }
  for (let i = 0; i < N; i++) for (let j = 0; j < M; j++) {
    const a = i * (M + 1) + j, b = a + M + 1;
    idx.push(a, b, a + 1, a + 1, b, b + 1);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setIndex(idx); g.computeVertexNormals();
  return g;
}

// Facade tile: vertical fins with a shield-shaped opening, red accent line at the base.
function facadeTexture() {
  const cv = document.createElement('canvas'); cv.width = 128; cv.height = 512;
  const x = cv.getContext('2d');
  x.fillStyle = '#ebe8e2'; x.fillRect(0, 0, 128, 512);
  x.globalCompositeOperation = 'destination-out';
  const shield = (cx, cy, w, h) => {
    x.beginPath(); x.moveTo(cx, cy - h / 2);
    x.bezierCurveTo(cx + w * 0.6, cy - h * 0.35, cx + w / 2, cy + h * 0.1, cx, cy + h / 2);
    x.bezierCurveTo(cx - w / 2, cy + h * 0.1, cx - w * 0.6, cy - h * 0.35, cx, cy - h / 2);
    x.fill();
  };
  shield(64, 150, 70, 190); shield(64, 370, 70, 190);
  x.fillRect(0, 0, 10, 512); x.fillRect(118, 0, 10, 512);
  x.globalCompositeOperation = 'source-over';
  x.fillStyle = '#ebe8e2'; x.fillRect(0, 0, 3, 512); x.fillRect(125, 0, 3, 512);
  x.fillStyle = '#ebe8e2'; x.fillRect(62, 0, 4, 512);
  x.fillStyle = '#9b2a24'; x.fillRect(0, 498, 128, 6);
  const t = new THREE.CanvasTexture(cv);
  t.wrapS = THREE.RepeatWrapping; t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  t.flipY = true;
  return t;
}
