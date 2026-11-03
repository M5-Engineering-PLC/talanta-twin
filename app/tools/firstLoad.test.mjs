// Software tests with mocked network and renderer. No physical measurement or GPU output.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';
import * as THREE from 'three/webgpu';
import { KTX2Loader } from 'three/addons/loaders/KTX2Loader.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { createTimeOfDay, PRESETS } from '../src/hero/timeOfDay.js';
import { loadHero } from '../src/hero/loadHero.js';
import { loadGroundTiles } from '../src/hero/groundTiles.js';
import { choosePanorama } from '../src/hero/environment.js';
import { firstLoadBytes } from './first_load_bytes.mjs';

const source = await readFile(new URL('../src/main.js', import.meta.url), 'utf8');
const prepareBody = source.split('async prepare(current) {')[1].split('\n      },\n      frame(q)')[0];
const stepBody = source.split('function heroTodStep(dusk) {')[1].split('\n}\n// Keep procedural')[0];
const flush = () => new Promise(resolve => setImmediate(resolve));
const deferred = () => { let resolve; const promise = new Promise(r => { resolve = r; }); return { promise, resolve }; };
const release = name => new URL(`../../assets/web_hero_v3/${name}`, import.meta.url);

function idleHost() {
  const frames = [], idle = [], timers = [];
  return { frames, idle, timers, requestAnimationFrame: cb => frames.push(cb), requestIdleCallback: cb => idle.push(cb),
    setTimeout: (cb, delay) => { assert.equal(typeof delay, 'number'); timers.push(cb); } };
}
function timeHarness({ phone = false, holdNight = null } = {}) {
  const calls = [], base = new THREE.Texture(), material = new THREE.MeshStandardMaterial();
  let disposed = 0; base.addEventListener('dispose', () => disposed++);
  material.userData = { talanta_bake_group: 'shell', talanta_lightmap: { intensity: 1 } }; material.lightMap = base;
  const group = new THREE.Group(); group.add(new THREE.Mesh(new THREE.BoxGeometry(), material));
  const api = createTimeOfDay({ group, scene: new THREE.Scene(), renderer: {}, phone,
    manifest: { tod: { base: '0730', times: Object.keys(PRESETS), dir: 'lightmaps' } },
    io: {
      async json(url) { calls.push(url); const time = url.match(/(\d{4})\/tod/)[1]; return { time, preset: PRESETS[time],
        ground_tile_gain: 1, groups: { shell: { file: 'shell.ktx2', intensity: 1 } }, panorama: null }; },
      async textures(urls) { calls.push(...urls); if (holdNight && urls.some(u => u.includes('/2000/'))) await holdNight.promise; return urls.map(() => new THREE.Texture()); },
      async environment() { return null; },
    } });
  return { api, calls, material, base, disposed: () => disposed };
}

test('prepare awaits only the start light set and schedules deferred work after preparation', async () => {
  const calls = [], start = deferred(), crowdReady = deferred(), groundReady = deferred();
  const hero = { groundReady: groundReady.promise, tod: {
    setTime(time) { calls.push(time); return start.promise; }, preload() { assert.fail('prepare must not preload a later set'); },
    preloadWhenIdle(time) { calls.push(`idle:${time}`); },
  } };
  const noop = () => {};
  const prepare = vm.runInNewContext(`(async function(current) {${prepareBody}\n})`, {
    stopTour: noop, stopPlay: noop, stopLiveClock: noop, modeVersion: 0, stopEvent: noop, stopShow: noop,
    state: {}, applyBuild: noop, $: () => ({}), startHero: async () => {}, ensureCrowd: async () => {},
    performance, heroLoading: false, hero, crowd: { ready: crowdReady.promise },
  });
  let ready = false; const work = prepare(() => true).then(() => { ready = true; });
  await flush(); assert.deepEqual(calls, ['1805']); assert.equal(ready, false);
  start.resolve(); crowdReady.resolve(); await flush(); assert.equal(ready, false);
  groundReady.resolve(); await work; assert.deepEqual(calls, ['1805', 'idle:1805']);
});

