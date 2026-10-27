import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import * as THREE from 'three/webgpu';
import { TIERS, detectTier, createFpsMonitor } from '../src/perf.js';
import { limitEnvToSpecular } from '../src/hero/environment.js';

// Software tests. These do not compile shaders or measure GPU performance.
test('ultra is explicit and automatic detection never selects it', () => {
  assert.ok(TIERS.ultra);
  const descriptors = Object.fromEntries(['location', 'navigator', 'screen', 'window'].map(k => [k, Object.getOwnPropertyDescriptor(globalThis, k)]));
  try {
    Object.defineProperties(globalThis, {
      location: { value: { search: '' }, configurable: true },
      navigator: { value: { hardwareConcurrency: 32, deviceMemory: 32, maxTouchPoints: 0 }, configurable: true },
      screen: { value: { width: 3840, height: 2160 }, configurable: true },
      window: { value: {}, configurable: true },
    });
    for (const backend of [{ isWebGPUBackend: true }, { isWebGLBackend: true }, {}]) assert.notEqual(detectTier({ backend }), 'ultra');
    location.search = '?tier=ultra'; assert.equal(detectTier({}), 'ultra');
    location.search = '?lite&tier=ultra'; assert.equal(detectTier({}), 'low');
  } finally {
    for (const [key, descriptor] of Object.entries(descriptors)) {
      if (descriptor) Object.defineProperty(globalThis, key, descriptor); else delete globalThis[key];
    }
  }
});

test('converted baked materials carry the mask flag and retain their lighting', () => {
  const root = new THREE.Group(), texture = new THREE.Texture();
  const baked = new THREE.MeshStandardMaterial({ lightMap: texture, lightMapIntensity: 1.4 });
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(), baked);
  mesh.userData.heroLightmapped = true;
  const unbaked = new THREE.Mesh(new THREE.BoxGeometry(), new THREE.MeshStandardMaterial());
  root.add(mesh, unbaked);
  limitEnvToSpecular(root, new THREE.Texture());
  assert.equal(mesh.material.userData.ultraBaked, true);
  assert.equal(mesh.material.lightMap, texture);
  assert.equal(mesh.material.lightMapIntensity, 1.4);
  assert.notEqual(unbaked.material.userData.ultraBaked, true);
  const converted = mesh.material;
  limitEnvToSpecular(root, new THREE.Texture());
  assert.equal(mesh.material, converted);
});

test('ultra URL uses an allowlist, supports none, all, and explicit exclusions', async () => {
  const { parseUltraSettings, DEFAULT_SETTINGS } = await import('../src/hero/ultra.js');
  assert.deepEqual(parseUltraSettings(''), { ...DEFAULT_SETTINGS });
  assert.ok(Object.values(parseUltraSettings('?ultra=none')).every(v => v === false));
  const selected = parseUltraSettings('?tier=ultra&ultra=ssgi,traa,ssr');
  assert.equal(selected.ssgi, true); assert.equal(selected.traa, true); assert.equal(selected.ssr, true);
  assert.equal(selected.fog, false); assert.equal(selected.bloom, false);
  assert.equal(parseUltraSettings('?ultra=all,-ssr').ssr, false);
  assert.ok(Object.values(parseUltraSettings('?ultra=unknown')).every(v => v === false));
});

