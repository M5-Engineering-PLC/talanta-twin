// ENV-01: nearest time with hysteresis, tod.json parsing, the material swap on mock materials, the panorama per time.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three/webgpu';
import { nearestTime, parseTod, collectLightmapped, applyLightmaps, applyGroundGain, createTimeOfDay, PRESETS } from '../src/hero/timeOfDay.js';

const TIMES = ['0730', '1030', '1805', '2000'];
const hm = (h, m = 0) => h * 60 + m;

test('nearest time on the 24 h circle', () => {
  assert.equal(nearestTime(TIMES, hm(7, 30)), '0730');
  assert.equal(nearestTime(TIMES, hm(9, 10)), '1030');
  assert.equal(nearestTime(TIMES, hm(14, 0)), '1030');
  assert.equal(nearestTime(TIMES, hm(15, 0)), '1805');
  assert.equal(nearestTime(TIMES, hm(23, 59)), '2000');
  assert.equal(nearestTime(TIMES, hm(1, 0)), '2000');   // 5 h from 20:00, 6.5 h from 07:30
  assert.equal(nearestTime(TIMES, hm(3, 0)), '0730');
});

test('hysteresis: no change near a boundary, change once the margin is passed', () => {
  // boundary 0730/1030 is 09:00; margin 25 min
  assert.equal(nearestTime(TIMES, hm(9, 10), '0730'), '0730');
  assert.equal(nearestTime(TIMES, hm(9, 20), '0730'), '1030');
  assert.equal(nearestTime(TIMES, hm(9, 40), '0730'), '1030');
  assert.equal(nearestTime(TIMES, hm(8, 50), '1030'), '1030');
  assert.equal(nearestTime(TIMES, hm(8, 20), '1030'), '0730');
  // a wobble of +-5 min around the boundary never flips
  let cur = '0730', flips = 0;
  for (let i = 0; i < 40; i++) { const next = nearestTime(TIMES, hm(9) + (i % 2 ? 5 : -5), cur); if (next !== cur) flips++; cur = next; }
  assert.equal(flips, 0);
  // wrap over midnight: 01:45 is the 2000/0730 boundary
  assert.equal(nearestTime(TIMES, hm(1, 55), '2000'), '2000');
  assert.equal(nearestTime(TIMES, hm(2, 30), '2000'), '0730');
});

const good = () => ({ time: '1805', preset: 'sunset_artistic', ground_tile_gain: 1.1,
  groups: { stadium_shell: { file: 'stadium_shell_light.ktx2', bytes: 10, sha256: 'a'.repeat(64), intensity: 25.9 } }, panorama: null });

test('parseTod accepts a good file and rejects bad ones', () => {
  assert.equal(parseTod(good(), '1805').time, '1805');
  assert.throws(() => parseTod(good(), '1030'), /time is 1805/);
  assert.throws(() => parseTod({ ...good(), preset: 'night' }, '1805'), /preset/);
  assert.throws(() => parseTod({ ...good(), groups: {} }, '1805'), /groups/);
  assert.throws(() => parseTod({ ...good(), ground_tile_gain: undefined }, '1805'), /ground_tile_gain/);
  assert.throws(() => parseTod({ ...good(), groups: { a: { file: 'x' } } }, '1805'), /intensity/);
  assert.throws(() => parseTod(null), /not an object/);
  assert.deepEqual(TIMES.map((t) => PRESETS[t]), ['morning_golden', 'daylight_artistic', 'sunset_artistic', 'night']);
});

const tex = (name) => ({ name, disposed: 0, dispose() { this.disposed++; } });
const mat = (group, texCoord, lightMap, intensity) => ({ userData: { talanta_bake_group: group, talanta_lightmap: { texCoord, intensity }, heroDaylight: { intensity } }, lightMap, lightMapIntensity: intensity });
const meshOf = (material, name = 'm') => ({ isMesh: true, name, material });
const rootOf = (...meshes) => ({ traverse(fn) { meshes.forEach(fn); } });

