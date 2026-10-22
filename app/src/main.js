import * as THREE from 'three/webgpu';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { loadData, TOTAL_FILES } from './data.js';
import { makeTerrain, heightSampler, boxOf } from './world/terrain.js';
import { makeBuildings, makeRoads, makeTrees } from './world/context.js';
import { buildBowl } from './world/bowl.js';
import { buildPitch, pitchFeatures, buildSport } from './world/pitch.js';
import { ribbon, centroid, circlePts } from './world/geom.js';
import { sunPosition, eatDate, sunEvents, openingMinutes } from './sun.js';
import { initLanding } from './ui/landing.js';
import { lineChart } from './ui/charts.js';
import { buildSite } from './world/site.js';
import { pass, mrt, output, normalView, vec4 } from 'three/tsl';
import { ao } from 'three/addons/tsl/display/GTAONode.js';
import { bloom } from 'three/addons/tsl/display/BloomNode.js';
import { loadHero } from './hero/loadHero.js';
import { loadEnvironment, limitEnvToSpecular, horizonFogColor } from './hero/environment.js';
import { applyHeroToneMapping, heroGrade, applyHeroHaze } from './hero/heroLook.js';
import { getGradePreset } from './hero/grade.js';
import { initOverlay } from './hero/overlay.js';
import CAMS from '../cameras/manifest.json';
import { buildTraffic } from './hero/traffic.js';
import { buildCrowd } from './hero/crowd.js';
import { createTour, enableTouchUX } from './tour.js';
import { detectTier, TIERS, createFpsMonitor, profileGeometry } from './perf.js';

const $ = (s) => document.querySelector(s);
const smooth = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const DAY = 86400000;

// ---------------------------------------------------------------- boot
let loaded = 0;
const progress = () => { loaded++; $('#splash-bar').style.width = `${Math.min(100, (loaded / (TOTAL_FILES + 3)) * 100)}%`; };
const D = await loadData(progress);
const M = D.manifest;
const [LON, LAT] = M.origin_lonlat;
const F = M.features;
const PAD = F.site_pad_y;

const stage = $('#stage');
const params = new URLSearchParams(location.search);
const LITE = params.has('lite'); // software-GPU test mode
const renderer = new THREE.WebGPURenderer({ antialias: true, logarithmicDepthBuffer: true });
await renderer.init();
// Quality tier (app/src/perf.js): ?lite = low, ?tier=<high|medium|low>, ?fps shows the readout.
let tier = detectTier(renderer), quality = TIERS[tier];
renderer.setPixelRatio(Math.min(devicePixelRatio, quality.pixelRatio));
renderer.shadowMap.enabled = quality.shadows;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
$('#view').appendChild(renderer.domElement);
console.info('renderer backend:', renderer.backend?.isWebGPUBackend ? 'WebGPU' : 'WebGL2');

const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0xe7dfd1, 4000, 70000);
const camera = new THREE.PerspectiveCamera(42, 1, 1, 90000);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.dampingFactor = 0.08;
controls.maxPolarAngle = THREE.MathUtils.degToRad(87); controls.minDistance = 15; controls.maxDistance = 30000;

// ---------------------------------------------------------------- sky dome
const sky = new THREE.Mesh(new THREE.SphereGeometry(80000, 32, 16), new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.BackSide, fog: false, depthWrite: false }));
sky.geometry.setAttribute('color', new THREE.BufferAttribute(new Float32Array(sky.geometry.attributes.position.count * 3), 3));
sky.renderOrder = -1;
scene.add(sky);
function paintSky(zenith, horizon) {
  const p = sky.geometry.attributes.position, c = sky.geometry.attributes.color, a = new THREE.Color(), z = new THREE.Color(zenith), h = new THREE.Color(horizon);
  for (let i = 0; i < p.count; i++) { const t = Math.max(0, p.getY(i) / 80000); a.copy(h).lerp(z, Math.pow(t, 0.55)); c.setXYZ(i, a.r, a.g, a.b); }
  c.needsUpdate = true;
}

// ---------------------------------------------------------------- terrain
const texLoader = new THREE.TextureLoader();
const grounds = await Promise.all(M.ground.map(async (g) => {
  const t = await texLoader.loadAsync('./data/' + g.file); progress();
  t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  return { tex: t, meta: g };
}));
const [tSite, tFar, tHz] = M.terrain;
const holeOf = (inner, outer, drop) => ({ ...boxOf(inner), pad: outer.dx * 1.5, drop });
const terrainHz = makeTerrain(tHz, D.terrain[2], grounds[2], holeOf(tFar, tHz, 120));
const terrainFar = makeTerrain(tFar, D.terrain[1], grounds[1], holeOf(tSite, tFar, 60));
const terrainSite = makeTerrain(tSite, D.terrain[0], grounds[0], null);
terrainSite.name = 'terrain-site';
scene.add(terrainHz, terrainFar, terrainSite);
const groundAt = heightSampler(tSite, D.terrain[0]);
const terrains = [terrainSite, terrainFar, terrainHz];

// ---------------------------------------------------------------- context
const buildings = makeBuildings(D.bPos, D.bCol, D.bIdx, D.bSrc);
const BH = M.buildings.height_src, bEst = BH.default_by_area + BH.osm_floors;
const roads = makeRoads(D.rPos, D.rW, D.rIdx);
const trees = makeTrees(D.trees, quality.treeCount, tier === 'high' ? 2500 : tier === 'medium' ? 1200 : 800);
scene.add(buildings, roads, trees);

// ---------------------------------------------------------------- stadium
const bowl = buildBowl(F, { tier });
bowl.group.position.y = PAD;
scene.add(bowl.group);
// Stage 01 round trip: ?blender shows the Blender blockout (glTF, built from gis/parameter_ledger.csv)
// in place of the procedural bowl and pitch. The procedural bowl stays the default.
const BLENDER = new URLSearchParams(location.search).has('blender');
let blockout = null;
if (BLENDER) {
  new GLTFLoader().load('./data/blockout.glb', (g) => {
    blockout = g.scene; blockout.name = 'blender-blockout';
    blockout.traverse((o) => { if (o.isMesh) { o.castShadow = o.receiveShadow = true; if (o.name === 'site_pad') o.visible = false; } });
    scene.add(blockout);
    bowl.group.visible = false; pitch.group.visible = false;
    console.info('blender blockout loaded:', blockout.children.length, 'objects');
  }, undefined, (e) => console.warn('blender blockout failed to load', e));
}
const pitch = buildPitch(F.pitch_bearing_deg);
pitch.group.position.y = PAD;
scene.add(pitch.group);
const sport = buildSport(F.sport, PAD);
scene.add(sport.group);
const PF = pitchFeatures(F.pitch_bearing_deg);
const site = buildSite(F, bowl, groundAt, PAD);
scene.add(site.group);
console.info('seats modelled:', bowl.seatCount, '· people:', site.peopleCount);

const siteLine = new THREE.Mesh(ribbon(F.site, 2.2, (x, z) => groundAt(x, z) + 0.9, true, true), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.85, side: THREE.DoubleSide }));
siteLine.name = 'site-boundary';
scene.add(siteLine);

// ---------------------------------------------------------------- lights
const hemi = new THREE.HemisphereLight(0xdfe6ee, 0x7a6a55, 1.0);
const sun = new THREE.DirectionalLight(0xfff3e0, 2.5);
sun.castShadow = true;
function applyShadowQuality() {
  const extent = quality.shadowExtent;
  sun.shadow.mapSize.set(quality.shadowSize, quality.shadowSize);
  Object.assign(sun.shadow.camera, { left: -extent, right: extent, top: extent, bottom: -extent, near: 10, far: quality.shadowFar });
  sun.shadow.camera.updateProjectionMatrix();
  sun.shadow.map?.dispose(); sun.shadow.map = null;
  sun.shadow.needsUpdate = true;
}
applyShadowQuality();
sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.6;
scene.add(hemi, sun, sun.target);
const flood = [];
for (let k = 0; k < 4; k++) {
  const a = (k / 4) * Math.PI * 2 + Math.PI / 4, i = Math.round((a / (Math.PI * 2)) * bowl.dirs.length) % (bowl.dirs.length - 1);
  const [ux, uz] = bowl.dirs[i], r = bowl.rHole[i];
  const s = new THREE.SpotLight(0xfff6dd, 0, 420, 0.75, 0.6, 1.2);
  s.position.set(ux * r, PAD + 42, uz * r); s.target.position.set(0, PAD, 0);
  scene.add(s, s.target); flood.push(s);
}

