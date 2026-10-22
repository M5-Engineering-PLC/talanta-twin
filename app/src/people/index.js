import * as THREE from 'three/webgpu';
import { uniform, attribute, positionLocal, vec3, float, sin, cos, abs, max, min, smoothstep, mix, uv, step, color, cameraWorldMatrix, modelWorldMatrixInverse } from 'three/tsl';
import { figureGeometry } from './geometry.js';
import { generateSeats } from './seats.js';
import { clampFill, occupancyOrder, selectSeats } from './model.js';

// PPL-01 / PPL-02. Visualization only, not a validated safety simulation.
// quality can be a tier string or { seats, features, width, farDistance }.
// seats accepts the future Blender seats.json schema in parent-local metres.
export function installSeatedCrowd({ scene, camera, renderer, bowlGroup, heroGroup, quality = 'high', seats: seatList, features }) {
  // Seats and features may come as options or, for older callers, inside a quality object.
  const config = { ...(typeof quality === 'object' ? quality : {}), ...(seatList ? { seats: seatList } : {}), ...(features ? { features } : {}) };
  const root = new THREE.Group();
  root.name = 'seated-crowd'; root.userData.claim = 'Visualization';
  const parent = heroGroup || bowlGroup || scene;
  parent.add(root);
  const u = { time: uniform(0), start: uniform(0), cheer: uniform(0), goal: uniform(0), end: uniform(1),
    wave: uniform(0), speed: uniform(12), perimeter: uniform(600), scarves: uniform(0), phones: uniform(0), night: uniform(0), duration: uniform(8) };
  let seats = [], order = [], fill = 1, meshes = [], dead = false, failure = null;
  let home = '#b92332', away = '#18733d';
  let waveAngle = (angle) => angle;
  root.userData.animation = u;
  const width = () => config.width ?? globalThis.innerWidth ?? 1024;
  let lastWidth = width();
  let label;
  if (globalThis.document) {
    label = document.createElement('div');
    label.textContent = 'Visualization'; label.dataset.peopleVisualization = '';
    Object.assign(label.style, { position: 'fixed', bottom: '16px', left: '16px', zIndex: '1000', color: '#fff',
      background: 'rgba(0,0,0,.78)', padding: '5px 9px', borderRadius: '3px', font: '12px sans-serif', pointerEvents: 'none' });
    (renderer?.domElement?.parentElement || document.body).appendChild(label);
  }
  function material(cards) {
    const mat = new THREE.MeshBasicNodeMaterial({ side: THREE.DoubleSide, alphaTest: .5 });
    const phase = attribute('fanPhase', 'float'), angle = attribute('fanAngle', 'float');
    const elapsed = max(0, u.time.sub(u.start));
    const active = float(1).sub(step(u.duration, elapsed));
    const travel = elapsed.mul(u.speed).div(u.perimeter).mul(Math.PI * 2);
    const delta = cos(angle.sub(travel)).clamp(-1, 1).acos();
    const wave = float(1).sub(smoothstep(.06, .20, delta)).mul(u.wave);
    const endMatch = step(0, attribute('fanEnd', 'float').mul(u.end));
    const lift = max(wave, max(u.cheer, u.goal.mul(endMatch))).mul(active);
    const scarf = u.scarves.mul(active), phone = u.phones.mul(u.night);
    const raised = max(lift, scarf);
    const bob = sin(u.time.mul(1.7).add(phase)).mul(.012);
    const turn = sin(u.time.mul(.7).add(phase)).mul(.035);
    const shirt = attribute('fanShirt', 'vec3');
    if (cards) {
      const p = uv(), x = abs(p.x.sub(.5)), y = p.y;
      const head = float(1).sub(step(.1, p.sub(vec3(.5, .78, 0).xy).length()));
      const body = float(1).sub(step(.24, x)).mul(step(.18, y)).mul(float(1).sub(step(.68, y)));
      const arms = step(.28, x).mul(float(1).sub(step(.43, x))).mul(step(mix(.32, .60, raised), y)).mul(float(1).sub(step(mix(.6, .92, raised), y)));
      const scarfMask = step(.9, y).mul(scarf);
      const phoneMask = step(.85, y).mul(step(.35, p.x.sub(.5))).mul(phone);
      mat.opacityNode = max(max(head, body), max(arms, max(scarfMask, phoneMask)));
      mat.colorNode = mix(mix(shirt, color('#95633f'), head), color('#ffffff'), phoneMask);
      const local = positionLocal.mul(vec3(1, mix(1.25, 1.95, raised), 1));
      // Convert camera axes to parent-local axes, then undo the instance yaw.
      // Card matrices carry translation only.
      const right = modelWorldMatrixInverse.mul(cameraWorldMatrix.element(0)).xyz.normalize();
      const up = modelWorldMatrixInverse.mul(cameraWorldMatrix.element(1)).xyz.normalize();
      mat.positionNode = right.mul(local.x).add(up.mul(local.y.add(bob)));
    } else {
      const kind = attribute('kind', 'float');
      const isScarf = float(1).sub(step(.1, abs(kind.sub(3))));
      const isPhone = float(1).sub(step(.1, abs(kind.sub(4))));
      const visible = mix(float(1), scarf, isScarf).mul(mix(float(1), phone, isPhone));
      const p = positionLocal.mul(visible);
      const leg = float(1).sub(step(.1, abs(kind.sub(2))));
      const y = p.y.add(attribute('rise', 'float').mul(raised)).add(p.y.mul(raised).mul(leg)).add(bob);
      mat.positionNode = vec3(p.x.mul(cos(turn)).add(p.z.mul(sin(turn))), y, p.z.mul(float(1).sub(raised.mul(leg))).mul(cos(turn)).sub(p.x.mul(sin(turn))));
      const skin = float(1).sub(step(.1, abs(kind.sub(1))));
      const legs = float(1).sub(step(.1, abs(kind.sub(2))));
      mat.colorNode = mix(mix(mix(shirt, color('#95633f'), skin), color('#292934'), legs), color('#ffffff').mul(3), isPhone);
    }
    return mat;
  }
  function clearMeshes() {
    for (const mesh of meshes) { root.remove(mesh); mesh.geometry.dispose(); mesh.material.dispose(); mesh.dispose(); }
    meshes = [];
  }
  function rebuild() {
    clearMeshes();
    const picked = selectSeats(seats, fill, width(), order);
    if (!picked.length) { syncLabel(); return; }
    const colors = [new THREE.Color(home), new THREE.Color(away), new THREE.Color('#ded9cc'), new THREE.Color('#292934')];
    for (const cards of width() < 768 ? [true] : [false, true]) {
      const geometry = cards ? new THREE.PlaneGeometry(.8, 1).translate(0, .5, 0) : figureGeometry();
      const phase = [], angles = [], ends = [], shirts = [];
      const mesh = new THREE.InstancedMesh(geometry, material(cards), picked.length);
      const transform = new THREE.Object3D();
      picked.forEach((index, j) => {
        const seat = seats[index];
        transform.position.set(seat.x, seat.y + .02, seat.z);
        transform.rotation.set(0, cards ? 0 : seat.facing_deg * Math.PI / 180, 0);
        transform.updateMatrix(); mesh.setMatrixAt(j, transform.matrix);
        const end = seat.z >= 0 ? 1 : -1;
        const rand = (Math.sin(index * 17.13) * 43758.5 % 1 + 1) % 1;
        const team = rand < .72 ? (end > 0 ? 0 : 1) : rand < .88 ? 2 : 3;
        colors[team].toArray(shirts, j * 3);
        phase.push(rand * Math.PI * 2); angles.push(waveAngle((Math.atan2(seat.z, seat.x) + Math.PI * 2) % (Math.PI * 2))); ends.push(end);
      });
      geometry.setAttribute('fanPhase', new THREE.InstancedBufferAttribute(new Float32Array(phase), 1));
      geometry.setAttribute('fanAngle', new THREE.InstancedBufferAttribute(new Float32Array(angles), 1));
      geometry.setAttribute('fanEnd', new THREE.InstancedBufferAttribute(new Float32Array(ends), 1));
      geometry.setAttribute('fanShirt', new THREE.InstancedBufferAttribute(new Float32Array(shirts), 3));
      mesh.name = cards ? 'crowd-cards' : 'crowd-figures'; mesh.userData.cards = cards;
      mesh.frustumCulled = false; mesh.visible = cards === (width() < 768);
      root.add(mesh); meshes.push(mesh);
    }
    syncLabel();
  }
  function syncLabel() {
    let visible = !dead && meshes.some((mesh) => mesh.visible && mesh.count > 0);
    for (let p = root; p; p = p.parent) visible = visible && p.visible;
    if (label) label.hidden = !visible;
  }
  function accept(data) {
    if (dead) return;
    if (!Array.isArray(data) || !data.length || data.some((s) => !['x', 'y', 'z', 'facing_deg'].every((k) => Number.isFinite(s[k])))) throw new Error('Crowd seat data is invalid');
    seats = data.map((s) => ({ ...s, tier: s.tier ?? 0, row: s.row ?? 0 }));
    order = occupancyOrder(seats);
    // Map each azimuth onto arc length along a representative row.
    const ring = seats.filter((s) => s.tier === seats[0].tier && s.row === seats[0].row)
      .map((s) => ({ ...s, angle: (Math.atan2(s.z, s.x) + Math.PI * 2) % (Math.PI * 2) }))
      .sort((a, b) => a.angle - b.angle);
    const distances = [0];
    for (let i = 0; i < ring.length; i++) {
      const next = ring[(i + 1) % ring.length];
      distances.push(distances[i] + Math.hypot(next.x - ring[i].x, next.z - ring[i].z));
    }
    u.perimeter.value = distances.at(-1) || 600;
    waveAngle = (angle) => {
      if (ring.length < 2) return angle;
      if (angle < ring[0].angle) angle += Math.PI * 2;
      let lo = 0, hi = ring.length;
      while (lo + 1 < hi) { const mid = (lo + hi) >> 1; if (ring[mid].angle <= angle) lo = mid; else hi = mid; }
      const end = hi === ring.length ? ring[0].angle + Math.PI * 2 : ring[hi].angle;
      const arc = distances[lo] + (distances[hi] - distances[lo]) * (angle - ring[lo].angle) / (end - ring[lo].angle);
      return arc / u.perimeter.value * Math.PI * 2;
    };
    rebuild();
  }
  function fromMesh(group) {
    const source = group?.getObjectByName('seats');
    if (!source?.isInstancedMesh) return null;
    const m = new THREE.Matrix4(), relative = new THREE.Matrix4();
    parent.updateWorldMatrix(true, false); source.updateWorldMatrix(true, false);
    relative.copy(parent.matrixWorld).invert().multiply(source.matrixWorld);
    const result = [];
    for (let i = 0; i < source.count; i++) {
      source.getMatrixAt(i, m); m.premultiply(relative);
      result.push({ x: m.elements[12], y: m.elements[13], z: m.elements[14], facing_deg: Math.atan2(m.elements[8], m.elements[10]) * 180 / Math.PI, tier: 0, row: Math.round(m.elements[13] * 100) });
    }
    return result;
  }
  const initial = config.seats || (config.features && generateSeats(config.features)) || fromMesh(heroGroup) || fromMesh(bowlGroup);
  let ready;
  if (initial) { accept(initial); ready = Promise.resolve(); }
  else ready = (async () => {
    let response = await fetch('/data/seats.json');
    let data;
    if (response.ok && response.headers.get('content-type')?.includes('json')) data = await response.json();
    if (data) accept(data);
    else {
      response = await fetch('/data/manifest.json');
      if (!response.ok) throw new Error('Crowd manifest is unavailable');
      accept(generateSeats((await response.json()).features));
    }
  })().catch((error) => { failure = error; root.userData.error = error.message; if (label) { label.textContent = 'Visualization unavailable'; label.hidden = false; } throw error; });
  // Prevent an unhandled rejection when the host does not consume ready.
  ready.catch(() => {});
  const position = new THREE.Vector3(), center = new THREE.Vector3();
  return {
    ready, group: root,
    setFill(fraction) { fill = clampFill(fraction); if (!dead) rebuild(); },
    setPalette(homeHex, awayHex) { home = homeHex; away = awayHex; if (!dead) rebuild(); },
    react(name, params = {}) {
      if (dead) return;
      if (!['cheer', 'goal', 'wave', 'scarves', 'phones'].includes(name)) throw new Error(`Unknown crowd reaction: ${name}`);
      if (name === 'phones') { u.phones.value = params.on === false ? 0 : 1; return; }
      for (const key of ['cheer', 'goal', 'wave', 'scarves']) u[key].value = Number(key === name);
      u.start.value = u.time.value; u.duration.value = params.duration ?? (name === 'wave' ? 60 : 8);
      u.end.value = (params.end === 'away' || params.end === -1 || params === -1 || params === 'away') ? -1 : 1;
      u.speed.value = Number.isFinite(params.speed) ? params.speed : 12;
    },
    update(dtSeconds, timeSeconds) {
      if (dead || failure) return;
      u.time.value = Number.isFinite(timeSeconds) ? timeSeconds : u.time.value + Math.max(0, dtSeconds || 0);
      if (width() !== lastWidth) { lastWidth = width(); rebuild(); }
      camera.getWorldPosition(position); root.getWorldPosition(center);
      const far = width() < 768 || quality === 'low' || position.distanceTo(center) > (config.farDistance ?? 300);
      for (const mesh of meshes) mesh.visible = mesh.userData.cards === far;
      syncLabel();
    },
    setNight(on) { u.night.value = Number(Boolean(on)); },
    dispose() { if (dead) return; dead = true; clearMeshes(); root.removeFromParent(); label?.remove(); },
  };
}
