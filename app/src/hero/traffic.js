import * as THREE from 'three/webgpu';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { instanceColor, mx_noise_float, sin, uv, vec2, vec3 } from 'three/tsl';

// Nganya model credit: app/public/vehicles/CREDITS.md
const CAR_PAINT = [0xf1f1ed, 0xf1f1ed, 0xd9dde0, 0xd9dde0, 0x242629, 0x242629, 0xb8443c, 0x315b91];
const NGANYA_PAINT = [0xf6f4ee, 0x572b8f, 0x18191c, 0x7fd338, 0xff1687, 0xf27c19];
const NEON = [0x39ff72, 0x9d46ff, 0xff36ba, 0x26e9ff, 0xff354c];
const CAR_SPECS = [
  { name: 'saloon', weight: 0.48, length: 4.45, width: 1.82, height: 1.25, wheelR: 0.34, ground: 0.69 },
  { name: 'estate', weight: 0.18, length: 4.35, width: 1.82, height: 1.48, wheelR: 0.34, ground: 0.69 },
  { name: 'suv', weight: 0.22, length: 4.75, width: 1.95, height: 1.72, wheelR: 0.42, ground: 0.82 },
  { name: 'pickup', weight: 0.12, length: 5.15, width: 1.95, height: 1.62, wheelR: 0.4, ground: 0.78 },
];
const BUS = { length: 11, width: 2.5, height: 3.15, wheelR: 0.5, ground: 1.05 };
const BODA = { length: 2, width: 0.78, height: 1.05, wheelR: 0.34, ground: 0.65 };
const rngOf = (seed) => () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
const lerp = (a, b, t) => a + (b - a) * t;

function makeLane(raw, name) {
  const points = (raw.points || raw.pts || []).map((p) => Array.isArray(p) ? [p[0], p[1] ?? 0, p[2] ?? 0] : [p.x, p.y ?? 0, p.z]);
  const cumulative = [0];
  for (let i = 1; i < points.length; i++) cumulative.push(cumulative[i - 1] + Math.hypot(points[i][0] - points[i - 1][0], points[i][2] - points[i - 1][2]));
  return { points, cumulative, length: cumulative.at(-1) || 0, name, leftLane: raw.leftLane, direction: raw.direction, vehicles: [] };
}

function pointAt(lane, distance) {
  const d = Math.max(0, Math.min(lane.length, distance));
  let i = 1;
  while (i < lane.cumulative.length - 1 && lane.cumulative[i] < d) i++;
  const a = lane.points[i - 1], b = lane.points[i], span = lane.cumulative[i] - lane.cumulative[i - 1] || 1;
  const t = (d - lane.cumulative[i - 1]) / span;
  return { x: lerp(a[0], b[0], t), y: lerp(a[1], b[1], t), z: lerp(a[2], b[2], t), dx: (b[0] - a[0]) / span, dz: (b[2] - a[2]) / span };
}

function wheelsGeometry(spec, count = 4) {
  const wheel = new THREE.CylinderGeometry(spec.wheelR, spec.wheelR, spec.wheelR * 0.55, 8);
  wheel.rotateX(Math.PI / 2);
  const out = [];
  const axles = count === 2 ? [-spec.length * 0.34, spec.length * 0.34] : count === 6 ? [-spec.length * 0.36, 0, spec.length * 0.36] : [-spec.length * 0.32, spec.length * 0.32];
  for (const x of axles) for (const z of count === 2 ? [0] : [-spec.width * 0.43, spec.width * 0.43]) {
    const g = wheel.clone(); g.translate(x, spec.wheelR, z); out.push(g);
  }
  wheel.dispose();
  return mergeGeometries(out, false);
}

function addBatch(group, instances, geometry, material, colorOf) {
  if (!instances.length) return null;
  const mesh = new THREE.InstancedMesh(geometry, material, instances.length);
  // Vehicles move every frame, so cached bounds go stale: skip frustum culling instead of recomputing them.
  mesh.castShadow = true; mesh.receiveShadow = true; mesh.frustumCulled = false; mesh.userData.claim = 'Visualization';
  if (colorOf) instances.forEach((v, i) => mesh.setColorAt(i, colorOf(v)));
  group.add(mesh);
  return mesh;
}