// ---------------------------------------------------------------- state
const today = new Date();
const state = {
  day: new Date(today.getTime() + 3 * 3600000).toISOString().slice(0, 10),
  minutes: openingMinutes(params.get('time')),
  liveClock: false,
  mode: 'venue',
  build: Date.UTC(2026, 9, 1),
  playing: false,
  speed: 4,
};
$('#date').value = state.day;
const liveClock = document.createElement('button');
liveClock.type = 'button'; liveClock.textContent = 'Live clock'; liveClock.setAttribute('aria-pressed', 'false');
$('#date').after(liveClock);
function stopLiveClock() { state.liveClock = false; liveClock.setAttribute('aria-pressed', 'false'); }
liveClock.onclick = () => {
  state.liveClock = !state.liveClock; lastLiveMinute = ''; stopPlay();
  liveClock.setAttribute('aria-pressed', String(state.liveClock));
};

// ---------------------------------------------------------------- time of day
const zDay = new THREE.Color('#9dbad6'), zDusk = new THREE.Color('#4b5878'), zNight = new THREE.Color('#0c1222');
const hDay = new THREE.Color('#ece3d3'), hDusk = new THREE.Color('#e9a77b'), hNight = new THREE.Color('#202838');
let night = 0;
function applyTime() {
  const sp = sunPosition(eatDate(state.day, state.minutes), LAT, LON);
  const el = sp.elevation, az = (sp.azimuth * Math.PI) / 180, er = (Math.max(el, -10) * Math.PI) / 180;
  const dir = new THREE.Vector3(Math.sin(az) * Math.cos(er), Math.sin(er), -Math.cos(az) * Math.cos(er));
  sun.position.copy(dir).multiplyScalar(1800); sun.target.position.set(0, PAD, 0);
  const dayF = smooth(-6, 12, el), dusk = smooth(-8, 2, el) * (1 - smooth(4, 16, el));
  sun.intensity = 2.8 * smooth(-1, 8, el);
  sun.color.set('#ffae66').lerp(new THREE.Color('#fff4e6'), smooth(2, 28, el));
  hemi.intensity = 0.18 + 0.95 * dayF;
  hemi.color.set('#26324a').lerp(new THREE.Color('#e3e8ee'), dayF);
  const z = zNight.clone().lerp(zDay, dayF).lerp(zDusk, dusk * 0.7);
  const h = hNight.clone().lerp(hDay, dayF).lerp(hDusk, dusk * 0.85);
  paintSky(z, h);
  scene.fog.color.copy(h);
  night = 1 - smooth(-2, 5, el);
  bowl.lightsMat.emissiveIntensity = night * 4;
  bowl.ledMat.emissiveIntensity = night * 3.5;
  bowl.shieldMat.emissiveIntensity = 0.22 + night * 0.25;
  if (bloomPass) bloomPass.strength.value = getGradePreset().bloom.strength + night * 0.55;
  for (const s of flood) s.intensity = night * 9000;
  renderer.toneMappingExposure = 1.0 + night * 0.25;
  return sp;
}

// ---------------------------------------------------------------- construction replay (Sentinel-2)
const TL = M.timeline.map((r) => ({ t: Date.parse(r.date), v: r.date < '2025-06-01' ? 0 : Math.min(1, r.ring_bright_frac / 0.9) }));
function roofAt(t) {
  if (t <= TL[0].t) return TL[0].v;
  for (let i = 1; i < TL.length; i++) if (t <= TL[i].t) { const a = TL[i - 1], b = TL[i]; return a.v + (b.v - a.v) * ((t - a.t) / (b.t - a.t)); }
  return TL.at(-1).v;
}
const pitchEarth = new THREE.Color('#9a6b4a');
function applyBuild() {
  const t = state.mode === 'construction' ? state.build : Date.now();
  const struct = smooth(Date.UTC(2024, 4, 1), Date.UTC(2025, 9, 1), t);
  const roof = state.mode === 'construction' ? roofAt(t) : 1;
  bowl.group.visible = t >= Date.UTC(2024, 2, 1) && !blockout; // ?blender: the blockout replaces it
  bowl.seating.scale.y = Math.max(0.02, struct);
  const fs = Math.max(0.001, smooth(Date.UTC(2025, 5, 1), Date.UTC(2026, 2, 1), t));
  bowl.facade.scale.y = fs; bowl.lattice.scale.y = fs;
  bowl.shields.visible = t > Date.UTC(2026, 0, 15) && layerOn('bowl');
  bowl.seats.visible = t > Date.UTC(2026, 2, 1) && layerOn('bowl');
  site.group.visible = t > Date.UTC(2026, 3, 1) && layerOn('furniture');
  bowl.roof.geometry.setDrawRange(0, Math.floor((bowl.roof.userData.indexCount * roof) / 6) * 6);
  bowl.truss.count = Math.floor(bowl.truss.userData.count * Math.min(1, roof * 1.4 + (struct > 0.95 ? 0.15 : 0)));
  const g = smooth(Date.UTC(2026, 4, 15), Date.UTC(2026, 6, 1), t);
  pitch.material.color.copy(pitchEarth).lerp(new THREE.Color('#ffffff'), g);
  return { struct, roof };
}

// ---------------------------------------------------------------- camera fly-to
let fly = null;
function poseFrom({ target, az, el, d }) {
  const a = (az * Math.PI) / 180, e = (el * Math.PI) / 180;
  const T = new THREE.Vector3(...target);
  return { target: T, pos: new THREE.Vector3(T.x + Math.sin(a) * Math.cos(e) * d, T.y + Math.sin(e) * d, T.z - Math.cos(a) * Math.cos(e) * d) };
}
function flyTo(pose, ms = 2000) {
  fly = { t0: performance.now(), ms, p0: camera.position.clone(), t0v: controls.target.clone(), p1: pose.pos, t1: pose.target };
}
function stepFly(now) {
  if (!fly) return;
  const k = Math.min(1, (now - fly.t0) / fly.ms), e = ease(k);
  camera.position.lerpVectors(fly.p0, fly.p1, e);
  const lift = Math.sin(Math.PI * e) * 0.18 * fly.p0.distanceTo(fly.p1);
  camera.position.y += lift;
  controls.target.lerpVectors(fly.t0v, fly.t1, e);
  if (k >= 1) fly = null;
}

// ---------------------------------------------------------------- highlights
const hl = new THREE.Group(); hl.name = 'highlight'; scene.add(hl);
const hlMat = new THREE.MeshBasicMaterial({ color: 0xf2b33d, transparent: true, opacity: 0.9, side: THREE.DoubleSide, depthWrite: false });
const hlMat2 = new THREE.MeshBasicMaterial({ color: 0xffe2a0, transparent: true, opacity: 0.35, side: THREE.DoubleSide, depthWrite: false });
function setHighlight(rings = []) {
  for (const c of hl.children) c.geometry.dispose();
  hl.clear();
  for (const r of rings) {
    hl.add(new THREE.Mesh(ribbon(r.pts, r.w ?? 1.2, r.y, r.closed ?? true), hlMat));
    hl.add(new THREE.Mesh(ribbon(r.pts, (r.w ?? 1.2) * 3.5, typeof r.y === 'function' ? (x, z) => r.y(x, z) - 0.05 : r.y - 0.05, r.closed ?? true), hlMat2));
  }
}