test('all effects off returns to the unchanged high chain before allocating resources', async () => {
  const { createUltraPipeline, parseUltraSettings } = await import('../src/hero/ultra.js');
  // No renderer or scene: accessing either would fail rather than return the high-path sentinel.
  assert.equal(createUltraPipeline({ settings: parseUltraSettings('?ultra=none') }), null);
  const main = readFileSync(new URL('../src/main.js', import.meta.url), 'utf8');
  assert.match(main, /import\('\.\/hero\/ultra\.js'\)/);
  assert.doesNotMatch(main, /import .* from ['"]\.\/hero\/ultra\.js/);
});

// Evaluate only the scalar arithmetic emitted by maskIndirect, without a GPU.
function scalar(node) {
  if (node.isVarNode) return scalar(node.node);
  if (node.isConstNode) return node.value;
  if (node.isMathNode && node.method === 'oneMinus') return 1 - scalar(node.aNode);
  if (node.isOperatorNode && node.op === '*') return scalar(node.aNode) * scalar(node.bNode);
  throw new Error(`Unexpected scalar node ${node.constructor.name}`);
}

test('the actual MRT mask emits one for baked materials and suppresses their entire GI term', async () => {
  const { float } = await import('three/tsl');
  const { bakedMaskNode, maskIndirect } = await import('../src/hero/ultra.js');
  for (const [material, want] of [[{ userData: { ultraBaked: true } }, 1], [{ lightMap: new THREE.Texture() }, 1], [{ userData: {} }, 0]]) {
    const mask = bakedMaskNode.shaderNode.jsFunc({ material });
    assert.equal(scalar(mask), want);
    assert.equal(scalar(maskIndirect(float(7), mask)), want === 1 ? 0 : 7);
  }
});

function graphContext(webgpu = true) {
  const renderer = { backend: { isWebGPUBackend: webgpu }, shadowMap: { enabled: false }, logarithmicDepthBuffer: true,
    toneMapping: THREE.ACESFilmicToneMapping, outputColorSpace: THREE.SRGBColorSpace };
  return { renderer, scene: new THREE.Scene(), camera: new THREE.PerspectiveCamera(45, 1, 0.1, 10000),
    sun: new THREE.DirectionalLight(), look: { bloom: { strength: .065, radius: .3, threshold: .95 } } };
}

test('real ultra graph selects one AO source and disables scene MSAA for TRAA', async () => {
  const { uniform } = await import('three/tsl');
  const { createUltraPipeline, parseUltraSettings } = await import('../src/hero/ultra.js');
  for (const flags of ['ssgi,denoise,ao,traa', 'ao', 'ssr', 'fog,bloom,flare,grain,lut,sss']) {
    const controller = createUltraPipeline({ ...graphContext(), settings: parseUltraSettings('?ultra=' + flags), warmth: uniform(0), exposure: uniform(1) });
    assert.equal(Boolean(controller.effects.ssgi && controller.effects.ao), false);
    if (flags.includes('ssgi')) {
      assert.ok(controller.effects.ssgi);
      assert.equal(controller.scenePass.options.samples, 0);
      assert.ok(controller.effects.traa);
      assert.ok(controller.scenePass.getMRT().has('properties'));
      assert.ok(controller.scenePass.getMRT().has('diffuse'));
    }
    if (flags === 'ao') assert.ok(controller.effects.ao);
    controller.dispose(); controller.dispose();
  }
});

test('unsupported WebGL-only selection returns the unchanged high path without resources', async () => {
  const { createUltraPipeline, parseUltraSettings } = await import('../src/hero/ultra.js');
  const warn = console.warn; console.warn = () => {};
  try {
    assert.equal(createUltraPipeline({ ...graphContext(false), settings: parseUltraSettings('?ultra=ssgi,traa,ssr') }), null);
  } finally { console.warn = warn; }
});

test('IES profile parses and installs at most eight shadowless lights from the show data', async () => {
  const { IESLoader } = await import('three/addons/loaders/IESLoader.js');
  const { createFloodlights } = await import('../src/hero/ultra.js');
  const { fallbackFacadeLines, padY } = await import('../src/shows/geometry.js');
  const ies = new IESLoader().parse(readFileSync(new URL('../public/ultra/007cfb11e343e2f42e3b476be4ab684e.ies', import.meta.url), 'utf8'));
  assert.ok(ies.image.data.length > 0);
  const geometry = fallbackFacadeLines(), scene = new THREE.Scene();
  const rig = createFloodlights(scene, geometry, ies);
  assert.equal(rig.lights.length, 8); assert.equal(rig.root.position.y, padY);
  assert.deepEqual(rig.lights[0].position.toArray(), geometry.floodlights[0].pos);
  assert.deepEqual(rig.lights[1].position.toArray(), geometry.floodlights[3].pos);
  for (const light of rig.lights) { assert.equal(light.castShadow, false); assert.equal(light.iesMap, ies); assert.ok(light.isSpotLight); }
  rig.update(630); assert.ok(rig.lights.every(l => l.intensity === 0));
  rig.update(1200); assert.ok(rig.lights.every(l => l.intensity === 180000));
  rig.dispose(); assert.equal(scene.children.length, 0); ies.dispose();
});

test('ultra can downgrade to high even when the URL explicitly selects ultra', () => {
  const descriptors = Object.fromEntries(['location', 'document'].map(k => [k, Object.getOwnPropertyDescriptor(globalThis, k)]));
  try {
    Object.defineProperties(globalThis, {
      location: { value: { search: '?tier=ultra' }, configurable: true },
      document: { value: { createElement: () => ({ style: {} }), body: { appendChild() {} } }, configurable: true },
    });
    const tiers = [], monitor = createFpsMonitor({ tier: 'ultra', onDowngrade: tier => tiers.push(tier) });
    for (let t = 0; t <= 4050; t += 50) monitor.update(t);
    assert.deepEqual(tiers, ['high']);
    location.search = '?tier=high';
    const pinned = createFpsMonitor({ tier: 'high', onDowngrade: tier => tiers.push(tier) });
    for (let t = 0; t <= 4050; t += 50) pinned.update(t);
    assert.deepEqual(tiers, ['high']);
  } finally {
    for (const [key, descriptor] of Object.entries(descriptors)) {
      if (descriptor) Object.defineProperty(globalThis, key, descriptor); else delete globalThis[key];
    }
  }
});

test('render failure restores renderer state and renders the scene instead of throwing', async () => {
  const { uniform } = await import('three/tsl');
  const { createUltraPipeline, parseUltraSettings } = await import('../src/hero/ultra.js');
  const context = graphContext(), renderer = context.renderer;
  const target = new THREE.RenderTarget(), savedFog = {}, savedMRT = {};
  let currentTarget = target, currentMRT = savedMRT, plain = 0, failures = 0;
  Object.assign(renderer, {
    xr: { enabled: true }, autoClear: false, toneMappingExposure: 1.2,
    info: { render: { calls: 0 } },
    getRenderTarget: () => currentTarget, setRenderTarget: v => { currentTarget = v; },
    getActiveCubeFace: () => 0, getActiveMipmapLevel: () => 0,
    getRenderObjectFunction: () => null, setRenderObjectFunction() {},
    getPixelRatio: () => 1, setPixelRatio() {},
    getMRT: () => currentMRT, setMRT: v => { currentMRT = v; },
    getClearColor: out => out.set(0x123456), getClearAlpha: () => .5, setClearColor() {},
    getScissorTest: () => false, setScissorTest() {},
    render(object) {
      if (object.isQuadMesh) { renderer.setMRT(null); renderer.setRenderTarget(null); throw new Error('Injected effect failure'); }
      assert.equal(object, context.scene); plain++;
    },
  });
  context.scene.fogNode = savedFog;
  const warn = console.warn; console.warn = () => {};
  try {
    const controller = createUltraPipeline({ ...context, settings: parseUltraSettings('?ultra=fog'), warmth: uniform(0), exposure: uniform(1), onFailure: () => failures++ });
    controller.render(); controller.render();
    assert.equal(plain, 1); assert.equal(failures, 1);
    assert.equal(renderer.xr.enabled, true);
    assert.equal(renderer.toneMapping, THREE.ACESFilmicToneMapping);
    assert.equal(renderer.outputColorSpace, THREE.SRGBColorSpace);
    assert.equal(currentTarget, target); assert.equal(currentMRT, savedMRT);
    assert.equal(context.scene.fogNode, savedFog);
  } finally { console.warn = warn; target.dispose(); }
});

test('ultra suppresses other spotlights during its frame and restores them afterward', async () => {
  const { limitSpotlights } = await import('../src/hero/ultra.js');
  const scene = new THREE.Scene(), root = new THREE.Group(); scene.add(root);
  for (let i = 0; i < 8; i++) root.add(new THREE.SpotLight(0xffffff, 10));
  for (let i = 0; i < 12; i++) scene.add(new THREE.SpotLight(0xffffff, 20));
  const restore = limitSpotlights(scene, root);
  let active = 0; scene.traverse(o => { if (o.isSpotLight && o.intensity > 0) active++; });
  assert.equal(active, 8);
  restore();
  assert.ok(scene.children.filter(o => o.isSpotLight).every(o => o.intensity === 20));
});

test('LUT preserves neutral endpoints and has monotonic equal channels', async () => {
  const { createCameraLut } = await import('../src/hero/ultra.js');
  const lut = createCameraLut(), data = lut.image.data;
  assert.deepEqual([...data.slice(0, 4)], [0, 0, 0, 255]);
  assert.deepEqual([...data.slice(-4)], [255, 255, 255, 255]);
  let previous = -1;
  for (let n = 0; n < 16; n++) {
    const offset = (n + 16 * n + 256 * n) * 4;
    assert.equal(data[offset], data[offset + 1]); assert.equal(data[offset], data[offset + 2]);
    assert.ok(data[offset] > previous); previous = data[offset];
  }
  lut.dispose();
});
