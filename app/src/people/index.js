import * as THREE from 'three/webgpu';
import { uniform, attribute, vec2, vec3, float, sin, cos, abs, max, smoothstep, mix, step, texture, floor, fract, select } from 'three/tsl';
import { figureGeometry, crowdAssets, loadCrowdAssets, crowdLevelIndex } from './geometry.js';
import { generateSeats } from './seats.js';
import { clampFill, occupancyOrder, selectSeats, crowdTier, partitionCrowd, standingPlaces, fanVariation } from './model.js';

// PPL-01 / PPL-02. Visualization only, not a validated safety simulation.
// quality can be a tier string or { seats, features, width, farDistance }.
// seats accepts the future Blender seats.json schema in parent-local metres.
export function installSeatedCrowd({ scene, camera, renderer, bowlGroup, heroGroup, quality = 'high', seats: seatList, features }) {
  // Accept the existing options and the older quality object.
  const config = { ...(typeof quality === 'object' ? quality : {}), ...(seatList ? { seats: seatList } : {}), ...(features ? { features } : {}) };
  const root = new THREE.Group();
  root.name = 'seated-crowd'; root.userData.claim = 'Visualization';
  // Drawn bowl seats are authoritative and use the bowl parent frame.
  const hasBowlSeats = bowlGroup?.getObjectByName('seats')?.isInstancedMesh;
  const parent = hasBowlSeats ? bowlGroup : heroGroup || bowlGroup || scene;
  parent.add(root);
  const u = { time: uniform(0), start: uniform(0), cheer: uniform(0), goal: uniform(0), end: uniform(1),
    wave: uniform(0), speed: uniform(12), perimeter: uniform(600), scarves: uniform(0), phones: uniform(0), night: uniform(0), duration: uniform(8) };
  let seats = [], order = [], fill = 1, meshes = [], dead = false, failure = null;
  let home = '#b92332', away = '#18733d';
  let waveAngle = (angle) => angle;
  root.userData.animation = u;
  const width = () => config.width ?? globalThis.innerWidth ?? 1024;
  let lastWidth = width();
  // A phone animation file holds only the low level, so the low tier is forced once it is loaded.
  const tier = () => crowdAssets() && !crowdAssets().levels.includes(0) ? 'low' : crowdTier(quality, width());
  const localCamera = new THREE.Vector3(), lastCamera = new THREE.Vector3(Infinity, Infinity, Infinity);
  function cameraPosition() {
    if (!camera) return localCamera.set(0, 0, 0);
    camera.getWorldPosition(localCamera); root.worldToLocal(localCamera); return localCamera;
  }
  let label;
  if (globalThis.document) {
    label = document.createElement('div');
    label.textContent = 'Visualization'; label.dataset.peopleVisualization = '';
    Object.assign(label.style, { position: 'fixed', top: '78px', left: '16px', zIndex: '1000', color: '#fff',
      background: 'rgba(0,0,0,.78)', padding: '5px 9px', borderRadius: '3px', font: '12px sans-serif', pointerEvents: 'none' });
    (renderer?.domElement?.parentElement || document.body).appendChild(label);
  }
  function material(lod) {
    const { manifest, texture: animation } = crowdAssets();
    const level = crowdLevelIndex(lod);
    const mat = new THREE.MeshBasicNodeMaterial({ side: THREE.DoubleSide });
    const phase = attribute('fanPhase', 'float'), angle = attribute('fanAngle', 'float');
    const elapsed = max(0, u.time.sub(u.start));
    const active = float(1).sub(step(u.duration, elapsed));
    const travel = elapsed.mul(u.speed).div(u.perimeter).mul(Math.PI * 2);
    const delta = cos(angle.sub(travel)).clamp(-1, 1).acos();
    const wave = float(1).sub(smoothstep(.06, .20, delta)).mul(u.wave).mul(active);
    const endMatch = step(0, attribute('fanEnd', 'float').mul(u.end));
    const cheer = max(u.cheer, u.goal.mul(endMatch)).mul(active);
    const scarf = u.scarves.mul(active), phone = u.phones.mul(u.night);
    const standing = config.standing === true;
    const slot = name => manifest.clips.find(c => c.name === name).slot;
    const clip = select(wave.greaterThan(.01), float(slot(standing ? 'cheer' : 'wave')),
      select(max(cheer, scarf).greaterThan(0), float(slot('cheer')),
        select(attribute('fanClap', 'float').greaterThan(.86), float(slot(standing ? 'Dance_Loop' : 'clap')), float(slot(standing ? 'Idle_Loop' : 'Sitting_Idle_Loop')))));
    // Uniform clip slots let replacement clips retain the runtime interface.
    let duration = float(manifest.clips[0].duration);
    for (const c of manifest.clips.slice(1)) duration = select(clip.equal(c.slot), float(c.duration), duration);
    const loop = fract(u.time.add(phase).div(duration));
    const waveProgress = standing ? float(.6) : float(.2).sub(sin(angle.sub(travel))).div(.4).clamp(0, 1);
    const reactionProgress = elapsed.div(2).min(.6).add(sin(u.time.mul(7).add(phase)).mul(.025).mul(elapsed.clamp(0, 1)));
    const progress = select(wave.greaterThan(.01), waveProgress, select(max(cheer, scarf).greaterThan(0), standing ? reactionProgress.max(.4) : reactionProgress, loop));
    const frame = progress.mul(manifest.framesPerClip - 1);
    const row = clip.add(level * manifest.clips.length).mul(manifest.framesPerClip).add(floor(frame));
    const x = attribute('fanVertex', 'float').add(.5).div(manifest.width);
    const sample = r => texture(animation, vec2(x, r.add(.5).div(manifest.height))).level(0).xyz;
    let animated = mix(sample(row), sample(row.add(1).min(clip.add(level * manifest.clips.length + 1).mul(manifest.framesPerClip).sub(1))), fract(frame));
    if (standing) {
      // Blend standing reactions from an idle stance without a seated pose.
      const idle = manifest.clips[slot('Idle_Loop')];
      const baseFrame = fract(u.time.add(phase).div(idle.duration)).mul(manifest.framesPerClip - 1);
      const baseRow = floor(baseFrame).add((level * manifest.clips.length + idle.slot) * manifest.framesPerClip);
      const base = mix(sample(baseRow), sample(baseRow.add(1)), fract(baseFrame));
      const blend = max(wave, max(cheer, scarf)).mul(elapsed.div(.25).clamp(0, 1));
      animated = mix(animated, mix(base, animated, blend), max(wave, max(cheer, scarf)));
    }
    const kind = attribute('kind', 'float');
    const isScarf = abs(kind.sub(3)).lessThan(.1), isPhone = abs(kind.sub(4)).lessThan(.1);
    const visible = select(isScarf, scarf, select(isPhone, phone, float(1)));
    const p = animated.mul(vec3(attribute('fanScale', 'vec2').x, attribute('fanScale', 'vec2').y, 1)).mul(visible);
    const yaw = attribute('fanYaw', 'float');
    // positionNode replaces the instanced position. Apply the origin once.
    mat.positionNode = attribute('fanOrigin', 'vec3').add(vec3(p.x.mul(cos(yaw)).add(p.z.mul(sin(yaw))), p.y, p.z.mul(cos(yaw)).sub(p.x.mul(sin(yaw)))));
    const skin = attribute('fanSkin', 'vec3'), trousers = attribute('fanTrousers', 'vec3');
    const shirt = attribute('fanShirt', 'vec3');
    mat.colorNode = select(isPhone, vec3(3), select(kind.equal(1), skin, select(kind.equal(2), trousers, shirt)));
    mat.userData.bakedAnimation = true;
    return mat;
  }
  function clearMeshes() {
    for (const mesh of meshes) { root.remove(mesh); mesh.geometry.dispose(); mesh.material.dispose(); mesh.dispose(); }
    meshes = [];
  }
  function rebuild() {
    if (dead || !crowdAssets()) return;
    clearMeshes();
    const picked = selectSeats(seats, fill, tier() === 'low' ? 767 : width(), order);
    const batches = partitionCrowd(seats, picked, tier(), cameraPosition(), config.farDistance ?? 60);
    lastCamera.copy(localCamera);
    const colors = [new THREE.Color(home), new THREE.Color(away), new THREE.Color('#ded9cc'), new THREE.Color('#292934')];
    for (const [lod, indices] of batches.entries()) {
      if (!indices.length) continue;
      const geometry = figureGeometry(lod);
      const values = { fanOrigin: [], fanYaw: [], fanPhase: [], fanAngle: [], fanEnd: [], fanShirt: [], fanSkin: [], fanTrousers: [], fanScale: [], fanClap: [] };
      const mesh = new THREE.InstancedMesh(geometry, material(lod), indices.length);
      const transform = new THREE.Object3D();
      indices.forEach((index, j) => {
        const seat = seats[index], variation = fanVariation(index);
        transform.position.set(seat.x, seat.y + .02, seat.z);
        transform.rotation.set(0, seat.facing_deg * Math.PI / 180, 0);
        transform.updateMatrix(); mesh.setMatrixAt(j, transform.matrix);
        values.fanOrigin.push(seat.x, seat.y + .02, seat.z); values.fanYaw.push(seat.facing_deg * Math.PI / 180);
        const end = seat.z >= 0 ? 1 : -1;
        const rand = variation.random;
        const team = rand < .72 ? (end > 0 ? 0 : 1) : rand < .88 ? 2 : 3;
        colors[team].toArray(values.fanShirt, j * 3);
        new THREE.Color(variation.skin).toArray(values.fanSkin, j * 3);
        new THREE.Color(variation.trousers).toArray(values.fanTrousers, j * 3);
        values.fanScale.push(...variation.scale); values.fanClap.push(variation.clap);
        values.fanPhase.push(rand * Math.PI * 2); values.fanAngle.push(waveAngle((Math.atan2(seat.z, seat.x) + Math.PI * 2) % (Math.PI * 2))); values.fanEnd.push(end);
      });
      for (const [name, value] of Object.entries(values)) {
        const size = ['fanOrigin', 'fanShirt', 'fanSkin', 'fanTrousers'].includes(name) ? 3 : name === 'fanScale' ? 2 : 1;
        geometry.setAttribute(name, new THREE.InstancedBufferAttribute(new Float32Array(value), size));
      }
      mesh.name = lod === 0 ? 'crowd-figures' : 'crowd-lod1'; mesh.userData.lod = lod;
      mesh.frustumCulled = false;
      root.add(mesh); meshes.push(mesh);
    }
    syncLabel();
  }
  function syncLabel() {
    let visible = !dead && meshes.some((mesh) => mesh.visible && mesh.count > 0);
    for (let p = root; p; p = p.parent) visible = visible && p.visible;
    if (label) {
      label.hidden = !visible;
      const compass = document.getElementById?.('compass')?.getBoundingClientRect();
      if (compass) { label.style.top = `${compass.bottom + 10}px`; label.style.left = `${compass.left}px`; }
    }
  }
  function accept(data) {
    if (dead) return;
    if (!Array.isArray(data) || data.some((s) => !['x', 'y', 'z', 'facing_deg'].every((k) => Number.isFinite(s[k])))) throw new Error('Crowd seat data is invalid');
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
  const initial = fromMesh(bowlGroup) || fromMesh(heroGroup) || config.seats || (config.features && generateSeats(config.features));
  const installedWithAssets = Boolean(crowdAssets());
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
  })();
  ready = Promise.all([ready, loadCrowdAssets({ quality: config.tier ?? quality, width: config.width })]).then(() => { if (!installedWithAssets) rebuild(); }).catch((error) => { failure = error; root.userData.error = error.message; if (label) { label.textContent = 'Visualization unavailable'; label.hidden = false; } throw error; });
  // Prevent an unhandled rejection when the host does not consume ready.
  ready.catch(() => {});
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
      if (tier() !== 'low' && cameraPosition().distanceTo(lastCamera) > 15) rebuild();
      syncLabel();
    },
    setNight(on) { u.night.value = Number(Boolean(on)); },
    dispose() { if (dead) return; dead = true; clearMeshes(); root.removeFromParent(); label?.remove(); },
  };
}

// Ground positions use the same figure, texture, controls, and claim label.
export function installStandingCrowd({ parent, area, count, quality = 'high', colours = {} }) {
  const places = standingPlaces(area, count);
  const crowd = installSeatedCrowd({ scene: parent, quality: { ...(typeof quality === 'object' ? quality : { tier: quality }),
    seats: places, standing: true } });
  crowd.group.name = 'standing-crowd';
  const home = Array.isArray(colours) ? colours[0] : colours.home;
  const away = Array.isArray(colours) ? colours[1] : colours.away;
  if (home || away) crowd.setPalette(home ?? '#b92332', away ?? '#18733d');
  return crowd;
}