test('night is requested only after a painted frame and idle, then other sets use later idle callbacks', async () => {
  const h = timeHarness(), host = idleHost(); await h.api.setTime('1805');
  h.calls.length = 0; h.api.preloadWhenIdle('1805', undefined, host); h.api.preloadWhenIdle('1805', undefined, host);
  assert.equal(host.frames.length, 1); assert.deepEqual(h.calls, []);
  host.frames.shift()(); assert.equal(host.idle.length, 0); assert.deepEqual(h.calls, []);
  // The browser can paint the first frame between these animation callbacks.
  host.frames.shift()(); assert.equal(host.idle.length, 1); assert.deepEqual(h.calls, []);
  await host.idle.shift()(); assert.match(h.calls[0], /\/2000\/tod.json$/);
  assert.equal(h.calls.some(u => u.includes('/1030/')), false);
  while (host.idle.length) await host.idle.shift()();
  assert.ok(h.calls.some(u => u.includes('/0730/tod.json'))); assert.ok(h.calls.some(u => u.includes('/1030/')));
  h.api.dispose();
});

test('idle fallback uses a numeric timer and disposal cancels queued downloads', async () => {
  const h = timeHarness(), host = idleHost(); delete host.requestIdleCallback;
  await h.api.setTime('1805'); h.calls.length = 0; h.api.preloadWhenIdle('1805', undefined, host);
  host.frames.shift()(); host.frames.shift()(); assert.equal(host.timers.length, 1);
  h.api.dispose(); await host.timers.shift()(); assert.deepEqual(h.calls, []);
});

test('a sequence seek before night is ready returns with sunset visible and swaps after loading', async () => {
  const night = deferred(), h = timeHarness({ holdNight: night }); await h.api.setTime('1805');
  const host = idleHost();
  const sunset = h.material.lightMap, hero = { tod: h.api }, sequence = { active: true, frame: { lightSet: '2000' } };
  const context = {
    hero, heroSequence: sequence, heroTodTime: '1805', heroLookKey: '', heroLighting: null,
    heroWarmth: {}, getGradePreset: () => ({ warmth: 0 }),
  };
  const step = vm.runInNewContext(`(function(dusk) {${stepBody}\n})`, context);
  h.api.preloadWhenIdle('1805', () => { context.heroLookKey = ''; }, host);
  step({}); await hero.environmentReady;
  assert.equal(h.api.current, '1805'); assert.equal(h.material.lightMap, sunset);
  assert.equal(h.calls.some(u => u.includes('/2000/')), false, 'an early seek cannot start night before idle');
  host.frames.shift()(); host.frames.shift()(); const loading = host.idle.shift()();
  await flush(); step({}); assert.equal(h.api.current, '1805'); assert.equal(h.material.lightMap, sunset);
  context.heroLookKey = 'held-seek'; night.resolve(); await loading; assert.equal(context.heroLookKey, '');
  step({}); await flush(); assert.equal(h.api.current, '2000'); assert.notEqual(h.material.lightMap, sunset);
  h.api.dispose();
});