function carMeshes(group, spec, instances) {
  if (!instances.length) return [];
  const L = spec.length, W = spec.width, H = spec.height;
  const body = new THREE.BoxGeometry(L, H * 0.58, W);
  body.translate(0, spec.ground + H * 0.29, 0);
  const cabinLength = spec.name === 'estate' ? 0.62 : spec.name === 'pickup' ? 0.43 : 0.52;
  const cabin = new THREE.BoxGeometry(L * cabinLength, H * 0.42, W * 0.82);
  cabin.translate(spec.name === 'pickup' ? -L * 0.16 : -L * 0.02, spec.ground + H * 0.72, 0);
  const windows = new THREE.MeshStandardMaterial({ color: 0x253844, roughness: 0.34, metalness: 0.08, flatShading: true });
  const bodyMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.62, flatShading: true });
  const wheelMat = new THREE.MeshStandardMaterial({ color: 0x202224, roughness: 0.95, flatShading: true });
  const meshes = [
    addBatch(group, instances, body, bodyMat, (v) => new THREE.Color(v.color)),
    addBatch(group, instances, cabin, windows),
    addBatch(group, instances, wheelsGeometry(spec), wheelMat),
  ];
  if (spec.name === 'pickup') {
    const bed = new THREE.BoxGeometry(L * 0.36, H * 0.18, W * 0.78); bed.translate(L * 0.29, spec.ground + H * 0.68, 0);
    meshes.push(addBatch(group, instances, bed, bodyMat, (v) => new THREE.Color(v.color)));
  }
  return meshes.filter(Boolean);
}

function busMeshes(group, instances) {
  if (!instances.length) return [];
  const bodyGeo = new THREE.BoxGeometry(BUS.length, BUS.height, BUS.width); bodyGeo.translate(0, BUS.ground + BUS.height / 2, 0);
  const windowGeo = new THREE.BoxGeometry(BUS.length * 0.78, BUS.height * 0.34, BUS.width * 1.01); windowGeo.translate(-BUS.length * 0.02, BUS.ground + BUS.height * 0.75, 0);
  const bandGeo = new THREE.BoxGeometry(BUS.length * 0.97, BUS.height * 0.2, BUS.width * 1.02); bandGeo.translate(0, BUS.ground + BUS.height * 0.2, 0);
  const trimGeo = new THREE.BoxGeometry(0.18, 0.09, BUS.width * 1.03); trimGeo.translate(BUS.length * 0.48, BUS.ground + BUS.height * 0.31, 0);
  const wheelGeo = wheelsGeometry(BUS, 6);
  const white = new THREE.MeshStandardMaterial({ color: 0xf2f0eb, roughness: 0.68, flatShading: true });
  const dark = new THREE.MeshStandardMaterial({ color: 0x23313a, roughness: 0.38 });
  const red = new THREE.MeshStandardMaterial({ color: 0x8e1f32, roughness: 0.72, flatShading: true });
  const lamp = new THREE.MeshStandardMaterial({ color: 0xff263e, emissive: 0xd90c27, emissiveIntensity: 1.5 });
  const rubber = new THREE.MeshStandardMaterial({ color: 0x202224, roughness: 0.95, flatShading: true });
  return [addBatch(group, instances, bodyGeo, white), addBatch(group, instances, windowGeo, dark), addBatch(group, instances, bandGeo, red), addBatch(group, instances, trimGeo, lamp), addBatch(group, instances, wheelGeo, rubber)].filter(Boolean);
}

function bodaMeshes(group, instances) {
  if (!instances.length) return [];
  const frameGeo = new THREE.BoxGeometry(1.25, 0.24, 0.35); frameGeo.translate(0, 0.61, 0);
  const wheels = wheelsGeometry(BODA, 2);
  const riderGeo = new THREE.BoxGeometry(0.48, 0.62, 0.38); riderGeo.translate(-0.08, 1.23, 0);
  const headGeo = new THREE.IcosahedronGeometry(0.19, 0); headGeo.translate(0.12, 1.66, 0);
  const barGeo = new THREE.BoxGeometry(0.72, 0.11, 0.12); barGeo.translate(0.48, 1.12, 0);
  const bikeMat = new THREE.MeshStandardMaterial({ color: 0xd13931, roughness: 0.72, flatShading: true });
  const tireMat = new THREE.MeshStandardMaterial({ color: 0x202224, roughness: 0.95 });
  const riderMat = new THREE.MeshStandardMaterial({ color: 0x344b74, roughness: 0.86, flatShading: true });
  const skinMat = new THREE.MeshStandardMaterial({ color: 0x704832, roughness: 0.9, flatShading: true });
  return [addBatch(group, instances, frameGeo, bikeMat), addBatch(group, instances, wheels, tireMat), addBatch(group, instances, riderGeo, riderMat), addBatch(group, instances, headGeo, skinMat), addBatch(group, instances, barGeo, tireMat)].filter(Boolean);
}

