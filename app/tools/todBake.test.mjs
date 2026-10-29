// ENV-01: post_glb.mjs tod mode (pure checks in blender/web_hero/node/tod_lib.mjs, plus dry runs on a tiny fake set).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import zlib from 'node:zlib';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
const sha = (b) => createHash('sha256').update(b).digest('hex');
import { fileURLToPath } from 'node:url';
import * as T from '../../blender/web_hero/node/tod_lib.mjs';

const POST = fileURLToPath(new URL('../../blender/web_hero/node/post_glb.mjs', import.meta.url));
const crcTable = Array.from({ length: 256 }, (_, n) => { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; return c >>> 0; });
const crc = (b) => { let c = 0xffffffff; for (const x of b) c = crcTable[(c ^ x) & 255] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; };
function chunk(name, data) { const b = Buffer.alloc(12 + data.length); b.writeUInt32BE(data.length, 0); b.write(name, 4, 'latin1'); data.copy(b, 8); b.writeUInt32BE(crc(b.subarray(4, 8 + data.length)), 8 + data.length); return b; }
/** An 8-bit RGB PNG, every pixel (v, v, v), alternate rows use filter 2 (up) to exercise the decoder. */
function png(w, h, v) {
  const rows = [];
  for (let y = 0; y < h; y++) {
    const px = Buffer.alloc(w * 3, y % 2 ? 0 : v);
    rows.push(Buffer.concat([Buffer.from([y % 2 ? 2 : 0]), y % 2 ? px : px]));   // filter 2 with zero residual repeats the row above
  }
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4); ihdr[8] = 8; ihdr[9] = 2;
  return Buffer.concat([Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]), chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(Buffer.concat(rows))), chunk('IEND', Buffer.alloc(0))]);
}

test('PNG size and decode, luminance of a grey map', () => {
  const b = png(8, 4, 255);
  assert.deepEqual(T.pngSize(b), [8, 4]);
  const d = T.decodePng(b); assert.equal(d.data.length, 8 * 4 * 3); assert.ok(d.data.every((x) => x === 255));
  const r = T.pngLuminanceSum(b, 2); assert.equal(r.count, 32); assert.ok(Math.abs(r.sum / r.count - 2) < 1e-9);
  assert.throws(() => T.pngSize(Buffer.from('nope')), /not a PNG/);
});

test('ground gain is the ratio of the mean ground light (maps x light_scale)', () => {
  const groups = { ground_00: { light_scale: 2 }, ground_01: { light_scale: 2 }, stadium_shell: { light_scale: 9 } };
  const base = T.groundLuminance(groups, () => png(4, 4, 255));
  const dim = T.groundLuminance({ ground_00: { light_scale: 1 }, ground_01: { light_scale: 1 } }, () => png(4, 4, 255));
  assert.ok(Math.abs(base - 2) < 1e-9);   // only ground_* count
  assert.equal(T.groundTileGain(dim, base), 0.5);
  assert.throws(() => T.groundTileGain(1, 0), /not usable/);
  assert.throws(() => T.groundLuminance({ roof: { light_scale: 1 } }, () => png(2, 2, 1)), /no ground/);
});

test('checkAgainstBase refuses a group or size mismatch', () => {
  const base = { roof: [2048, 2048], ground_00: [1024, 1024] };
  assert.deepEqual(T.checkAgainstBase(base, { roof: [2048, 2048], ground_00: [1024, 1024] }), []);
  assert.match(T.checkAgainstBase(base, { roof: [2048, 2048] })[0], /ground_00 is in the bundle but not in the set/);
  assert.match(T.checkAgainstBase(base, { ...base, extra: [4, 4] })[0], /extra is in the set but not in the bundle/);
  assert.match(T.checkAgainstBase(base, { roof: [1024, 1024], ground_00: [1024, 1024] })[0], /roof_light is 1024x1024, the bundle has 2048x2048/);
});

test('presets, codec rules and encoded sizes follow the bundle mode', () => {
  assert.deepEqual(['0730', '1030', '1805', '2000'].map((t) => T.TOD_PRESETS[t]), ['morning_golden', 'daylight_artistic', 'sunset_artistic', 'night']);
  assert.throws(() => T.checkHHMM('0900'), /no preset/); assert.throws(() => T.checkHHMM('99'), /four digits/);
  assert.equal(T.hhmmFromEat('07:30 EAT'), '0730');
  assert.deepEqual(T.encodedSize(2048, 2048, 'roof', false), [2048, 2048]);
  assert.deepEqual(T.encodedSize(4096, 4096, 'suburbs', false), [3072, 3072]);
  assert.deepEqual(T.encodedSize(2048, 2048, 'roof', true), [1024, 1024]);
  assert.deepEqual(T.encodedSize(1024, 1024, 'ground_03', true), [256, 256]);
  assert.equal(T.ktxOptions('light', false).isUASTC, true);
  assert.deepEqual([T.ktxOptions('light', true).isUASTC, T.ktxOptions('light', true).qualityLevel, T.ktxOptions('light', false).isSetKTX2SRGBTransferFunc], [false, 255, true]);
});