test('phone prioritizes night while retaining two cached sets and uses only phone lightmaps', async () => {
  const h = timeHarness({ phone: true }), host = idleHost(); await h.api.setTime('1805');
  h.api.preloadWhenIdle('1805', undefined, host); host.frames.shift()(); host.frames.shift()();
  await host.idle.shift()(); assert.equal(h.disposed(), 1, 'unused embedded base maps release the phone cache slot');
  assert.equal(h.api.current, '1805');
  while (host.idle.length) await host.idle.shift()();
  assert.equal(h.calls.some(u => /\/(0730|1030)\//.test(u)), false, 'full cache blocks extra idle sets');
  assert.ok(h.calls.every(u => u.startsWith('./lightmaps_phone/')));
  const count = h.calls.length; await h.api.setTime('2000'); assert.equal(h.calls.length, count, 'night maps are already cached');
  await h.api.setTime('0730'); assert.ok(h.calls.some(u => u.includes('/0730/')), 'the released base set loads again on demand');
  assert.equal(h.material.lightMap.wrapS, h.base.wrapS); assert.equal(h.material.lightMap.anisotropy, h.base.anisotropy);
  h.api.dispose();
});

test('phone manifest, models, ground and time sets never request desktop files', async () => {
  const calls = [], originalFetch = globalThis.fetch, detect = KTX2Loader.prototype.detectSupport;
  const loadTexture = KTX2Loader.prototype.loadAsync, loadModel = GLTFLoader.prototype.loadAsync;
  KTX2Loader.prototype.detectSupport = function () { return this; };
  KTX2Loader.prototype.loadAsync = async url => { calls.push(url); return new THREE.Texture(); };
  GLTFLoader.prototype.loadAsync = async url => { calls.push(url); return { scene: new THREE.Group() }; };
  globalThis.fetch = async url => {
    calls.push(url);
    const file = url === './models/manifest_phone.json' ? 'manifest_phone.json' : url.replace(/^\.\//, '');
    return new Response(await readFile(release(file)), { headers: { 'content-type': 'application/json' } });
  };
  try {
    const hero = await loadHero({ renderer: {}, phone: true }); assert.ok(hero); assert.equal(hero.phone, true);
    await loadGroundTiles({ renderer: {}, manifest: hero.manifest, parent: hero.group, camera: { position: { x: 0, z: 0 } }, groundAt: () => 0, coarseOnly: true });
    const tod = createTimeOfDay({ group: hero.group, scene: new THREE.Scene(), renderer: {}, manifest: hero.manifest, phone: true,
      io: { json: async url => { calls.push(url); return JSON.parse(await readFile(release(url.replace(/^\.\//, '')), 'utf8')); },
        textures: async urls => Promise.all(urls.map(url => KTX2Loader.prototype.loadAsync(url))),
        environment: async ({ manifest }) => { calls.push(...choosePanorama(manifest, { phone: true }).map(p => './' + p)); return null; } } });
    await tod.setTime('1805'); await tod.preload('2000', { priority: true }); await tod.setTime('2000');
    assert.equal(calls[0], './models/manifest_phone.json');
    assert.equal(calls.filter(u => u.endsWith('.glb')).length, 2);
    assert.ok(calls.filter(u => u.endsWith('.glb')).every(u => u.startsWith('./models/models_phone/')));
    assert.equal(calls.filter(u => u.includes('/ground/L1_')).length, 36);
    assert.ok(calls.some(u => u.includes('/lightmaps_phone/2000/')));
    assert.ok(calls.every(u => !u.includes('/models/models/') && !u.includes('/lightmaps/') && !u.includes('/ground/L0_') && !u.endsWith('/manifest.json')));
    tod.dispose();
  } finally { globalThis.fetch = originalFetch; KTX2Loader.prototype.detectSupport = detect; KTX2Loader.prototype.loadAsync = loadTexture; GLTFLoader.prototype.loadAsync = loadModel; }
});

test('a missing or broken phone manifest keeps the procedural fallback without desktop requests', async () => {
  const fetch = globalThis.fetch, detect = KTX2Loader.prototype.detectSupport, warn = console.warn;
  KTX2Loader.prototype.detectSupport = function () { return this; }; console.warn = () => {};
  try {
    for (const response of [() => new Response('', { status: 404 }), () => new Response('<html>Vite</html>'), () => { throw new Error('network'); }]) {
      const calls = []; globalThis.fetch = async url => { calls.push(url); return response(); };
      assert.equal(await loadHero({ renderer: {}, phone: true }), null); assert.deepEqual(calls, ['./models/manifest_phone.json']);
    }
  } finally { globalThis.fetch = fetch; KTX2Loader.prototype.detectSupport = detect; console.warn = warn; }
});

test('byte estimates defer exactly the night set and exclude embedded base maps', async () => {
  for (const phone of [false, true]) {
    const manifest = JSON.parse(await readFile(release(phone ? 'manifest_phone.json' : 'manifest.json'), 'utf8'));
    const bytes = firstLoadBytes(manifest, { phone });
    const night = manifest.tod_files.filter(f => f.file.startsWith(`${manifest.tod.dir}/2000/`)).reduce((n, f) => n + f.bytes, 0);
    assert.equal(bytes.before - bytes.after, night); assert.ok(bytes.after > bytes.models);
    assert.equal(bytes.models, Object.values(manifest.models).reduce((n, m) => n + m.bytes, 0));
  }
});