function nganyaBodyMaterial() {
  const material = new THREE.MeshStandardNodeMaterial({ color: 0xffffff, roughness: 0.48, metalness: 0.03 });
  const tex = uv();
  const seed = instanceColor.r.mul(19).add(instanceColor.g.mul(31)).add(instanceColor.b.mul(13));
  const noise = mx_noise_float(tex.mul(22).add(vec2(seed, seed.mul(0.37))), 0.5, 0.5);
  const stripes = sin(tex.y.mul(72).add(tex.x.mul(11)).add(seed)).abs().oneMinus().step(0.62);
  const art = noise.mul(0.55).add(stripes.mul(0.8)).clamp(0, 1);
  material.colorNode = vec3(art.mul(0.82).add(0.18), stripes.mul(0.78).add(noise.mul(0.32)).add(0.12), noise.mul(0.82).add(0.18));
  return material;
}

function prepareNganya(scene) {
  scene.updateMatrixWorld(true);
  const axis = new THREE.Matrix4().set(0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1);
  const sourceByMaterial = new Map();
  scene.traverse((node) => {
    if (!node.isMesh || /font mask/i.test(node.name)) return;
    const name = node.material?.name;
    if (!['Plane__0', 'LIGHTS', 'window', 'BLACK', 'LIGT'].includes(name)) return;
    const geometry = node.geometry.clone();
    geometry.applyMatrix4(node.matrixWorld);
    geometry.applyMatrix4(axis);
    if (!geometry.getAttribute('normal')) geometry.computeVertexNormals();
    if (!sourceByMaterial.has(name)) sourceByMaterial.set(name, []);
    sourceByMaterial.get(name).push(geometry);
  });
  const combined = new Map();
  const bounds = new THREE.Box3();
  for (const [name, list] of sourceByMaterial) {
    const geometry = mergeGeometries(list, false);
    if (!geometry) continue;
    geometry.computeBoundingBox(); bounds.union(geometry.boundingBox);
    combined.set(name, geometry);
  }
  const length = bounds.max.x - bounds.min.x;
  if (!Number.isFinite(length) || length <= 0) throw new Error('Nganya model has no usable length axis');
  const scale = 7 / length;
  const normalize = new THREE.Matrix4().makeScale(scale, scale, scale);
  normalize.setPosition(-((bounds.min.x + bounds.max.x) / 2) * scale, -bounds.min.y * scale, -((bounds.min.z + bounds.max.z) / 2) * scale);
  for (const geometry of combined.values()) { geometry.applyMatrix4(normalize); geometry.computeVertexNormals(); geometry.computeBoundingBox(); }
  return combined;
}

