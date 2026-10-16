import * as THREE from 'three/webgpu';
import { rotate, rayRadius } from './geom.js';

// Site furniture for the fully built state. Positions are ESTIMATES from reference frames
// (JWNowpO44rw 07:14, 04:45, 20:05; 8n3ILabO8uw; CuS83a44PG8) until W1b measures them.
// 07:14 was a V6 held-out frame; it is now recorded as used and replaced (gis/heldout_frames.csv).
// main forecourt on the north side (towards Ngong Road), an eye-shaped plaza with radial
// paving and a central planter, a long fountain pool with dry-deck jets and steps.
export function buildSite(features, bowl, groundAt, pad) {
  const g = new THREE.Group(); g.name = 'site-furniture';
  const b = features.pitch_bearing_deg;
  const north = rotate([[0, -1]], b)[0];
  const rN = rayRadius(features.bowl_outer, north[0], north[1]);
  const local = (along, across) => { const [x, z] = rotate([[across, -along]], b)[0]; return [x, z]; };
  const yaw = -(b * Math.PI) / 180;

  // ---- plaza (eye shape, the shield form) ----
  const plazaC = rN + 78, half = 92, depth = 46;
  const eye = [];
  for (let i = 0; i <= 64; i++) { const t = (i / 64) * Math.PI * 2; const x = half * Math.cos(t), y = depth * Math.sin(t) * Math.pow(Math.abs(Math.cos(t * 0.5) * Math.sin(t * 0.5)) * 2, 0.0); eye.push([x, y * (1 - 0.35 * Math.pow(Math.cos(t), 2))]); }
  const shape = new THREE.Shape(eye.map(([x, y]) => new THREE.Vector2(x, y)));
  const pg = new THREE.ShapeGeometry(shape, 48); pg.rotateX(-Math.PI / 2);
  const uvs = pg.attributes.uv; for (let i = 0; i < uvs.count; i++) uvs.setXY(i, (pg.attributes.position.getX(i) + half) / (2 * half), (pg.attributes.position.getZ(i) + depth) / (2 * depth));
  const plaza = new THREE.Mesh(pg, new THREE.MeshStandardMaterial({ map: plazaTexture(), roughness: 0.85, polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -4 }));
  const [px, pz] = local(plazaC, 0);
  plaza.position.set(px, pad + 0.18, pz); plaza.rotation.y = yaw; plaza.receiveShadow = true;
  g.add(plaza);
  // central planter with flowers
  const planter = new THREE.Mesh(new THREE.CylinderGeometry(7, 7.4, 0.8, 48), new THREE.MeshStandardMaterial({ color: '#e7e3dc', roughness: 0.7 }));
  planter.position.set(px, pad + 0.4, pz); g.add(planter);
  const bed = new THREE.Mesh(new THREE.CylinderGeometry(6.4, 6.4, 0.9, 48), new THREE.MeshStandardMaterial({ map: flowerTexture(), roughness: 1 }));
  bed.position.set(px, pad + 0.5, pz); g.add(bed);

  // ---- forecourt paving between the facade and the plaza ----
  const fc = new THREE.Mesh(new THREE.PlaneGeometry(150, plazaC - rN + 10), new THREE.MeshStandardMaterial({ color: '#d8d2c7', roughness: 0.9, polygonOffset: true, polygonOffsetFactor: -3, polygonOffsetUnits: -3 }));
  fc.rotation.x = -Math.PI / 2; const [fx, fz] = local(rN + (plazaC - rN) / 2, 0); fc.position.set(fx, pad + 0.12, fz);
  g.add(fc); fc.rotation.z = yaw;
  fc.receiveShadow = true;

  // ---- fountain pool with steps ----
  const poolC = rN + 36, poolL = 66, poolW = 15;
  const fountain = new THREE.Group(); fountain.name = 'fountain';
  const [fx2, fz2] = local(poolC, 0);
  fountain.position.set(fx2, pad, fz2); fountain.rotation.y = yaw;
  const stone = new THREE.MeshStandardMaterial({ color: '#ddd7cc', roughness: 0.75 });
  // Three stone steps as frames round an open pool; the water sits above the paving, below the coping.
  const STEP = 0.18, rimY = 3 * STEP, waterY = rimY - 0.12;
  const rectPath = (P, w, d) => { P.moveTo(-w / 2, -d / 2); P.lineTo(w / 2, -d / 2); P.lineTo(w / 2, d / 2); P.lineTo(-w / 2, d / 2); P.closePath(); return P; };
  for (let s = 0; s < 3; s++) {
    const sh = rectPath(new THREE.Shape(), poolL + 12 - s * 4, poolW + 12 - s * 4);
    sh.holes.push(rectPath(new THREE.Path(), poolL, poolW));
    const sg = new THREE.ExtrudeGeometry(sh, { depth: STEP * (s + 1), bevelEnabled: false });
    sg.rotateX(-Math.PI / 2);
    const st = new THREE.Mesh(sg, stone); st.castShadow = st.receiveShadow = true; fountain.add(st);
  }
  const basin = new THREE.Mesh(new THREE.PlaneGeometry(poolL, poolW), new THREE.MeshStandardMaterial({ color: '#2f5560', roughness: 0.9 }));
  basin.rotation.x = -Math.PI / 2; basin.position.y = 0.03; fountain.add(basin);
  const water = new THREE.Mesh(new THREE.PlaneGeometry(poolL, poolW), new THREE.MeshStandardMaterial({ color: '#5f7f8c', roughness: 0.05, metalness: 0.6, emissive: '#3a2a6a', emissiveIntensity: 0 }));
  water.rotation.x = -Math.PI / 2; water.position.y = waterY; water.name = 'fountain-water'; fountain.add(water);
  // jets: two straight rows and a centre arc (dry-deck nozzles)
  const jets = [];
  for (const row of [-3.5, 3.5]) for (let i = 0; i < 30; i++) jets.push({ x: -poolL / 2 + 3 + (i * (poolL - 6)) / 29, z: row, h: 4, ph: i * 0.37 + (row > 0 ? 1.7 : 0) });
  for (let i = 0; i < 13; i++) { const a = -Math.PI / 2 + (i / 12) * Math.PI; jets.push({ x: Math.sin(a) * 10, z: -Math.cos(a) * 3, h: 8, ph: i * 0.5 }); }
  const jetGeo = new THREE.CylinderGeometry(0.06, 0.22, 1, 8, 1, true); jetGeo.translate(0, 0.5, 0);
  const jetMat = new THREE.MeshStandardMaterial({ color: '#ffffff', emissive: '#ffffff', emissiveIntensity: 0.15, transparent: true, opacity: 0.55, depthWrite: false });
  const jetMesh = new THREE.InstancedMesh(jetGeo, jetMat, jets.length);
  const capGeo = new THREE.SphereGeometry(0.55, 10, 8);
  const capMesh = new THREE.InstancedMesh(capGeo, jetMat, jets.length);
  fountain.add(jetMesh, capMesh);
  g.add(fountain);

  // ---- light masts round the site (white poles, frames 26:12, 20:05) ----
  const site = features.site;
  const masts = [];
  let per = 0; const segs = [];
  for (let i = 0; i < site.length - 1; i++) { const l = Math.hypot(site[i + 1][0] - site[i][0], site[i + 1][1] - site[i][1]); segs.push(l); per += l; }
  const cx = 0, cz = 0;
  for (let d = 20; d < per; d += 70) {
    let i = 0, acc = 0; while (acc + segs[i] < d) { acc += segs[i]; i++; }
    const f = (d - acc) / segs[i];
    let x = site[i][0] + (site[i + 1][0] - site[i][0]) * f, z = site[i][1] + (site[i + 1][1] - site[i][1]) * f;
    const L = Math.hypot(x - cx, z - cz); x -= ((x - cx) / L) * 22; z -= ((z - cz) / L) * 22;
    masts.push([x, z]);
  }
  for (const s of [-1, 1]) for (let k = 0; k < 4; k++) masts.push(local(rN + 20 + k * 38, s * 70));
  const poleMat = new THREE.MeshStandardMaterial({ color: '#f3f2ee', roughness: 0.4, metalness: 0.3 });
  const lampMat = new THREE.MeshStandardMaterial({ color: '#fdf8e8', emissive: '#ffe9b8', emissiveIntensity: 0 });
  const poles = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.25, 0.45, 26, 8).translate(0, 13, 0), poleMat, masts.length);
  const lamps = new THREE.InstancedMesh(new THREE.BoxGeometry(2.6, 1.2, 1.2).translate(0, 26.2, 0), lampMat, masts.length);
  const m = new THREE.Matrix4();
  masts.forEach(([x, z], i) => { m.makeTranslation(x, groundAt(x, z), z); poles.setMatrixAt(i, m); lamps.setMatrixAt(i, m); });
  poles.castShadow = true; g.add(poles, lamps);

  // ---- people for scale (Visualization) ----
  const people = [];
  const rnd = mulberry(11);
  for (let i = 0; i < 300; i++) {
    const t = rnd() * Math.PI * 2, r = Math.sqrt(rnd());
    let along, across;
    if (i < 140) { along = plazaC + Math.sin(t) * depth * 0.8 * r; across = Math.cos(t) * half * 0.85 * r; }
    else if (i < 230) { along = rN + 6 + rnd() * (plazaC - rN - 10); across = (rnd() - 0.5) * 140; }
    else { const a = rnd() * Math.PI * 2, rr = 6 + rnd() * 10; const ux = Math.cos(a), uz = Math.sin(a); const ro = rayRadius(features.bowl_outer, ux, uz) + rr; people.push({ x: ux * ro, z: uz * ro, a: rnd() * 6.28, s: 0.6 + rnd() * 0.8, c: i }); continue; }
    const [x, z] = local(along, across);
    if (Math.abs(along - poolC) < poolW / 2 + 6 && Math.abs(across) < poolL / 2 + 6) continue;
    people.push({ x, z, a: rnd() * 6.28, s: 0.6 + rnd() * 0.8, c: i });
  }
  const body = new THREE.CapsuleGeometry(0.24, 1.15, 3, 8); body.translate(0, 0.83, 0);
  const crowd = new THREE.InstancedMesh(body, new THREE.MeshStandardMaterial({ roughness: 0.8 }), people.length);
  const palette = ['#b3121b', '#1f6b3a', '#1b1a18', '#f2f0ea', '#2f4e7a', '#c9a227', '#7a4b2a', '#b3121b'];
  const col = new THREE.Color();
  people.forEach((p, i) => { m.makeTranslation(p.x, pad + 0.15, p.z); crowd.setMatrixAt(i, m); crowd.setColorAt(i, col.set(palette[p.c % palette.length])); });
  crowd.castShadow = true; crowd.name = 'people';
  g.add(crowd);

  const dummy = new THREE.Object3D();
  function update(time, night) {
    jets.forEach((j, i) => {
      const h = j.h * (0.55 + 0.45 * Math.sin(time * 1.3 + j.ph) ** 2);
      dummy.position.set(j.x, waterY, j.z); dummy.scale.set(1, h, 1); dummy.updateMatrix(); jetMesh.setMatrixAt(i, dummy.matrix);
      dummy.position.set(j.x, waterY + h, j.z); dummy.scale.setScalar(0.6 + 0.6 * (h / j.h)); dummy.updateMatrix(); capMesh.setMatrixAt(i, dummy.matrix);
    });
    jetMesh.instanceMatrix.needsUpdate = capMesh.instanceMatrix.needsUpdate = true;
    const hue = (time * 0.05) % 1;
    jetMat.emissive.setHSL(night > 0.3 ? 0.75 + 0.2 * Math.sin(time * 0.4) : 0, night > 0.3 ? 0.8 : 0, night > 0.3 ? 0.6 : 1);
    jetMat.emissiveIntensity = 0.15 + night * 2.2;
    water.material.emissive.setHSL(0.78 + 0.08 * Math.sin(hue * 6.28), 0.7, 0.35);
    water.material.emissiveIntensity = night * 0.8;
    lampMat.emissiveIntensity = night * 6;
    for (let i = 0; i < people.length; i += 7) { const p = people[i]; p.x += Math.cos(p.a) * 0.02 * p.s; p.z += Math.sin(p.a) * 0.02 * p.s; m.makeTranslation(p.x, pad + 0.15, p.z); crowd.setMatrixAt(i, m); }
    crowd.instanceMatrix.needsUpdate = true;
  }
  return { group: g, update, fountain, plaza: { x: px, z: pz }, pool: { x: fx2, z: fz2 }, crowd, peopleCount: people.length };
}