test('applyLightmaps sets channel, colour space, intensity and returns the old textures', () => {
  const oldShell = tex('old'), oldPaint = tex('oldp');
  const a = mat('stadium_shell', 0, oldShell, 8), b = mat('shields', 1, oldPaint, 5), c = mat('stadium_shell', 0, oldShell, 8);
  const entries = collectLightmapped(rootOf(meshOf(a), meshOf(b), meshOf(c), meshOf(a), meshOf({ userData: {} })));
  assert.equal(entries.length, 3);   // shared material once, plain material skipped
  const t1 = tex('new'), t2 = tex('newp');
  const replaced = applyLightmaps(entries, new Map([['stadium_shell', t1], ['shields', t2]]), new Map([['stadium_shell', 25.9], ['shields', 11.5]]));
  assert.equal(a.lightMap, t1); assert.equal(c.lightMap, t1); assert.equal(b.lightMap, t2);
  assert.equal(a.lightMapIntensity, 25.9); assert.equal(b.lightMapIntensity, 11.5);
  assert.equal(a.userData.heroDaylight.intensity, 25.9);
  assert.equal(t1.channel, 0); assert.equal(t2.channel, 1);
  assert.equal(t1.colorSpace, THREE.SRGBColorSpace); assert.equal(t1.flipY, false);
  assert.deepEqual([...replaced].sort((x, y) => x.name.localeCompare(y.name)), [oldShell, oldPaint].sort((x, y) => x.name.localeCompare(y.name)));
});

test('a group without a new texture keeps its material unchanged', () => {
  const old = tex('old'), a = mat('landmarks', 0, old, 3);
  const replaced = applyLightmaps(collectLightmapped(rootOf(meshOf(a))), new Map(), new Map());
  assert.equal(a.lightMap, old); assert.equal(a.lightMapIntensity, 3); assert.equal(replaced.size, 0);
});

test('ground gain sets the tile colour and the heroLighting baseline', () => {
  const m = { color: new THREE.Color(1, 1, 1), userData: { heroDaylight: { color: [1, 1, 1] } } };
  applyGroundGain([m], 0.25);
  assert.equal(m.color.r, 0.25); assert.deepEqual(m.userData.heroDaylight.color, [0.25, 0.25, 0.25]);
  applyGroundGain([m], 1);
  assert.equal(m.color.g, 1);
});

function harness({ failTime = null, withPano = true } = {}) {
  const base = tex('base'), shield = tex('shield');
  const m1 = mat('stadium_shell', 0, base, 8), m2 = mat('shields', 1, shield, 5);
  const tile = { isMesh: true, name: 'hero-ground-L0_0_0.ktx2', material: { color: new THREE.Color(1, 1, 1), userData: {} } };
  const group = rootOf(meshOf(m1), meshOf(m2), tile);
  const made = [], envCalls = [], scene = { background: null, environment: null, backgroundRotation: new THREE.Euler(), environmentRotation: new THREE.Euler() };
  const tods = { '1030': { ...good(), time: '1030', preset: 'daylight_artistic', ground_tile_gain: 1.86, panorama: null,
      groups: { stadium_shell: { file: 'a.ktx2', bytes: 1, sha256: 'b'.repeat(64), intensity: 14 }, shields: { file: 'b.ktx2', bytes: 1, sha256: 'b'.repeat(64), intensity: 9 } } },
    '2000': { ...good(), time: '2000', preset: 'night', ground_tile_gain: 0.0087, panorama: withPano ? { hdr: 'talanta_pano_2030_2048.hdr', exr: 'talanta_pano_2030.exr' } : null,
      groups: { stadium_shell: { file: 'c.ktx2', bytes: 1, sha256: 'b'.repeat(64), intensity: 1.2 }, shields: { file: 'd.ktx2', bytes: 1, sha256: 'b'.repeat(64), intensity: 0.8 } } },
    '0730': { ...good(), time: '0730', preset: 'morning_golden', ground_tile_gain: 1, panorama: { hdr: 'talanta_pano_0730_2048.hdr', exr: 'talanta_pano_0730.exr' }, groups: { stadium_shell: { file: 'e', bytes: 1, sha256: 'b'.repeat(64), intensity: 8 } } } };
  const io = {
    async json(url) { const t = url.match(/\/(\d{4})\/tod\.json$/)[1]; if (t === failTime) throw new Error('404'); return tods[t]; },
    async textures(urls) { return urls.map((u) => { const t = tex(u); made.push(t); return t; }); },
    async environment({ manifest }) { envCalls.push(manifest); const texture = tex('env' + envCalls.length); return { texture, rotation: new THREE.Euler(0, 1, 0), dispose() { texture.disposed++; } }; },
  };
  const manifest = { files: [], tod: { base: '0730', times: TIMES, dir: 'lightmaps' } };
  const onEnv = [];
  const api = createTimeOfDay({ group, renderer: {}, scene, base: './', manifest, phone: false, io, onEnvironment: (e, t) => onEnv.push(t) });
  return { api, m1, m2, base, shield, tile, made, envCalls, scene, onEnv, group };
}