// ---------------------------------------------------------------- focus targets
const west = Math.round(bowl.dirs.length / 2);
const sportSorted = [...F.sport].sort((a, b) => b.area - a.area);
const pitchesOnly = sportSorted.filter((s) => s.kind === 'pitch');
const trackF = sportSorted.find((s) => s.kind === 'track');
const lamwia = M.labels.find((l) => l.text.startsWith('Ngong Hills ·'));
const roofRingAt = (r, y) => ({ pts: bowl.dirs.map(([ux, uz], i) => [ux * r[i], uz * r[i]]), y });
const P0 = PAD + 0.35;
// Fit distance: the whole bowl (plus a margin) fills the frame at any window shape.
const BOWL_R = Math.max(...bowl.rOut);
function fitD(radius, margin = 1.15) {
  const vf = THREE.MathUtils.degToRad(camera.fov) / 2, hf = Math.atan(Math.tan(vf) * camera.aspect);
  return (radius * margin) / Math.sin(Math.min(vf, hf));
}
const CENTRE = [0, PAD + 22, 0];
// Critic cameras from app/cameras/manifest.json (review viewpoints, not real camera locations).
function camPose(id) { const c = CAMS.cameras.find((k) => k.id === id); return { pos: new THREE.Vector3(...c.position), target: new THREE.Vector3(...c.target) }; }
const fitted = (az, el, k = 1) => () => poseFrom({ target: CENTRE, az, el, d: fitD(BOWL_R) * k });
const FOCUS = [
  { id: 'overview', name: 'Overview', k: 'Whole bowl, centred, Ngong Hills behind', poseFn: fitted(40, 22), label: null, rings: [] },
  { id: 'lead06', name: 'Lead view NE', k: 'Camera L06, framed as landing mockup 06: Ngong Road, looking SW to the Ngong Hills', pose: camPose('L06'), label: null, rings: [] },
  { id: 'lead07', name: 'Lead view SSW', k: 'Camera L07, framed as landing mockup 07: over the forest, looking NNE to Lavington', pose: camPose('L07'), label: null, rings: [] },
  { id: 'top', name: 'Top down', k: 'Plan view of the bowl and roof opening', poseFn: () => poseFrom({ target: [0, PAD, 0.01], az: 0, el: 89.5, d: fitD(BOWL_R, 1.25) }), label: null, rings: [] },
  { id: 'entrance', name: 'Main forecourt', k: 'Shield facade, plaza · positions estimated', pose: { pos: new THREE.Vector3(site.plaza.x + 60, PAD + 22, site.plaza.z - 70), target: new THREE.Vector3(0, PAD + 24, -40) }, label: null, rings: [] },
  { id: 'fountain', name: 'Fountain', k: 'Dry-deck jets · position estimated', pose: { pos: new THREE.Vector3(site.pool.x + 30, PAD + 17, site.pool.z - 44), target: new THREE.Vector3(site.pool.x, PAD + 2, site.pool.z + 6) }, label: [site.pool.x, PAD + 10, site.pool.z], rings: [] },
  { id: 'shield', name: 'Shield facade', k: 'Maasai shield, crossed spears, louvres', pose: { pos: new THREE.Vector3(18, PAD + 28, site.pool.z - 8), target: new THREE.Vector3(0, PAD + 26, -110) }, label: null, rings: [] },
  { id: 'ngong', name: 'Ngong Hills', k: `Lamwia ${lamwia?.elev ?? ''} m · 17 km SW · GLO-30`, pose: { pos: new THREE.Vector3(330, PAD + 120, -330), target: new THREE.Vector3(lamwia.x * 0.3, PAD + 120, lamwia.z * 0.3) }, label: null, rings: [] },
  { id: 'bowl', name: 'Stadium bowl', k: 'Outline: OSM · tiers estimated', pose: poseFrom({ target: [0, PAD + 18, 0], az: 125, el: 30, d: 430 }), label: [0, PAD + 60, 0], rings: [{ pts: F.bowl_outer, y: PAD + 0.6, w: 1.8 }] },
  { id: 'pitch', name: 'Pitch', k: '105 × 68 m in a 115 × 74 m zone (W1b)', pose: poseFrom({ target: [0, PAD, 0], az: 90 + F.pitch_bearing_deg, el: 48, d: 175 }), label: [0, PAD + 6, 0], rings: [{ pts: PF.pitch, y: P0, w: 0.9 }] },
  { id: 'centre', name: 'Centre circle', k: 'Radius 9.15 m', pose: poseFrom({ target: [0, PAD, 0], az: 70, el: 52, d: 62 }), label: [0, PAD + 3, 0], rings: [{ pts: PF.centre, y: P0, w: 0.5 }] },
  { id: 'penN', name: 'Penalty area · north', k: '40.32 × 16.5 m', pose: poseFrom({ target: [PF.penNc[0], PAD, PF.penNc[1]], az: 180 + F.pitch_bearing_deg, el: 38, d: 70 }), label: [PF.penNc[0], PAD + 3, PF.penNc[1]], rings: [{ pts: PF.penN, y: P0, w: 0.5 }] },
  { id: 'penS', name: 'Penalty area · south', k: '40.32 × 16.5 m', pose: poseFrom({ target: [PF.penSc[0], PAD, PF.penSc[1]], az: F.pitch_bearing_deg, el: 38, d: 70 }), label: [PF.penSc[0], PAD + 3, PF.penSc[1]], rings: [{ pts: PF.penS, y: P0, w: 0.5 }] },
  { id: 'seating', name: 'Seating tiers', k: 'Green · red · black (design facts)', pose: { pos: new THREE.Vector3(bowl.dirs[west][0] * bowl.at(west, 0.82), PAD + 42, bowl.dirs[west][1] * bowl.at(west, 0.82)), target: new THREE.Vector3(30, PAD + 6, 0) }, label: null, rings: [{ pts: bowl.dirs.map(([ux, uz], i) => [ux * bowl.rIn[i], uz * bowl.rIn[i]]), y: PAD + 1.4, w: 0.6 }] },
  { id: 'roof', name: 'Roof canopy', k: 'Fixed canopy, open centre · height estimated', pose: poseFrom({ target: [0, PAD + 40, 0], az: 210, el: 58, d: 380 }), label: [0, PAD + 58, 0], rings: [roofRingAt(bowl.rHole, PAD + 46.6), roofRingAt(bowl.rOut.map((r) => r - 15), PAD + bowl.topY + 0.5)] },
  ...pitchesOnly.map((s, i) => {
    const [cx, cz] = centroid(s.ring);
    return { id: `train${i}`, name: `Training pitch ${'AB'[i] ?? i + 1}`, k: `${s.area.toLocaleString()} m² · OSM`, pose: poseFrom({ target: [cx, PAD, cz], az: 35, el: 42, d: 190 }), label: [cx, PAD + 5, cz], rings: [{ pts: s.ring, y: PAD + 0.5, w: 1 }] };
  }),
  ...(trackF ? [(() => { const [cx, cz] = centroid(trackF.ring); return { id: 'track', name: 'Warm-up track', k: `${trackF.area.toLocaleString()} m² · OSM`, pose: poseFrom({ target: [cx, PAD, cz], az: 320, el: 45, d: 160 }), label: [cx, PAD + 5, cz], rings: [{ pts: trackF.ring, y: PAD + 0.5, w: 1 }] }; })()] : []),
  { id: 'site', name: 'Site boundary', k: '33.9 ha · W1b, Dec 2025', pose: poseFrom({ target: [0, PAD, 60], az: 15, el: 55, d: 1250 }), label: null, rings: [{ pts: F.site, y: (x, z) => groundAt(x, z) + 1.3, w: 3 }] },
  { id: 'approach', name: 'Ngong Road approach', k: 'Fly-in view (CAM-01 preview)', pose: poseFrom({ target: [0, PAD + 25, 0], az: 28, el: 7, d: 950 }), label: null, rings: [] },
];
let focusId = 'overview', focusLabelPos = null;
function focus(id, ms) {
  const f = FOCUS.find((x) => x.id === id); if (!f) return;
  focusId = id; focusLabelPos = f.label ? { pos: new THREE.Vector3(...f.label), text: f.name } : null;
  setHighlight(f.rings);
  flyTo(f.poseFn ? f.poseFn() : f.pose, ms);
  document.querySelectorAll('[data-focus]').forEach((b) => b.classList.toggle('on', b.dataset.focus === id));
}
// Views bar: numbered views (keys 1-9), previous/next (arrow keys) and Centre (C or Home).
const chips = ['overview', 'lead06', 'lead07', 'entrance', 'shield', 'seating', 'pitch', 'top', 'ngong'].filter((c) => FOCUS.some((f) => f.id === c));
$('#focusbar').innerHTML = `<button class="nav" id="vprev" title="Previous view (←)">‹</button>`
  + chips.map((c, i) => `<button data-focus="${c}" title="${FOCUS.find((f) => f.id === c).k} (key ${i + 1})"><b>${i + 1}</b> ${FOCUS.find((f) => f.id === c).name}</button>`).join('')
  + `<button class="nav" id="vnext" title="Next view (→)">›</button><button class="nav centre" id="vcentre" title="Centre on the stadium (C)">◎ Centre</button>`;