function mulberry(a) { return () => { a |= 0; a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

function tex(w, h, draw) {
  const cv = document.createElement('canvas'); cv.width = w; cv.height = h; draw(cv.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t;
}
function plazaTexture() {
  return tex(1024, 512, (x, w, h) => {
    x.fillStyle = '#dcd6cb'; x.fillRect(0, 0, w, h);
    x.strokeStyle = 'rgba(150,140,128,0.55)'; x.lineWidth = 3;
    for (let k = 1; k <= 4; k++) { x.beginPath(); x.ellipse(w / 2, h / 2, (w / 2) * (k / 4.4), (h / 2) * (k / 4.4), 0, 0, Math.PI * 2); x.stroke(); }
    for (let a = 0; a < 24; a++) { const t = (a / 24) * Math.PI * 2; x.beginPath(); x.moveTo(w / 2 + Math.cos(t) * 40, h / 2 + Math.sin(t) * 20); x.lineTo(w / 2 + Math.cos(t) * w, h / 2 + Math.sin(t) * h); x.stroke(); }
    x.fillStyle = 'rgba(120,60,40,0.25)'; x.beginPath(); x.ellipse(w / 2, h / 2, 120, 60, 0, 0, Math.PI * 2); x.fill();
    for (let i = 0; i < 4000; i++) { x.fillStyle = `rgba(0,0,0,${Math.random() * 0.04})`; x.fillRect(Math.random() * w, Math.random() * h, 2, 2); }
  });
}
function flowerTexture() {
  return tex(256, 256, (x, w, h) => {
    x.fillStyle = '#3f6b2e'; x.fillRect(0, 0, w, h);
    const c = ['#e6c229', '#d6402a', '#f2efe6', '#b3121b', '#e6c229'];
    for (let i = 0; i < 1600; i++) { x.fillStyle = c[i % c.length]; x.beginPath(); x.arc(Math.random() * w, Math.random() * h, 2 + Math.random() * 2, 0, 7); x.fill(); }
  });
}