test('setTime swaps maps, intensity, ground gain and panorama in one step; the base textures survive', async () => {
  const h = harness();
  assert.equal(await h.api.setTime('1030'), true);
  assert.equal(h.m1.lightMap.name, './lightmaps/1030/a.ktx2'); assert.equal(h.m2.lightMap.channel, 1);
  assert.equal(h.m1.lightMapIntensity, 14); assert.equal(h.tile.material.color.r, 1.86);
  assert.equal(h.base.disposed, 0, 'base texture still cached');
  assert.equal(h.envCalls.length, 1); assert.equal(h.scene.environment.name, 'env1');
  assert.equal(await h.api.setTime('2000'), true);
  assert.equal(h.m1.lightMapIntensity, 1.2); assert.equal(h.tile.material.color.r, 0.0087);
  assert.match(h.envCalls[1].environment.file_2048, /talanta_pano_2030_2048\.hdr$/);
  assert.ok(h.envCalls[1].files.some((f) => f.file === 'app/public/env/talanta_pano_2030.exr'));
  assert.equal(h.scene.environment.name, 'env2');
  assert.deepEqual(h.onEnv, ['1030', '2000']);
  assert.equal(h.api.current, '2000');
});

test('the base time reuses the GLB textures and keeps the base panorama', async () => {
  const h = harness();
  await h.api.setTime('1030'); await h.api.setTime('0730');
  assert.equal(h.m1.lightMap, h.base); assert.equal(h.m1.lightMapIntensity, 8); assert.equal(h.base.disposed, 0);
  assert.equal(h.made.length, 2, 'no maps loaded for the base time');
});

test('a time without panorama in tod.json uses the base-time panorama manifest', async () => {
  const h = harness();
  await h.api.setTime('1030');
  assert.equal(h.envCalls[0].environment, undefined);   // manifest passed through: choosePanorama takes the base-time file
});

test('a failed load keeps the current set and warns once', async () => {
  const h = harness({ failTime: '2000' });
  await h.api.setTime('1030');
  const warns = []; const warn = console.warn; console.warn = (...a) => warns.push(a);
  try { assert.equal(await h.api.setTime('2000'), false); assert.equal(await h.api.setTime('2000'), false); } finally { console.warn = warn; }
  assert.equal(h.m1.lightMap.name, './lightmaps/1030/a.ktx2'); assert.equal(h.m1.lightMapIntensity, 14);
  assert.equal(warns.length, 1);
});

test('phone keeps at most two sets and disposes the replaced one', async () => {
  const h = harness();
  const phone = createTimeOfDay({ group: h.group, renderer: {}, scene: h.scene, base: './', manifest: { files: [], tod: { base: '0730', times: TIMES, dir: 'lightmaps_phone' } }, phone: true, io: {
    json: async (u) => ({ '1030': { ...good(), time: '1030', preset: 'daylight_artistic', groups: { stadium_shell: { file: 'a', bytes: 1, sha256: 'b'.repeat(64), intensity: 14 } } },
                          '2000': { ...good(), time: '2000', preset: 'night', groups: { stadium_shell: { file: 'c', bytes: 1, sha256: 'b'.repeat(64), intensity: 1 } } } }[u.match(/(\d{4})\/tod/)[1]]),
    textures: async (urls) => urls.map((u) => { const t = tex(u); h.made.push(t); return t; }),
    environment: async () => null } });
  await phone.setTime('1030');
  const first = h.m1.lightMap;
  assert.equal(await phone.preload('2000'), false, 'no room to preload on a phone');
  await phone.setTime('2000');
  assert.equal(first.disposed, 1, 'previous set disposed after the swap');
  assert.equal(h.base.disposed, 0);
});

test('without manifest.tod the module is inert', async () => {
  const api = createTimeOfDay({ group: rootOf(), renderer: {}, scene: {}, manifest: {}, io: {} });
  assert.deepEqual(api.times, []); assert.equal(await api.setTime('1030'), false); assert.equal(api.nearest(600), null);
});