function stepView(dir) { const i = chips.indexOf(focusId); focus(chips[(i < 0 ? 0 : i + dir + chips.length) % chips.length]); }
// Centre: keep the current viewing direction, re-aim at the stadium and fit it in the frame.
function centreView() {
  const dir = camera.position.clone().sub(controls.target).normalize(); if (dir.y < 0.15) dir.y = 0.15; dir.normalize();
  const T = new THREE.Vector3(...CENTRE); flyTo({ target: T, pos: T.clone().addScaledVector(dir, fitD(BOWL_R)) }, 1200);
}
$('#vprev').onclick = () => { stopTour(); stepView(-1); };
$('#vnext').onclick = () => { stopTour(); stepView(1); };
$('#vcentre').onclick = () => { stopTour(); centreView(); };
addEventListener('keydown', (e) => {
  if (e.target.closest('input, select, textarea')) return;
  const n = +e.key; if (n >= 1 && n <= chips.length) { stopTour(); focus(chips[n - 1]); }
  else if (e.key === 'ArrowRight') { stopTour(); stepView(1); }
  else if (e.key === 'ArrowLeft') { stopTour(); stepView(-1); }
  else if (e.key === 'c' || e.key === 'C' || e.key === 'Home') { stopTour(); centreView(); }
});
// Double-click a point to orbit around it.
renderer.domElement.addEventListener('dblclick', (e) => {
  const r = renderer.domElement.getBoundingClientRect(), rc = new THREE.Raycaster();
  rc.setFromCamera(new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1), camera);
  const hit = rc.intersectObjects(scene.children, true).find((h) => h.object.visible && !h.object.isSprite); if (!hit) return;
  const off = camera.position.clone().sub(controls.target); flyTo({ target: hit.point.clone(), pos: hit.point.clone().add(off.multiplyScalar(0.6)) }, 900);
});
$('#focuslist').innerHTML = FOCUS.map((f) => `<div class="focus-item" data-focus="${f.id}"><div>${f.name}<div class="k">${f.k}</div></div><span class="muted">›</span></div>`).join('');
document.addEventListener('click', (e) => { const b = e.target.closest('[data-focus]'); if (b) { stopTour(); focus(b.dataset.focus); } });
const tourBtn = $('#tour');
const tour = createTour({
  camera, controls, focus,
  views: chips.map((id) => FOCUS.find((f) => f.id === id)),
  onStop: () => { tourBtn.classList.remove('on'); tourBtn.textContent = '▶ Tour'; },
});
function stopTour() { if (tour.running) tour.stop(); }
tourBtn.onclick = () => {
  if (tour.running) return tour.stop();
  tour.start(); tourBtn.classList.add('on'); tourBtn.textContent = '■ Stop tour';
};
enableTouchUX({ stage, controls, onPrev: () => { stopTour(); stepView(-1); }, onNext: () => { stopTour(); stepView(1); }, onCentre: () => { stopTour(); centreView(); } });
controls.addEventListener('start', () => { fly = null; });

// ---------------------------------------------------------------- labels
const labelsEl = $('#labels');
const MAJOR = new Set(['Ngong Road', 'Jamuhuri Road', 'Jamhuri Park Road', 'Southern Bypass', 'Kabiria Road', 'Naivasha Road', 'Mbaazi Avenue', 'Kenyatta Drive']);
const labelItems = M.labels.filter((l) => (l.kind !== 'road' || MAJOR.has(l.text)) && l.text !== 'Ngong Hills').map((l) => {
  const e = document.createElement('div');
  e.className = `lbl ${l.kind}`;
  e.innerHTML = l.kind === 'peak' ? `Ngong Hills<span class="el">Lamwia ${l.elev.toLocaleString()} m</span>` : l.text;
  labelsEl.appendChild(e);
  const y = l.kind === 'road' ? groundAt(l.x, l.z) + 6 : l.y;
  return { e, l, p: new THREE.Vector3(l.x, y, l.z) };
});
const focusLbl = document.createElement('div'); focusLbl.className = 'lbl focus'; labelsEl.appendChild(focusLbl);
const v = new THREE.Vector3();
function placeLabel(e, p, show) {
  if (!show) { e.style.display = 'none'; return; }
  v.copy(p).project(camera);
  if (v.z > 1 || Math.abs(v.x) > 1.05 || Math.abs(v.y) > 1.05) { e.style.display = 'none'; return; }
  e.style.display = '';
  e.style.left = `${((v.x + 1) / 2) * stage.clientWidth}px`;
  e.style.top = `${((1 - v.y) / 2) * stage.clientHeight}px`;
}
function updateLabels() {
  const on = layerOn('labels');
  for (const it of labelItems) {
    const d = camera.position.distanceTo(it.p);
    const show = on && (it.l.kind === 'peak' || it.l.kind === 'far' || (it.l.kind === 'area' && d < 7000) || (it.l.kind === 'road' && d < 2200));
    placeLabel(it.e, it.p, show);
  }
  if (focusLabelPos) focusLbl.textContent = focusLabelPos.text;
  placeLabel(focusLbl, focusLabelPos?.pos ?? v, !!focusLabelPos && !fly);
}

// ---------------------------------------------------------------- layers panel
const LAYERS = [
  { id: 'terrain', name: 'Terrain (3D)', claim: 'Measured · Copernicus GLO-30', sw: 'linear-gradient(135deg,#a89b7c,#6f7d55)', objs: terrains, slider: false },
  { id: 'satellite', name: 'Satellite colour', claim: 'Measured · Sentinel-2, Sep–Oct 2026', sw: 'linear-gradient(135deg,#9c8a68,#5d6e45,#b9ab90)', slider: false },
  { id: 'bowl', name: 'Stadium bowl', claim: 'Measured outline · tiers estimated', sw: 'linear-gradient(135deg,#2e7442 30%,#a3282a 30% 70%,#1f1d1b 70%)', objs: [bowl.seating, bowl.seats, bowl.facade, bowl.lattice, bowl.shields, ...bowl.base], mats: [bowl.facade.material, bowl.lattice.material] },
  { id: 'furniture', name: 'Plaza, fountain, masts', claim: 'Estimated positions · reference frames', sw: 'linear-gradient(135deg,#dcd6cb 50%,#5f7f8c 50%)', objs: [site.group] },
  { id: 'roof', name: 'Roof canopy', claim: 'Estimated height 44–50 m', sw: 'linear-gradient(135deg,#f3f1ec,#d9d5cc)', objs: [bowl.roof, bowl.truss], mats: [bowl.roof.material] },
  { id: 'pitch', name: 'Pitch and markings', claim: 'Laws of the Game · zone W1b', sw: 'repeating-linear-gradient(0deg,#5a9644 0 4px,#4c8539 4px 8px)', objs: [pitch.group] },
  { id: 'sport', name: 'Training pitches and track', claim: 'OpenStreetMap', sw: 'linear-gradient(135deg,#5b8f45 60%,#b65d43 60%)', objs: [sport.group], mats: sport.materials },
  { id: 'buildings', name: 'Buildings', claim: `Footprints Overture · heights: ${BH.open_buildings_2023.toLocaleString()} Open Buildings 2023, ${bEst.toLocaleString()} estimated`, sw: 'linear-gradient(135deg,#d5cdbf,#a59a88)', objs: [buildings], mats: [buildings.material] },
  { id: 'roads', name: 'Roads', claim: 'OpenStreetMap via Overture', sw: 'linear-gradient(135deg,#ddd5c7 40%,#b79e80 40% 55%,#ddd5c7 55%)', objs: [roads], mats: [roads.material] },
  { id: 'trees', name: 'Trees', claim: 'Estimated · Sentinel-2 NDVI', sw: 'radial-gradient(circle,#5c7a45 40%,#3f5a30 70%)', objs: [trees], mats: trees.userData.mats },
  { id: 'site', name: 'Site boundary', claim: 'Measured · W1b, Dec 2025', sw: 'repeating-linear-gradient(90deg,#fff 0 5px,#9a9285 5px 9px)', objs: [siteLine], mats: [siteLine.material] },
  { id: 'labels', name: 'Labels', claim: 'OSM names · GLO-30 heights', sw: 'linear-gradient(135deg,#efe9de,#cfc6b6)', slider: false },
  { id: 'people', name: 'People for scale', claim: 'Visualization · not a crowd model', sw: 'radial-gradient(circle,#a3282a 30%,#2e7442 31% 60%,#e4dccb 61%)', objs: [site.crowd], slider: false },
  { id: 'crowd', name: 'Match-day crowd', claim: 'Visualization · phase 1', sw: 'radial-gradient(circle,#a3282a 30%,#2e7442 31% 60%,#e4dccb 61%)', disabled: true, slider: false },
];
const layerState = Object.fromEntries(LAYERS.map((l) => [l.id, !l.disabled]));
function layerOn(id) { return layerState[id]; }
$('#layers').innerHTML = LAYERS.map((l) => `
  <div class="layer${l.disabled ? ' off' : ''}" data-layer="${l.id}">
    <input type="checkbox" ${l.disabled ? 'disabled' : 'checked'} />
    <div class="sw" style="background:${l.sw}"></div>
    <div class="nm">${l.name}<span class="claim">${l.claim}</span></div>
    ${l.slider === false ? '<span></span>' : '<input type="range" min="0" max="100" value="100" />'}
    <span class="pct">${l.disabled ? '—' : l.slider === false ? '' : '100%'}</span>
  </div>`).join('');