test('validateTod and panoramaNames', () => {
  const ok = { time: '2000', preset: 'night', ground_tile_gain: 0.01, panorama: { hdr: 'a_2048.hdr', exr: 'a.exr' },
    groups: { roof: { file: 'roof_light.ktx2', bytes: 5, sha256: 'c'.repeat(64), intensity: 1.5 } } };
  assert.equal(T.validateTod(ok), ok);
  assert.throws(() => T.validateTod({ ...ok, preset: 'morning_golden' }), /preset/);
  assert.throws(() => T.validateTod({ ...ok, groups: { roof: { ...ok.groups.roof, sha256: 'x' } } }), /sha256/);
  assert.deepEqual(T.panoramaNames(['talanta_pano_2030.exr', 'talanta_pano_2030_2048.hdr']), { hdr: 'talanta_pano_2030_2048.hdr', exr: 'talanta_pano_2030.exr' });
  assert.equal(T.panoramaNames([]), null);
});

// ---- CLI: a fake bundle and fake sets on disk
function fakeSet(root, name, { time_eat, preset, v, roofSize = 8, groups = ['ground_00', 'roof'] }) {
  const dir = path.join(root, name); fs.mkdirSync(path.join(dir, 'maps'), { recursive: true });
  const g = {}; for (const n of groups) { g[n] = { size: 8, light_scale: 2, objects: [] }; fs.writeFileSync(path.join(dir, 'maps', `${n}_light.png`), png(n === 'roof' ? roofSize : 8, n === 'roof' ? roofSize : 8, v)); }
  fs.writeFileSync(path.join(dir, 'bake_log.json'), JSON.stringify({ date: '2026-01-15', time_eat, light_preset: preset, sun_elevation_deg: 5, sun_azimuth_deg: 250, sun_dir_app: [0, 0, 1], groups: g }));
  return dir;
}
function cli(...args) { const r = spawnSync(process.execPath, [POST, ...args], { encoding: 'utf8' }); return { code: r.status, out: r.stdout, err: r.stderr }; }
function bundle(root) {
  const dir = path.join(root, 'bundle'); fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, 'manifest.json'), JSON.stringify({ bundle: 'b', sun: { local: '07:30 EAT' }, files: [] }));
  return dir;
}

test('tod dry run prints the plan, ground_tile_gain, and writes nothing', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'tod-')); const out = bundle(root);
  const ref = fakeSet(root, 'ref', { time_eat: '07:30', preset: 'morning_golden', v: 255 });
  const set = fakeSet(root, 'set', { time_eat: '18:05', preset: 'sunset_artistic', v: 255 });
  const r = cli('tod=1805', `base=${set}`, `out=${out}`, `ref=${ref}`, 'dry');
  assert.equal(r.code, 0, r.err);
  const plan = JSON.parse(r.out); assert.equal(plan.groups, 2); assert.equal(plan.ground_tile_gain, 1); assert.equal(plan.preset, 'sunset_artistic');
  assert.deepEqual(plan.maps, ['ground_00 8x8', 'roof 8x8']); assert.equal(plan.panorama, null);
  assert.ok(!fs.existsSync(path.join(out, 'lightmaps')), 'dry run writes nothing');
});

test('tod mode refuses a set with another map size or group list (exit 2) and a wrong preset', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'tod-')); const out = bundle(root);
  const ref = fakeSet(root, 'ref', { time_eat: '07:30', preset: 'morning_golden', v: 200 });
  const size = fakeSet(root, 'size', { time_eat: '10:30', preset: 'daylight_artistic', v: 200, roofSize: 16 });
  let r = cli('tod=1030', `base=${size}`, `out=${out}`, `ref=${ref}`, 'dry');
  assert.equal(r.code, 2); assert.match(r.err, /roof_light is 16x16, the bundle has 8x8/);
  const lessGroups = fakeSet(root, 'less', { time_eat: '10:30', preset: 'daylight_artistic', v: 200, groups: ['ground_00'] });
  r = cli('tod=1030', `base=${lessGroups}`, `out=${out}`, `ref=${ref}`, 'dry');
  assert.equal(r.code, 2); assert.match(r.err, /roof is in the bundle but not in the set/);
  const wrong = fakeSet(root, 'wrong', { time_eat: '10:30', preset: 'night', v: 200 });
  r = cli('tod=1030', `base=${wrong}`, `out=${out}`, `ref=${ref}`, 'dry');
  assert.notEqual(r.code, 0); assert.match(r.err, /preset night is not daylight_artistic/);
  r = cli('tod=1030', `base=${ref}`, `out=${out}`, 'dry');
  assert.notEqual(r.code, 0); assert.match(r.err, /no tod_base/);
});

test('reindex lists the tod sets in the manifests and checks sha256', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'tod-')); const out = bundle(root);
  const crypto = sha;
  const file = Buffer.from('ktx'); const dir = path.join(out, 'lightmaps', '1805'); fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, 'roof_light.ktx2'), file);
  const tod = { time: '1805', preset: 'sunset_artistic', ground_tile_gain: 1, panorama: null, groups: { roof: { file: 'roof_light.ktx2', bytes: 3, sha256: crypto(file), intensity: 2 } } };
  fs.writeFileSync(path.join(dir, 'tod.json'), JSON.stringify(tod));
  const r = cli('reindex', `out=${out}`); assert.equal(r.code, 0, r.err);
  const man = JSON.parse(fs.readFileSync(path.join(out, 'manifest.json'), 'utf8'));
  assert.deepEqual(man.tod, { base: '0730', times: ['0730', '1805'], dir: 'lightmaps' });
  assert.deepEqual(man.tod_files.map((f) => f.file), ['lightmaps/1805/roof_light.ktx2', 'lightmaps/1805/tod.json']);
  fs.writeFileSync(path.join(dir, 'roof_light.ktx2'), 'bad');
  assert.notEqual(cli('reindex', `out=${out}`).code, 0);
});