/** Build instanced traffic for the supplied lane polylines. */
export function buildTraffic({ lines, groundAt, camera, count = 400, proxyDistance = 350 } = {}) {
  const group = new THREE.Group(); group.name = 'traffic'; group.userData.claim = 'Visualization';
  const random = rngOf(0x51a7a);
  const rawLanes = Array.isArray(lines) ? lines.map((lane) => [lane.name, lane]) : (lines?.roads || []).flatMap((road) => (road.lanes || []).map((lane) => [road.name, lane]));
  const lanes = rawLanes.map(([name, raw]) => makeLane(raw, name)).filter((lane) => lane.points.length > 1 && lane.length > 30);
  if (!lanes.length || count <= 0) return { group, update() {}, setLimit() {} };
  const laneTotal = lanes.reduce((sum, lane) => sum + lane.length, 0);
  const weightedLane = () => {
    let n = random() * laneTotal;
    for (const lane of lanes) { n -= lane.length; if (n <= 0) return lane; }
    return lanes.at(-1);
  };
  const cars = new Map(CAR_SPECS.map((spec) => [spec, []])), buses = [], bodas = [], nganyas = [];
  const fleet = Array.from({ length: Math.floor(count) }, () => {
    const lane = weightedLane(), v = { lane, distance: 0, target: (30 + random() * 30) / 3.6, speed: 0, cooldown: 0, index: 0 };
    lane.vehicles.push(v); return v;
  });
  function assignMix(vehicles, mix) {
    const entries = Object.entries(mix).map(([kind, share]) => ({ kind, quota: vehicles.length * share }));
    let assigned = entries.map((entry) => ({ ...entry, count: Math.floor(entry.quota), fraction: entry.quota % 1 }));
    let remaining = vehicles.length - assigned.reduce((n, entry) => n + entry.count, 0);
    assigned.sort((a, b) => b.fraction - a.fraction);
    for (let i = 0; i < remaining; i++) assigned[i].count++;
    for (let i = vehicles.length - 1; i > 0; i--) { const j = Math.floor(random() * (i + 1)); [vehicles[i], vehicles[j]] = [vehicles[j], vehicles[i]]; }
    let index = 0;
    for (const entry of assigned) for (let i = 0; i < entry.count; i++) {
      const v = vehicles[index++]; v.kind = entry.kind;
      if (v.kind === 'car') {
        let pick = random(); v.spec = CAR_SPECS.find((spec) => (pick -= spec.weight) < 0) || CAR_SPECS[0];
        v.color = CAR_PAINT[Math.floor(random() * CAR_PAINT.length)]; cars.get(v.spec).push(v);
      } else if (v.kind === 'nganya') {
        v.color = new THREE.Color(NGANYA_PAINT[Math.floor(random() * NGANYA_PAINT.length)]).multiplyScalar(0.9 + random() * 0.2).getHex();
        v.neon = NEON[Math.floor(random() * NEON.length)]; nganyas.push(v);
      } else if (v.kind === 'bus') buses.push(v);
      else bodas.push(v);
    }
  }
  assignMix(fleet.filter((v) => v.lane.name?.toLowerCase() === 'ngong road'), { car: 0.55, nganya: 0.25, bus: 0.12, boda: 0.08 });
  assignMix(fleet.filter((v) => v.lane.name?.toLowerCase() !== 'ngong road'), { car: 0.82, nganya: 0.10, boda: 0.08 });
  for (const v of [...buses, ...nganyas]) {
    if (v.lane.leftLane || random() > .85) continue;
    const candidates = lanes.filter((l) => l.name === v.lane.name && l.direction === v.lane.direction && l.leftLane);
    if (!candidates.length) continue;
    v.lane.vehicles.splice(v.lane.vehicles.indexOf(v), 1);
    v.lane = candidates[Math.floor(random() * candidates.length)]; v.lane.vehicles.push(v);
  }
  const vehicleLength = (v) => v.kind === 'bus' ? BUS.length : v.kind === 'nganya' ? 7 : v.kind === 'boda' ? BODA.length : v.spec.length;
  for (const lane of lanes) {
    let cursor = 16;
    for (const v of lane.vehicles) {
      v.distance = cursor; cursor += vehicleLength(v) + 8 + random() * 12;
      if (cursor > lane.length - 16) { v.distance = -20; v.cooldown = 1 + random() * 8; }
      else v.speed = v.target;
    }
    const active = lane.vehicles.filter((v) => v.distance >= 0);
    const occupied = active.at(-1)?.distance || 1;
    const stretch = Math.max(1, (lane.length - 24) / (occupied + 12));
    for (const v of active) v.distance *= stretch;
  }
  // Mapped road endpoints provide estimated junction queue locations, not a signal plan.
  for (const lane of lanes) {
    lane.junctions = [];
    if (lane.name?.toLowerCase() !== 'ngong road') continue;
    for (const other of lanes.filter((l) => l.name !== lane.name)) for (const p of [other.points[0], other.points.at(-1)]) {
      let best = 30, station = 0;
      lane.points.forEach((q, i) => { const d = Math.hypot(p[0] - q[0], p[2] - q[2]); if (d < best) { best = d; station = lane.cumulative[i]; } });
      if (best < 30 && station > 50 && station < lane.length - 50 && !lane.junctions.some((s) => Math.abs(s - station) < 40)) lane.junctions.push(station);
    }
  }
  const carMeshesBySpec = new Map([...cars].map(([spec, vehicles]) => [spec, carMeshes(group, spec, vehicles)]));
  const carMeshesAll = [...carMeshesBySpec.values()].flat();
  const busMeshesAll = busMeshes(group, buses), bodaMeshesAll = bodaMeshes(group, bodas);

  const proxyGeo = new THREE.BoxGeometry(7, 2.5, 2.25); proxyGeo.translate(0, 1.28, 0);
  const proxyMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.72, flatShading: true });
  const proxies = addBatch(group, nganyas, proxyGeo, proxyMat, (v) => new THREE.Color(v.color));
  const underGeo = new THREE.BoxGeometry(6.4, 0.055, 1.72); underGeo.translate(0, 0.12, 0);
  const underMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.85, blending: THREE.AdditiveBlending, depthWrite: false });
  const underglow = addBatch(group, nganyas, underGeo, underMat, (v) => new THREE.Color(v.neon));
  let modelMeshes = [], modelReady = false;
  if (nganyas.length) {
    try {
      new GLTFLoader().load('./vehicles/nganya/scene.gltf', (gltf) => {
        try {
          const geometries = prepareNganya(gltf.scene);
          const materialOf = new Map([
            ['Plane__0', nganyaBodyMaterial()],
            ['LIGHTS', new THREE.MeshStandardNodeMaterial({ color: 0xffffff, emissive: 0xffffff, emissiveIntensity: 2.2, roughness: 0.4 })],
            ['window', new THREE.MeshStandardMaterial({ color: 0x15252d, roughness: 0.3, metalness: 0.08 })],
            ['BLACK', new THREE.MeshStandardMaterial({ color: 0x111214, roughness: 0.85 })],
            ['LIGT', new THREE.MeshStandardNodeMaterial({ color: 0xffffff, emissive: 0xffffff, emissiveIntensity: 2.6, roughness: 0.35 })],
          ]);
          for (const [name, geometry] of geometries) {
            const material = materialOf.get(name);
            if (name === 'LIGHTS' || name === 'LIGT') material.emissiveNode = instanceColor;
            const mesh = new THREE.InstancedMesh(geometry, material, nganyas.length);
            mesh.count = 0; mesh.visible = false; mesh.castShadow = true; mesh.receiveShadow = true; mesh.userData.claim = 'Visualization';
            mesh.frustumCulled = false; group.add(mesh); modelMeshes.push({ name, mesh });
          }
          modelReady = modelMeshes.some(({ name }) => name === 'Plane__0');
        } catch (error) { console.warn('Nganya model setup failed; box proxies stay active.', error); }
      }, undefined, (error) => console.warn('Nganya model load failed; box proxies stay active.', error));
    } catch (error) { console.warn('Nganya model load failed; box proxies stay active.', error); }
  }
  for (const spec of CAR_SPECS) cars.get(spec).forEach((v, i) => { v.index = i; });
  buses.forEach((v, i) => { v.index = i; }); bodas.forEach((v, i) => { v.index = i; });

  const rootMatrix = new THREE.Matrix4(), rotation = new THREE.Quaternion(), position = new THREE.Vector3(), scale = new THREE.Vector3(1, 1, 1), up = new THREE.Vector3(0, 1, 0), color = new THREE.Color();
  function updateStats() {
    const visible = group.children.filter((mesh) => mesh.visible && mesh.count > 0);
    group.userData.drawCalls = visible.length;
    group.userData.triangles = visible.reduce((sum, mesh) => sum + (mesh.geometry.index?.count ?? mesh.geometry.getAttribute('position').count) / 3 * mesh.count, 0);
  }
  function vehicleMatrix(v) {
    const p = pointAt(v.lane, v.distance), terrainY = groundAt?.(p.x, p.z), y = (Number.isFinite(terrainY) ? terrainY : p.y) + 0.015;
    const edge = Math.max(0, Math.min(1, v.distance / 15, (v.lane.length - v.distance) / 15));
    scale.setScalar(edge); position.set(p.x, y + (v.lane.name?.toLowerCase() === 'ngong road' ? .4 : .02), p.z); rotation.setFromAxisAngle(up, Math.atan2(-p.dz, p.dx));
    rootMatrix.compose(position, rotation, scale);
    return rootMatrix;
  }
  // A quality downgrade can lower the live vehicle count; vehicles past the limit are parked out of sight.
  let limit = fleet.length; const hidden = new THREE.Matrix4().makeScale(0, 0, 0);
  fleet.forEach((v, i) => { v.order = i; });
  function setLimit(n) { limit = Math.max(0, Math.min(fleet.length, Math.floor(n))); }
  let elapsed = 0;
  function update(dt) {
    const stepDt = Math.max(0, Math.min(0.25, dt || 0)); elapsed += stepDt;
    for (const lane of lanes) {
      const ordered = lane.vehicles.filter((v) => v.distance >= 0).sort((a, b) => b.distance - a.distance);
      let leader = null;
      for (const v of ordered) {
        let desired = v.target;
        for (const station of lane.junctions || []) {
          const approach = station - v.distance;
          if (approach > 0 && approach < 65 && Math.sin(elapsed * .17 + station) > .2) desired = Math.min(desired, 3 + approach * .13);
        }
        const clearance = leader ? Math.max(0, leader.distance - v.distance - (vehicleLength(v) + vehicleLength(leader)) / 2 - 3) : Infinity;
        desired = Math.min(desired, Math.sqrt(2 * 3 * clearance));
        v.speed = Math.max(0, Math.min(desired, v.speed + 1.6 * stepDt));
        v.distance += Math.min(v.speed * stepDt, clearance);
        if (v.distance >= lane.length) { v.distance = -20; v.speed = 0; v.cooldown = 1 + random() * 3; }
        else leader = v;
      }
      let first = lane.vehicles.filter((v) => v.distance >= 0).reduce((a, v) => Math.min(a, v.distance - vehicleLength(v) / 2), Infinity);
      for (const v of lane.vehicles.filter((v) => v.distance < 0)) {
        v.cooldown -= stepDt;
        if (v.cooldown <= 0 && first > vehicleLength(v) / 2 + 12) { v.distance = 0; v.speed = 0; first = -vehicleLength(v) / 2; }
      }
    }
    for (const v of [...fleet]) if (v.kind === 'car' || v.kind === 'bus' || v.kind === 'boda') {
      const matrix = v.order < limit && v.distance >= 0 ? vehicleMatrix(v) : hidden;
      // Each car style has its own batch; v.index is the vehicle's slot in that batch.
      const meshes = v.kind === 'car' ? carMeshesBySpec.get(v.spec) : v.kind === 'bus' ? busMeshesAll : bodaMeshesAll;
      for (const mesh of meshes) mesh.setMatrixAt(v.index, matrix);
    }
    for (const mesh of [...carMeshesAll, ...busMeshesAll, ...bodaMeshesAll]) mesh.instanceMatrix.needsUpdate = true;
    if (!nganyas.length) { updateStats(); return; }
    let near = 0, far = 0;
    const cameraPos = camera?.position;
    for (const v of nganyas) {
      if (v.order >= limit || v.distance < 0) continue;
      const matrix = vehicleMatrix(v);
      const isFar = modelReady && cameraPos && cameraPos.distanceToSquared(position) > proxyDistance * proxyDistance;
      if (isFar || !modelReady) {
        proxies.setMatrixAt(far, matrix); proxies.setColorAt(far, color.set(v.color)); far++;
      } else {
        for (const entry of modelMeshes) {
          entry.mesh.setMatrixAt(near, matrix);
          if (entry.name === 'Plane__0') entry.mesh.setColorAt(near, color.set(v.color));
          else if (entry.name === 'LIGHTS' || entry.name === 'LIGT') entry.mesh.setColorAt(near, color.set(v.neon));
        }
        underglow.setMatrixAt(near, matrix); underglow.setColorAt(near, color.set(v.neon)); near++;
      }
    }
    proxies.count = far; proxies.visible = far > 0; proxies.instanceMatrix.needsUpdate = true; proxies.instanceColor.needsUpdate = true;
    underglow.count = near; underglow.visible = near > 0; underglow.instanceMatrix.needsUpdate = true; underglow.instanceColor.needsUpdate = true;
    for (const { mesh } of modelMeshes) { mesh.count = near; mesh.visible = near > 0; mesh.instanceMatrix.needsUpdate = true; if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true; }
    updateStats();
  }
  update(0);
  group.userData.kind = 'traffic'; group.userData.count = fleet.length; group.userData.typeCounts = { cars: [...cars.values()].reduce((n, a) => n + a.length, 0), nganyas: nganyas.length, buses: buses.length, bodas: bodas.length };
  group.userData.carStyleCounts = Object.fromEntries(CAR_SPECS.map((spec) => [spec.name, cars.get(spec).length]));
  const countRoadTypes = (list) => list.reduce((out, v) => { out[v.kind] = (out[v.kind] || 0) + 1; return out; }, {});
  group.userData.typeCountsByRoad = {
    ngong: countRoadTypes(fleet.filter((v) => v.lane.name?.toLowerCase() === 'ngong road')),
    other: countRoadTypes(fleet.filter((v) => v.lane.name?.toLowerCase() !== 'ngong road')),
  };
  return { group, update, setLimit };
}