for (const row of document.querySelectorAll('.layer')) {
  const L = LAYERS.find((l) => l.id === row.dataset.layer);
  row.querySelector('input[type=checkbox]').onchange = (e) => {
    layerState[L.id] = e.target.checked; row.classList.toggle('off', !e.target.checked);
    if (L.id === 'satellite') for (const t of terrains) { t.material.map = e.target.checked ? t.material.userData.map ?? t.material.map : null; t.material.color.set(e.target.checked ? '#ffffff' : '#cdbf9f'); t.material.needsUpdate = true; }
    for (const o of L.objs ?? []) o.visible = e.target.checked;
    if (L.id === 'bowl') applyBuild();
  };
  const r = row.querySelector('input[type=range]');
  if (r) r.oninput = (e) => {
    const val = e.target.value / 100; row.querySelector('.pct').textContent = `${e.target.value}%`;
    for (const m of L.mats ?? []) { m.transparent = val < 1; m.opacity = val; m.depthWrite = val > 0.98; m.needsUpdate = true; }
  };
}
for (const t of terrains) t.material.userData.map = t.material.map;
document.querySelectorAll('#sidetabs button').forEach((b) => b.onclick = () => {
  document.querySelectorAll('#sidetabs button, #side .tab').forEach((x) => x.classList.toggle('on', x.dataset.tab === b.dataset.tab));
});
$('#sources').innerHTML = [
  ['Contains modified Copernicus Sentinel data 2023–2026', 'Ground colour, trees, roof timeline'],
  ['Copernicus DEM GLO-30', 'Terrain, Ngong Hills heights'],
  ['© OpenStreetMap contributors (ODbL)', 'Bowl outline, roads, pitches, names'],
  ['Overture Maps Foundation', 'Building footprints and roads'],
  ['Google Open Buildings 2.5D Temporal (CC BY 4.0)', 'Building heights, 2023'],
  ['Microsoft Building Footprints', 'Some footprints'],
  ['W1b measurements, Google Earth Pro (numbers only)', 'Site boundary, pitch zone'],
  ['Open-Meteo (CC BY 4.0)', 'Weather card'],
].map(([a, b]) => `<div class="src"><b>${a}</b><span class="muted">${b}</span></div>`).join('');
$('#ov').innerHTML = [
  ['Venue', 'Raila Odinga Talanta Stadium'],
  ['Location', `${Math.abs(LAT).toFixed(5)}° S, ${LON.toFixed(5)}° E`],
  ['Capacity', '60,000 (press)'],
  ['Bowl outline', '256 × 204 m (OSM)'],
  ['Pitch zone', '115 × 74 m (W1b, Dec 2025)'],
  ['Long axis', `${(180 + F.pitch_bearing_deg).toFixed(1)}° / ${F.pitch_bearing_deg.toFixed(1)}°`],
  ['Site', '33.9 ha (W1b)'],
  ['Roof ring', 'Complete Feb 2026 (Sentinel-2)'],
  ['Twin status', '<span class="dot"></span>v0 · in progress'],
].map(([a, b]) => `<dt>${a}</dt><dd>${b}</dd>`).join('');

// ---------------------------------------------------------------- weather card (Open-Meteo, read-only)
const wxCache = {};
async function weatherFor(day) {
  if (wxCache[day]) return wxCache[day];
  const age = (Date.now() - Date.parse(day)) / DAY;
  const host = age > 80 ? 'https://archive-api.open-meteo.com/v1/archive' : 'https://api.open-meteo.com/v1/forecast';
  const url = `${host}?latitude=${LAT}&longitude=${LON}&hourly=temperature_2m,relative_humidity_2m,precipitation,cloud_cover,wind_speed_10m,wind_direction_10m&timezone=Africa%2FNairobi&start_date=${day}&end_date=${day}`;
  try { wxCache[day] = (await (await fetch(url)).json()).hourly ?? null; } catch { wxCache[day] = null; }
  return wxCache[day];
}
const compassPt = (deg) => ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'][Math.round(deg / 45) % 8];
let wxKey = '';
async function updateWeather(sp) {
  const hour = Math.min(23, Math.floor(state.minutes / 60)), key = `${state.day}:${hour}`;
  const sunTxt = `${sp.elevation.toFixed(0)}°`;
  if (key === wxKey) { $('#wx-sun') && ($('#wx-sun').textContent = sunTxt); return; }
  wxKey = key;
  const h = await weatherFor(state.day);
  const val = (k, f = (x) => x) => (h && h[k] && h[k][hour] != null ? f(h[k][hour]) : '—');
  $('#wx').innerHTML = `
    <div>Temp<b>${val('temperature_2m', (x) => `${x.toFixed(0)} °C`)}</b></div>
    <div>Humidity<b>${val('relative_humidity_2m', (x) => `${x}%`)}</b></div>
    <div>Wind<b>${val('wind_speed_10m', (x) => `${x.toFixed(0)} km/h`)}</b>${val('wind_direction_10m', (x) => `${compassPt(x)} (${x}°)`)}</div>
    <div>Rain<b>${val('precipitation', (x) => `${x} mm`)}</b></div>
    <div>Cloud<b>${val('cloud_cover', (x) => `${x}%`)}</b></div>
    <div>Sun height<b id="wx-sun">${sunTxt}</b></div>
    ${h ? '' : '<div style="grid-column:1/-1" class="muted small">Weather offline · showing sun only</div>'}`;
}

// ---------------------------------------------------------------- timeline + charts
const fmtHM = (m) => `${String(Math.floor(m / 60) % 24).padStart(2, '0')}:${String(Math.floor(m % 60)).padStart(2, '0')}`;
const fmtD = (t) => new Date(t).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' });
const C0 = Date.UTC(2023, 0, 1), C1 = Date.UTC(2026, 11, 31);
let ev = [], domain = [0, 1440];
const CONSTRUCTION_EVENTS = [
  { t: Date.UTC(2023, 0, 8), name: 'Before works: playing fields', ico: 'sq2', src: 'Sentinel-2' },
  { t: Date.UTC(2024, 2, 1), name: 'Groundbreaking', ico: '', src: 'Press' },
  { t: Date.UTC(2024, 3, 22), name: 'Earthworks visible', ico: 'tri', src: 'Sentinel-2' },
  { t: Date.UTC(2025, 10, 15), name: 'Roof ring 30%', ico: 'tri', src: 'Sentinel-2' },
  { t: Date.UTC(2026, 1, 11), name: 'Roof ring complete', ico: '', src: 'Sentinel-2' },
  { t: Date.UTC(2026, 5, 4), name: 'Pitch grass germinates', ico: 'sq2', src: 'Press' },
  { t: Date.UTC(2026, 9, 1), name: '94% complete', ico: 'tri', src: 'Parliament' },
  { t: Date.UTC(2026, 11, 31), name: 'CAF readiness deadline', ico: '', src: 'Press' },
];
function buildTimeline() {
  const tr = $('#track');
  if (state.mode === 'construction') {
    domain = [C0, C1];
    $('#tl-title').textContent = 'Construction replay'; $('#tl-range').textContent = 'Jan 2023 – Dec 2026 · roof from Sentinel-2';
    ev = CONSTRUCTION_EVENTS.map((e) => ({ ...e, v: e.t, time: fmtD(e.t) }));
    $('#track-ticks').innerHTML = [2023, 2024, 2025, 2026].flatMap((y) => [[Date.UTC(y, 0, 1), `Jan ${y}`], [Date.UTC(y, 6, 1), `Jul`]]).map(([t, s]) => `<span style="left:${pct(t)}%">${s}</span>`).join('');
    $('#track-fill').style.cssText = `left:${pct(Date.UTC(2024, 2, 1))}%;width:${pct(Date.UTC(2026, 9, 1)) - pct(Date.UTC(2024, 2, 1))}%`;
  } else {
    domain = [0, 1440];
    const se = sunEvents(state.day, LAT, LON);
    let floodOn = se.sunset - 25; for (let t = se.noon; t < 1440; t++) if (sunPosition(eatDate(state.day, t), LAT, LON).elevation < 4) { floodOn = t; break; }
    $('#tl-title').textContent = 'Time of day'; $('#tl-range').textContent = `${new Date(state.day).toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })} · EAT (UTC+3)`;
    ev = [
      { v: se.sunrise, name: 'Sunrise', ico: 'tri' }, { v: se.goldenEnd, name: 'Golden hour ends', ico: 'sq2' },
      { v: se.noon, name: `Solar noon · ${se.noonEl.toFixed(0)}°`, ico: '' }, { v: se.goldenStart, name: 'Golden hour', ico: 'sq2' },
      { v: se.sunset, name: 'Sunset', ico: 'tri' }, { v: floodOn, name: 'Floodlights on', ico: '' },
    ].filter((e) => e.v != null).map((e) => ({ ...e, time: fmtHM(e.v) }));
    $('#track-ticks').innerHTML = [0, 180, 360, 540, 720, 900, 1080, 1260, 1440].map((m) => `<span style="left:${pct(m)}%">${fmtHM(m === 1440 ? 0 : m)}</span>`).join('');
    $('#track-fill').style.cssText = `left:${pct(se.sunrise)}%;width:${pct(se.sunset) - pct(se.sunrise)}%`;
  }
  $('#track-marks').innerHTML = ev.map((e) => `<span style="left:${pct(e.v)}%" title="${e.name}"></span>`).join('');
  $('#events').innerHTML = ev.map((e, i) => `<div class="ev" data-ev="${i}"><i class="${e.ico}"></i><span>${e.name}${e.src ? ` <span class="muted small">· ${e.src}</span>` : ''}</span><span class="t">${e.time}</span></div>`).join('');
  $('#ev-sub').textContent = state.mode === 'construction' ? 'source shown' : 'sun at pitch centre';
  drawCharts();
}
const pct = (x) => ((x - domain[0]) / (domain[1] - domain[0])) * 100;
const curVal = () => (state.mode === 'construction' ? state.build : state.minutes);
function setVal(x) {
  x = Math.min(domain[1], Math.max(domain[0], x));
  if (state.mode === 'construction') state.build = x; else { stopLiveClock(); state.minutes = x; }
}
function trackFromEvent(e) { const r = $('#track').getBoundingClientRect(); setVal(domain[0] + ((e.clientX - r.left) / r.width) * (domain[1] - domain[0])); }
$('#track').addEventListener('pointerdown', (e) => { stopPlay(); trackFromEvent(e); const mv = (ev2) => trackFromEvent(ev2); addEventListener('pointermove', mv); addEventListener('pointerup', () => removeEventListener('pointermove', mv), { once: true }); });
$('#events').addEventListener('click', (e) => {
  const row = e.target.closest('.ev'); if (!row) return;
  const it = ev[+row.dataset.ev]; setVal(it.v); stopPlay();
  document.querySelectorAll('.ev').forEach((r) => r.classList.toggle('on', r === row));
  if (state.mode === 'construction') focus(it.name.startsWith('Pitch') ? 'pitch' : 'bowl');
  else focus(it.name.startsWith('Floodlights') ? 'bowl' : it.name.startsWith('Sunset') || it.name.startsWith('Golden hour') ? 'ngong' : 'overview');
});
function stopPlay() { state.playing = false; $('#play').textContent = '▶'; $('#play').classList.remove('on'); }
$('#play').onclick = () => { stopLiveClock(); state.playing = !state.playing; $('#play').textContent = state.playing ? '❚❚' : '▶'; $('#play').classList.toggle('on', state.playing); };
$('#step').onclick = () => { const n = ev.find((e) => e.v > curVal() + 1); setVal(n ? n.v : domain[0]); };
$('#speed').onchange = (e) => { state.speed = parseInt(e.target.value, 10); };

