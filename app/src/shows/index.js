import * as THREE from 'three/webgpu';
import { attribute, instanceColor, uniform, vec3, float, mix, sin, step } from 'three/tsl';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { Timeline, night_show } from './timeline.js';
import { fallbackFacadeLines, validFacadeLines, padY } from './geometry.js';
import { limits } from './shapes.js';
import { showState } from './state.js';

function strips(data) {
  const parts = [...data.ribs, data.fascia, data.opening].map((line, index) => {
    const curve = new THREE.CatmullRomCurve3(line.map(p => new THREE.Vector3(...p)));
    const g = new THREE.TubeGeometry(curve, Math.max(1, line.length - 1), 0.48, 4, false);
    const angle = Math.atan2(line[0][2], line[0][0]);
    g.setAttribute('ribIndex', new THREE.Float32BufferAttribute(new Float32Array(g.attributes.position.count).fill(index), 1));
    g.setAttribute('ribAngle', new THREE.Float32BufferAttribute(new Float32Array(g.attributes.position.count).fill(((angle / (2 * Math.PI)) + 1) % 1), 1));
    return g;
  });
  const merged = mergeGeometries(parts); parts.forEach(g => g.dispose()); return merged;
}

export function installShows({ scene, camera, renderer, heroGroup, bowlGroup, clock }) {
  const budget = limits(globalThis.innerWidth ?? 1024);
  const root = new THREE.Group(); root.name = 'shows-visualization'; root.userData.claim = 'simulation';
  // Export coordinates are stadium-local. Only the procedural pad elevation is inherited.
  root.position.y = bowlGroup?.position.y ?? padY; scene.add(root);
  const timeline = new Timeline(), enabled = new Map(['SHW-01', 'SHW-02', 'SHW-03'].map(id => [id, false]));
  const time = uniform(0), mode = uniform(0), tint = uniform(new THREE.Color('white'));
  const a = attribute('ribAngle', 'float'), rib = attribute('ribIndex', 'float');
  const band = mix(vec3(0.012), vec3(1), step(0.3, a));
  const red = mix(band, vec3(1, 0.015, 0.025), step(0.35, a));
  const edge = mix(red, vec3(1), step(0.65, a));
  const flag = mix(edge, vec3(0.01, 0.65, 0.08), step(0.7, a));
  const wave = sin(a.mul(Math.PI * 8).sub(time.mul(2))).mul(0.45).add(0.55);
  const chase = step(0.65, sin(rib.mul(0.45).sub(time.mul(4)))).mul(0.9).add(0.1);
  const color = mix(vec3(1), flag, step(0.5, mode));
  const movement = mix(float(1), chase, step(1.5, mode));
  const pulse = mix(movement, wave, step(2.5, mode));
  const facadeMaterial = new THREE.MeshStandardNodeMaterial({ color: 0x101010, roughness: 0.5 });
  facadeMaterial.emissiveNode = color.mul(pulse).mul(tint).mul(5);
  const lampMaterial = new THREE.MeshStandardNodeMaterial({ color: 0xffffff });
  lampMaterial.emissiveNode = instanceColor.mul(8);
  const droneMaterial = new THREE.MeshStandardNodeMaterial({ color: 0xffffff });
  droneMaterial.emissiveNode = instanceColor.mul(10);
  const droneGeo = new THREE.OctahedronGeometry(0.65, 0);
  const drones = new THREE.InstancedMesh(droneGeo, droneMaterial, budget.drones); drones.name = 'SHW-03'; drones.frustumCulled = false; drones.visible = false; root.add(drones);
  // The emissive node reads instanceColor, so the buffer must exist before the first compile.
  for (let i = 0; i < budget.drones; i++) drones.setColorAt(i, new THREE.Color(0, 0, 0));
  const lampGeo = new THREE.BoxGeometry(1.6, 0.7, 1.1);
  let facade, lamps, lights = [], data, disposed = false, scripted = false;
  const dummy = new THREE.Object3D(), c = new THREE.Color();
  const create = geometry => {
    if (disposed) return;
    if (facade) { root.remove(facade, lamps); facade.geometry.dispose(); lights.forEach(l => { root.remove(l, l.target); l.dispose(); }); }
    data = geometry;
    facade = new THREE.Mesh(strips(data), facadeMaterial); facade.name = 'SHW-02'; root.add(facade);
    lamps = new THREE.InstancedMesh(lampGeo, lampMaterial, data.floodlights.length); lamps.name = 'SHW-01'; lamps.frustumCulled = false; root.add(lamps);
    data.floodlights.forEach((l, i) => { dummy.position.set(...l.pos); dummy.lookAt(...l.aim); dummy.updateMatrix(); lamps.setMatrixAt(i, dummy.matrix); lamps.setColorAt(i, c.setRGB(0, 0, 0)); });
    lights = Array.from({ length: budget.lights }, (_, i) => {
      const l = data.floodlights[Math.floor(i / budget.lights * data.floodlights.length)];
      const light = new THREE.SpotLight(0xffffff, 0, 250, Math.PI / 7, 0.5, 2); light.castShadow = false;
      light.position.set(...l.pos); light.target.position.set(...l.aim); root.add(light, light.target); return light;
    });
  };
  create(fallbackFacadeLines());
  // The optional export replaces all fallback line geometry without changing the API.
  const controller = new AbortController();
  const ready = typeof window === 'undefined' ? Promise.resolve() : fetch('./data/facade_lines.json', { signal: controller.signal }).then(async response => {
    if (response.status === 404) return;
    if (!response.ok) throw new Error(`Facade lines request failed: ${response.status}`);
    const json = await response.json(); if (!validFacadeLines(json)) throw new Error('Invalid facade lines export'); create(json);
  }).catch(error => { if (!disposed) console.warn('Shows use estimated fallback geometry:', error.message); });
  function update(dtSeconds = 0, timeSeconds) {
    if (disposed) return;
    const cues = timeline.update(dtSeconds), t = scripted ? timeline.time : (timeSeconds ?? clock?.elapsedTime ?? 0); time.value = t;
    // THREE.Color retains all CSS colour forms accepted by the app.
    const cueColor = id => scripted ? cues.filter(c => c.module === id).at(-1)?.params.color : undefined;
    const colors = { facade: new THREE.Color(enabled.get('SHW-02') ? cueColor('SHW-02') ?? 'white' : 'white').toArray(),
      flood: new THREE.Color(enabled.get('SHW-01') ? cueColor('SHW-01') ?? 'white' : 'white').toArray() };
    const sampled = showState(cues, t, data, budget, { scripted, enabled: Object.fromEntries(enabled),
      viewer: camera?.getWorldPosition(new THREE.Vector3()), colors });
    const f = sampled['SHW-02']; facade.visible = f.visible;
    mode.value = f.mode; tint.value.setRGB(...f.tint);
    const flood = sampled['SHW-01']; lamps.visible = flood.visible;
    data.floodlights.forEach((_, i) => lamps.setColorAt(i, c.setRGB(...flood.rgb.slice(i * 3, i * 3 + 3))));
    lamps.instanceColor.needsUpdate = true;
    lights.forEach((l, i) => { l.intensity = flood.intensity[Math.floor(i / lights.length * data.floodlights.length)] * 180000; l.color.setRGB(...flood.color); });
    const drone = sampled['SHW-03']; drones.visible = drone.visible;
    if (drone.visible) {
      for (let i = 0; i < budget.drones; i++) {
        dummy.position.set(...drone.position.slice(i * 3, i * 3 + 3)); dummy.quaternion.identity(); dummy.updateMatrix();
        drones.setMatrixAt(i, dummy.matrix); drones.setColorAt(i, c.setRGB(...drone.rgb.slice(i * 3, i * 3 + 3)));
      }
      drones.instanceMatrix.needsUpdate = true; drones.instanceColor.needsUpdate = true;
    }
  }
  update(0, 0);
  return {
    timeline, ready,
    setEnabled(id, on) { if (!enabled.has(id)) throw new Error(`Unknown show: ${id}`); enabled.set(id, !!on); update(0); },
    play(name) { if (name !== 'night_show') throw new Error(`Unknown cue list: ${name}`); scripted = true; enabled.forEach((_, id) => enabled.set(id, true)); timeline.setCues(night_show).play(); update(0); },
    update,
    dispose() { if (disposed) return; disposed = true; controller.abort(); root.removeFromParent(); facade.geometry.dispose(); lampGeo.dispose(); droneGeo.dispose(); facadeMaterial.dispose(); lampMaterial.dispose(); droneMaterial.dispose(); lights.forEach(l => l.dispose()); },
  };
}