let cur1, cur2, cur3, profileZ;
function drawCharts() {
  const xs = [], ys = [];
  for (let m = 0; m <= 1440; m += 10) { xs.push(m); ys.push(sunPosition(eatDate(state.day, m), LAT, LON).elevation); }
  cur1 = lineChart($('#c1'), { xs, ys, xmin: 0, xmax: 1440, ymin: -90, ymax: 90, yticks: [-60, 0, 60], xticks: [[360, '06:00'], [720, '12:00'], [1080, '18:00']], color: '#b3261e' });
  const tx = TL.map((r) => r.t), ty = TL.map((r) => r.v * 100);
  cur2 = lineChart($('#c2'), { xs: tx, ys: ty, xmin: C0, xmax: C1, ymin: 0, ymax: 100, yticks: [0, 50, 100], xticks: [[Date.UTC(2023, 6, 1), '2023'], [Date.UTC(2024, 6, 1), '2024'], [Date.UTC(2025, 6, 1), '2025'], [Date.UTC(2026, 6, 1), '2026']], color: '#1f6b3a' });
  const pz = [], ph = [];
  for (let z = -1400; z <= 1400; z += 10) {
    let h = groundAt(0, z);
    const [rH, rO] = z > 0 ? [bowl.rHole[Math.round(bowl.dirs.length / 4)], bowl.rOut[Math.round(bowl.dirs.length / 4)]] : [bowl.rHole[Math.round((3 * bowl.dirs.length) / 4)], bowl.rOut[Math.round((3 * bowl.dirs.length) / 4)]];
    if (Math.abs(z) > rH && Math.abs(z) < rO + 2.5) h = PAD + 47;
    else if (Math.abs(z) <= rH && Math.abs(z) > 59) h = PAD + Math.min(40, (Math.abs(z) - 59) * 0.55);
    pz.push(z / 1000); ph.push(h + M.ground_elev_m);
  }
  profileZ = { pz, ph };
  const lo = Math.floor(Math.min(...ph) / 20) * 20, hi = Math.ceil(Math.max(...ph) / 20) * 20;
  cur3 = lineChart($('#c3'), { xs: pz, ys: ph, xmin: -1.4, xmax: 1.4, ymin: lo, ymax: hi, yticks: [lo, Math.round((lo + hi) / 2), hi], xticks: [[-1.2, 'N 1.2 km'], [0, 'pitch'], [1.2, 'S 1.2 km']], color: '#6d665b' });
}

// ---------------------------------------------------------------- modes and date
// Night show (SHW-01 to SHW-03): loaded on demand, removed when another mode is chosen.
let shows = null;
async function startShow() {
  if (!shows) {
    const { installShows } = await import('./shows/index.js');
    shows = installShows({ scene, camera, renderer, heroGroup: hero?.group, bowlGroup: bowl.group });
  }
  stopLiveClock(); state.minutes = 1200; const t = document.querySelector('#landing-time'); if (t) t.value = '1200';
  if (!startShow.savedFlood) {
    startShow.savedFlood = flood.map(light => ({ light, descriptor: Object.getOwnPropertyDescriptor(light, 'intensity') }));
    // applyTime writes intensity again after a time change. Hold these lamps dark until stopShow.
    for (const { light } of startShow.savedFlood) Object.defineProperty(light, 'intensity', { configurable: true, enumerable: true, get: () => 0, set: () => {} });
  }
  shows.play('night_show');
  if (import.meta.env.DEV) window.__shows = shows;
}
function stopShow() {
  shows?.dispose(); shows = null;
  if (startShow.savedFlood) {
    for (const { light, descriptor } of startShow.savedFlood) Object.defineProperty(light, 'intensity', descriptor);
    startShow.savedFlood = null;
  }
}
document.querySelectorAll('#modes button').forEach((b) => b.onclick = () => {
  if (b.disabled) return;
  document.querySelectorAll('#modes button').forEach((x) => x.classList.toggle('on', x === b));
  state.mode = b.dataset.mode === 'construction' ? 'construction' : 'venue';
  state.matchday = b.dataset.mode === 'matchday'; if (state.matchday) ensureCrowd();
  stopPlay(); buildTimeline(); applyBuild();
  if (b.dataset.mode === 'construction') { state.build = Date.UTC(2023, 0, 8); focus('bowl'); }
  if (b.dataset.mode === 'weather') { $('#weather').scrollIntoView({ behavior: 'smooth' }); focus('overview'); }
  if (b.dataset.mode === 'show') { focus('overview'); void startShow(); } else stopShow();
});
$('#date').onchange = (e) => { if (e.target.value) { stopLiveClock(); state.day = e.target.value; wxKey = ''; buildTimeline(); } };

// ---------------------------------------------------------------- map controls
const v2d = $('#v2d'), v3d = $('#v3d');
v2d.onclick = () => { v2d.classList.add('on'); v3d.classList.remove('on'); controls.maxPolarAngle = 0.0001; controls.enableRotate = false; const d = camera.position.distanceTo(controls.target); flyTo({ target: controls.target.clone(), pos: controls.target.clone().add(new THREE.Vector3(0, d, 0.01)) }, 1200); };
v3d.onclick = () => { v3d.classList.add('on'); v2d.classList.remove('on'); controls.maxPolarAngle = THREE.MathUtils.degToRad(87); controls.enableRotate = true; focus(focusId, 1200); };
$('#zoom').onchange = (e) => { const z = +e.target.value, d = 2400 / z, dir = camera.position.clone().sub(controls.target).normalize(); flyTo({ target: controls.target.clone(), pos: controls.target.clone().addScaledVector(dir, d) }, 900); };
$('#fs').onclick = () => (document.fullscreenElement ? document.exitFullscreen() : stage.requestFullscreen());

// ---------------------------------------------------------------- hover tooltip
const ray = new THREE.Raycaster(); const ndc = new THREE.Vector2();
const siteRing = F.site;
const inPoly = (x, z, P) => { let c = false; for (let i = 0, j = P.length - 1; i < P.length; j = i++) { const [xi, zi] = P[i], [xj, zj] = P[j]; if ((zi > z) !== (zj > z) && x < ((xj - xi) * (z - zi)) / (zj - zi) + xi) c = !c; } return c; };
const dms = (d, pos, neg) => { const a = Math.abs(d), deg = Math.floor(a), mi = Math.floor((a - deg) * 60), s = ((a - deg) * 60 - mi) * 60; return `${deg}°${String(mi).padStart(2, '0')}′${s.toFixed(1)}″${d < 0 ? neg : pos}`; };
let lastHover = 0;
const pickables = [terrainSite, bowl.seating, bowl.roof, bowl.facade, ...sport.meshes, pitch.group, buildings];
const HSRC = ['height: Open Buildings 2023', 'height estimated: OSM floors × 3.2 m', 'height estimated: default by footprint area'];
renderer.domElement.addEventListener('pointermove', (e) => {
  const now = performance.now(); if (now - lastHover < 70) return; lastHover = now;
  const r = renderer.domElement.getBoundingClientRect();
  ndc.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
  ray.setFromCamera(ndc, camera);
  const hit = ray.intersectObjects(pickables, true).find((h) => h.object.visible);
  const tip = $('#tooltip');
  if (!hit) { tip.hidden = true; return; }
  const p = hit.point, n = hit.face?.normal?.clone().transformDirection(hit.object.matrixWorld);
  let what = 'Ground', extra = '';
  const o = hit.object;
  if (o === bowl.seating) what = 'Seating <span class="dim">· rows estimated</span>';
  else if (o === bowl.roof) what = 'Roof canopy <span class="dim">· height estimated</span>';
  else if (o === bowl.facade) what = 'Facade <span class="dim">· shield screen</span>';
  else if (o.userData.kind === 'pitch') what = `Training pitch <span class="dim">· ${o.userData.area.toLocaleString()} m²</span>`;
  else if (o.userData.kind === 'track') what = 'Warm-up track';
  else if (o.name === 'pitch-surface') what = 'Pitch <span class="dim">· hybrid grass</span>';
  else if (o === buildings) what = `Building <span class="dim">· ${HSRC[o.userData.src[hit.face.a]] ?? 'height source unknown'}</span>`;
  else if (n) { const slope = (Math.acos(Math.min(1, n.y)) * 180) / Math.PI, asp = (Math.atan2(n.x, -n.z) * 180) / Math.PI; extra = ` · ${slope.toFixed(0)}° slope${slope > 1.5 ? ` · ${compassPt((asp + 360) % 360)}-facing` : ''}`; }
  const lat = LAT - p.z / 110574, lon = LON + p.x / (111320 * Math.cos((LAT * Math.PI) / 180));
  const inside = inPoly(p.x, p.z, siteRing);
  tip.innerHTML = `<b>${(p.y + M.ground_elev_m).toFixed(0)} m</b>${extra}<br>${what}<br><span class="dim">● ${inside ? 'Inside the Talanta site' : 'Outside the site'} · ${Math.hypot(p.x, p.z).toFixed(0)} m to centre spot</span><br><span class="dim">${dms(lat, 'N', 'S')} ${dms(lon, 'E', 'W')}</span>`;
  tip.hidden = false;
  tip.style.left = `${Math.min(e.clientX - stage.getBoundingClientRect().left + 14, stage.clientWidth - 230)}px`;
  tip.style.top = `${e.clientY - stage.getBoundingClientRect().top + 14}px`;
});
renderer.domElement.addEventListener('pointerleave', () => { $('#tooltip').hidden = true; });

// ---------------------------------------------------------------- resize, compass, scale bar
function resize() { const w = stage.clientWidth, h = stage.clientHeight; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); drawCharts(); }
new ResizeObserver(resize).observe(stage);
function updateHud() {
  const d = camera.position.clone().sub(controls.target);
  const bearing = (Math.atan2(-d.x, d.z) * 180) / Math.PI;
  $('#compass svg').style.transform = `rotate(${-bearing}deg)`;
  const mpp = (2 * d.length() * Math.tan(((camera.fov / 2) * Math.PI) / 180)) / stage.clientHeight;
  const target = mpp * 130, pow = Math.pow(10, Math.floor(Math.log10(target)));
  const nice = [1, 2, 5, 10].map((k) => k * pow).find((x) => x >= target * 0.7) ?? pow * 10;
  $('#scalebar').style.width = `${nice / mpp}px`;
  const f = (x) => (x >= 1000 ? `${x / 1000} km` : `${x} m`);
  $('#sb-mid').textContent = f(nice / 2); $('#sb-end').textContent = f(nice);
}

// ---------------------------------------------------------------- web hero (?hero)
// Baked Blender export (blender/web_hero, app/public/models + env). Lighting is baked for one moment
// (manifest.time), so hero mode keeps that baked light while the UI clock remains independent.
// It loads in the background: the procedural twin stays usable until the hero is ready, or if it never is.
let hero = null, heroHidden = [], heroFog = null, heroGradeOn = null;
let heroImpostors = null, heroTreesUpdated = -Infinity;
const withTimeout = (p, ms, what) => Promise.race([p, new Promise((_, rej) => setTimeout(() => rej(new Error(`${what} timed out after ${ms / 1000} s`)), ms))]);
async function loadPreferredHero() {
  for (const base of ['./models/', './models/test/']) {
    try {
      const response = await fetch(`${base}manifest.json`);
      if (!response.ok) continue;
      const manifest = await response.json();
      if (!manifest.models || typeof manifest.models !== 'object') continue;
      return await loadHero({ renderer, scene, base });
    } catch (error) { console.warn('hero manifest unavailable:', base, error); }
  }
  return null;
}
if (params.has('hero')) {
  (async () => {
    // A load that times out is cancelled: if it completes later, its result is dropped, never shown.
    let late = false;
    const h = await withTimeout(loadPreferredHero(), 180000, 'hero models').catch((e) => { late = true; console.warn(e); return null; });
    if (!h) return;
    let envLate = false;
    const envP = loadEnvironment({ renderer, scene: new THREE.Scene(), manifest: h.manifest, preferSmall: quality.panoramaSize === '2048' }).then((e) => { if (envLate) { e?.dispose(); return null; } return e; });
    const env = await withTimeout(envP, 120000, 'panorama').catch((e) => { envLate = true; console.warn(e); return null; });
    if (late) return;
    if (env) { scene.background = scene.environment = env.texture; scene.backgroundRotation.copy(env.rotation); scene.environmentRotation.copy(env.rotation); }
    scene.add(h.group);
    const { installTreeImpostors } = await import('./hero/impostors.js');
    heroImpostors = installTreeImpostors(h.group, camera);
    const { loadGroundTiles } = await import('./hero/groundTiles.js');
    void loadGroundTiles({ renderer, manifest: h.manifest, parent: h.group, camera, groundAt, coarseOnly: /Android|iPhone|iPad|Mobile/i.test(navigator.userAgent) || window.innerWidth < 768 });
    limitEnvToSpecular(h.group, env?.texture);
    let hasGround = false; h.group.traverse((o) => { if (o.isMesh && /^ground/.test(o.name)) hasGround = true; });
    heroHidden = [bowl.group, pitch.group, sport.group, site.group, buildings, roads, trees, siteLine, blockout].filter(Boolean);
    if (env) { heroHidden.push(sky, terrainHz, terrainFar); heroFog = horizonFogColor(env.texture); }
    applyHeroHaze(scene, heroFog ?? scene.fog.color);
    if (hasGround) heroHidden.push(terrainSite);
    sun.castShadow = false; renderer.shadowMap.enabled = false;
    // The UI keeps 07:30 or the user's choice; the lightmap retains its baked time.
    hero = h; heroGradeOn?.();
    console.info('hero mode on:', h.manifest.time, env ? 'panorama loaded' : 'no panorama, procedural sky kept');
  })();
}
// Keep procedural lights and geometry hidden when the time or layer controls change.
function heroLock() {
  if (performance.now() - heroTreesUpdated > 100) {
    heroImpostors?.update(); heroTreesUpdated = performance.now();
  }
  const contactShadows = params.get('contactShadows') !== '0' && quality.shadows;
  traffic?.setContactShadows?.(contactShadows);
  crowd?.setContactShadows?.(contactShadows);
  sun.intensity = 0; hemi.intensity = 0; for (const s of flood) s.intensity = 0;
  for (const o of heroHidden) o.visible = false;
  applyHeroHaze(scene, heroFog);
  applyHeroToneMapping(renderer, hero.manifest);
}
initOverlay({ stage, camera, controls });

// ---------------------------------------------------------------- post: ambient occlusion + bloom
let pipeline = null, bloomPass = null;
if (quality.postProcessing && !new URLSearchParams(location.search).has('nopost')) {
  try {
    pipeline = new THREE.RenderPipeline(renderer);
    const scenePass = pass(scene, camera);
    // PassNode inherits renderer.samples (4 with antialias:true). No extra AA pass is needed.
    scenePass.setMRT(mrt({ output, normal: normalView }));
    const color = scenePass.getTextureNode('output');
    const aoPass = ao(scenePass.getTextureNode('depth'), scenePass.getTextureNode('normal'), camera);
    aoPass.resolutionScale = 0.5;
    aoPass.radius.value = 1.2;
    const shaded = vec4(color.rgb.mul(aoPass.getTextureNode().r.mul(0.85).add(0.15)), color.a);
    const look = getGradePreset();
    bloomPass = bloom(shaded, look.bloom.strength + night * 0.55, look.bloom.radius, look.bloom.threshold);
    bloomPass.setResolutionScale(TIERS.high.bloomResolutionScale);
    pipeline.outputNode = heroGrade(shaded).add(bloomPass);
    heroGradeOn = () => { pipeline.outputNode = heroGrade(shaded).add(bloomPass); pipeline.needsUpdate = true; };
  } catch (e) { console.warn('post-processing off:', e); pipeline = null; bloomPass = null; }
}

// ---------------------------------------------------------------- loop
// ---------------------------------------------------------------- life: traffic and match-day crowd (Visualization)
// Traffic includes nganyas (CC-BY-4.0 model, app/public/vehicles/CREDITS.md) and Super Metro-style buses.
let traffic = null;
fetch('./data/traffic_lines.json').then((r) => r.json()).then((lines) => {
  traffic = buildTraffic({ lines, groundAt, camera, count: quality.trafficCount, proxyDistance: tier === 'high' ? 250 : 120 });
  traffic.setLimit?.(quality.trafficCount);
  scene.add(traffic.group);
}).catch((e) => console.warn('traffic off:', e));
// The crowd is heavy (about 56 triangles per fan), so it is built only when Match day is first opened.
let crowd = null;
function ensureCrowd() {
  if (crowd || !bowl.seats || quality.crowdFraction === 0) return;
  crowd = buildCrowd({ seats: bowl.seats, pitch: { centre: [0, 0, 0], bearing: F.pitch_bearing_deg }, fraction: quality.crowdFraction });
  crowd.group.position.y = PAD; scene.add(crowd.group);
}
const fpsMonitor = createFpsMonitor({ tier, onDowngrade(next) {
  tier = next; quality = TIERS[tier];
  renderer.setPixelRatio(Math.min(devicePixelRatio, quality.pixelRatio));
  renderer.shadowMap.enabled = quality.shadows && !hero;
  applyShadowQuality(); bowl.setTier(tier);
  // Apply the rest of the tier to what already exists: post-processing off, fewer trees, cheaper traffic.
  if (!quality.postProcessing) pipeline = null;
  { const keep = quality.treeCount / Math.max(1, trees.children.reduce((n, m) => n + m.count, 0)); if (keep < 1) for (const m of trees.children) if (m.isInstancedMesh) m.count = Math.floor(m.count * keep); }
  traffic?.setLimit(quality.trafficCount);
  if (crowd && quality.crowdFraction < 1) {
    scene.remove(crowd.group);
    crowd.group.traverse((o) => { if (o.isMesh) { o.geometry.dispose(); for (const m of Array.isArray(o.material) ? o.material : [o.material]) m.dispose(); } });
    crowd = null; if (state.matchday) ensureCrowd();
  }
  if (!quality.crowdFraction) site.crowd.visible = false;
} });
if (fpsMonitor.element) stage.appendChild(fpsMonitor.element);

buildTimeline();
applyBuild();
focus('overview', 1);
initLanding({
  views: FOCUS, focus, state, stopTour,
  setTime(minutes) { stopTour(); stopPlay(); stopLiveClock(); state.minutes = minutes; },
  setEvent(mode) { document.querySelector(`#modes button[data-mode="${mode}"]`)?.click(); },
  startTour() { tourBtn.click(); },
});
if (!quality.crowdFraction) site.crowd.visible = false;
let lastT = performance.now(), hud = 0, lastTimeKey = '', lastBuildKey = '', cachedSun;
let lastLiveMinute = '';
/** Return geometry counts before culling for the current scene parts. */
function performanceProfile() {
  return Object.fromEntries(Object.entries({ seats: bowl.seats, bowl: bowl.group, context: trees, buildings, roads, site: site.group, traffic: traffic?.group, crowd: crowd?.group }).map(([name, root]) => [name, profileGeometry(root)]));
}
renderer.setAnimationLoop((now) => {
  const dt = Math.min(0.1, (now - lastT) / 1000); lastT = now;
  if (state.liveClock) {
    const eatNow = new Date(Date.now() + 3 * 3600000), key = eatNow.toISOString().slice(0, 16);
    if (key !== lastLiveMinute) {
      const day = key.slice(0, 10), changed = day !== state.day;
      state.day = day; state.minutes = eatNow.getUTCHours() * 60 + eatNow.getUTCMinutes();
      $('#date').value = day; if (changed) { wxKey = ''; buildTimeline(); }
      lastLiveMinute = key;
    }
  }
  if (state.playing) {
    if (state.mode === 'construction') { state.build += state.speed * DAY * dt * 8; if (state.build > C1) state.build = C0; }
    else { state.minutes += state.speed * dt * 15; if (state.minutes > 1440) state.minutes = 0; }
  }
  stepFly(now);
  if (!hero && site.group.visible) site.update(now / 1000, night);
  traffic?.update(dt);
  shows?.update(dt);
  site.crowd.visible = quality.crowdFraction > 0 && layerOn('people');
  if (crowd) { crowd.group.visible = !hero && state.matchday && bowl.group.visible && bowl.seats.visible; if (crowd.group.visible) crowd.update(now / 1000, night); }
  fpsMonitor.update(now);
  controls.update();
  const timeKey = `${state.day}:${state.minutes}:${Boolean(hero)}`;
  if (timeKey !== lastTimeKey) { cachedSun = applyTime(); lastTimeKey = timeKey; }
  const buildKey = `${state.mode}:${state.build}:${Boolean(blockout)}:${JSON.stringify(layerState)}`;
  if (buildKey !== lastBuildKey) { applyBuild(); lastBuildKey = buildKey; }
  const sp = cachedSun;
  if (hero) heroLock();
  const cv = curVal();
  $('#thumb').style.left = `${pct(cv)}%`;
  $('#thumb-label').textContent = state.mode === 'construction' ? fmtD(cv) : fmtHM(cv);
  cur1?.(state.minutes, sp.elevation);
  const tb = state.mode === 'construction' ? state.build : Math.min(Date.now(), C1);
  cur2?.(tb, (state.mode === 'construction' ? roofAt(tb) : 1) * 100);
  if (profileZ) { const z = Math.max(-1.4, Math.min(1.4, controls.target.z / 1000)); const i = Math.round((z + 1.4) * 100); cur3?.(z, profileZ.ph[Math.min(profileZ.ph.length - 1, Math.max(0, i))]); }
  hlMat.opacity = 0.65 + 0.3 * Math.sin(now / 300);
  updateLabels();
  if (++hud % 6 === 0) { updateHud(); updateWeather(sp); }
  if (pipeline) {
    try { pipeline.render(); } catch (e) { console.warn('post-processing failed, plain render from now on:', e); pipeline = null; bloomPass = null; renderer.render(scene, camera); }
  } else renderer.render(scene, camera);
});
setTimeout(() => $('#splash').classList.add('done'), 250);
$('#claim').innerHTML = `<b>Raila Odinga Talanta Stadium</b> · 60,000 design capacity · ${Math.round(Math.max(...bowl.rOut) * 2)} m long · ${Math.round(bowl.topY)} m high (est.)`;
window.__twin = { performanceProfile, scene, camera, controls, focus, state, FOCUS, get blockout() { return blockout; } };
