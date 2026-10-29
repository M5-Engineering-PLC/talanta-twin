// Tests for fetch_assets.mjs with a small fake bundle and a fake gh. No network.
// Run from app/: node --test tools/
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const SCRIPT = path.join(path.dirname(fileURLToPath(import.meta.url)), 'fetch_assets.mjs');
const BUNDLE = 'test_bundle';
const sha = (buf) => createHash('sha256').update(buf).digest('hex');

// The fake gh serves the files in $FAKE_RELEASE and logs each call to $FAKE_GH_LOG.
const FAKE_GH = `#!/usr/bin/env node
const fs = require('fs'), path = require('path');
const a = process.argv.slice(2), rel = process.env.FAKE_RELEASE;
fs.appendFileSync(process.env.FAKE_GH_LOG, a.join(' ') + '\\n');
if (a[0] === 'release' && a[1] === 'view') { console.log(JSON.stringify({ assets: fs.readdirSync(rel).map((name) => ({ name })) })); process.exit(0); }
if (a[0] === 'release' && a[1] === 'download') {
  const dir = a[a.indexOf('--dir') + 1];
  a.forEach((x, i) => { if (x === '--pattern') fs.copyFileSync(path.join(rel, a[i + 1]), path.join(dir, a[i + 1])); });
  process.exit(0);
}
process.exit(2);
`;

// A bundle tree, its manifest, and a release folder that holds the tree as one tar (like web_hero_v1).
function setup() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'fetch-assets-'));
  const tree = path.join(root, 'tree', BUNDLE);
  const content = {
    'models/talanta_hero.glb': Buffer.from('glb hero'),
    'models/talanta_site.glb': Buffer.from('glb site'),
    'env/talanta_pano_0730.exr': Buffer.from('exr 8k'),
    'env/talanta_pano_0730_2048.hdr': Buffer.from('hdr 2048'),
    'ground/tiles.json': Buffer.from('{"tiles":[]}'),
    // Same basename in two folders: the lookup inside the tar must use the folder too.
    'ground/readme.json': Buffer.from('ground'),
    'env/readme.json': Buffer.from('env'),
  };
  for (const [file, buf] of Object.entries(content)) {
    fs.mkdirSync(path.join(tree, path.dirname(file)), { recursive: true });
    fs.writeFileSync(path.join(tree, file), buf);
  }
  const src = `blender/out/web_hero/${BUNDLE}`;
  const manifest = {
    bundle: BUNDLE, generated: '2026-10-19T00:00:00Z', frame: { up: 'y' },
    sun: { date: '2026-10-19', local: '07:30' },
    files: Object.entries(content).map(([file, buf]) => ({ file, bytes: buf.length, sha256: sha(buf) })),
    total_bytes: Object.values(content).reduce((n, b) => n + b.length, 0),
    models: {
      hero: { file: `${src}/models/talanta_hero.glb`, bytes: 8 },
      site: { file: `${src}/models/talanta_site.glb`, bytes: 8 },
    },
    panoramas: [{ preset: 'morning_golden', file: `${src}/env/talanta_pano_0730.exr`, file_2048: `${src}/env/talanta_pano_0730_2048.hdr`, resolution: [8192, 4096] }],
    lightmaps: { count: 0 }, labels: { people: 'Visualization' },
  };
  const manifestFile = path.join(root, 'manifest.json');
  fs.writeFileSync(manifestFile, JSON.stringify(manifest));
  const release = path.join(root, 'release');
  fs.mkdirSync(release);
  execFileSync('tar', ['-cf', path.join(release, `${BUNDLE}.tar`), '-C', path.join(root, 'tree'), BUNDLE]);
  const gh = path.join(root, 'gh');
  fs.writeFileSync(gh, FAKE_GH, { mode: 0o755 });
  const log = path.join(root, 'gh.log');
  fs.writeFileSync(log, '');
  return { root, tree, content, manifest, manifestFile, release, gh, log, pub: path.join(root, 'public') };
}

function run(t, ...extra) {
  const r = spawnSync(process.execPath, [SCRIPT, '--bundle', BUNDLE, '--manifest', t.manifestFile, '--public', t.pub, ...extra], {
    encoding: 'utf8', env: { ...process.env, GH_BIN: t.gh, FAKE_RELEASE: t.release, FAKE_GH_LOG: t.log },
  });
  return { code: r.status, out: r.stdout + r.stderr };
}
const downloads = (t) => fs.readFileSync(t.log, 'utf8').split('\n').filter((l) => l.startsWith('release download')).length;

test('installs from a release tar, verifies every file and writes the app manifest', () => {
  const t = setup();
  const r = run(t);
  assert.equal(r.code, 0, r.out);
  for (const [file, buf] of Object.entries(t.content)) assert.deepEqual(fs.readFileSync(path.join(t.pub, file)), buf, file);
  const app = JSON.parse(fs.readFileSync(path.join(t.pub, 'models', 'manifest.json'), 'utf8'));
  assert.equal(app.models.hero.file, 'app/public/models/talanta_hero.glb');
  // HDRLoader cannot read EXR: both sizes point at the 2048 HDR, the EXR stays listed.
  assert.equal(app.environment.file, 'app/public/env/talanta_pano_0730_2048.hdr');
  assert.equal(app.environment.file_2048, 'app/public/env/talanta_pano_0730_2048.hdr');
  assert.equal(app.environment.file_exr, 'app/public/env/talanta_pano_0730.exr');
  assert.ok(app.files.some((f) => f.file === app.environment.file), 'environment file must be in files (environment.js)');
  assert.deepEqual(app.ground, { index: 'app/public/ground/tiles.json' });
  assert.equal(downloads(t), 1);
});

test('a second run downloads nothing, and --check passes', () => {
  const t = setup();
  assert.equal(run(t).code, 0);
  const r = run(t);
  assert.equal(r.code, 0, r.out);
  assert.match(r.out, /7 of 7 files already installed/);
  assert.equal(downloads(t), 1);
  assert.equal(run(t, '--check').code, 0);
});

test('--check fails and names a changed file', () => {
  const t = setup();
  assert.equal(run(t).code, 0);
  fs.writeFileSync(path.join(t.pub, 'models/talanta_site.glb'), 'tampered');
  const r = run(t, '--check');
  assert.equal(r.code, 1);
  assert.match(r.out, /missing or changed: models\/talanta_site\.glb/);
});

test('a corrupt file in the release is rejected and not installed', () => {
  const t = setup();
  fs.writeFileSync(path.join(t.tree, 'models/talanta_hero.glb'), 'glb HERO');  // same size, other bytes
  execFileSync('tar', ['-cf', path.join(t.release, `${BUNDLE}.tar`), '-C', path.dirname(t.tree), BUNDLE]);
  const r = run(t);
  assert.equal(r.code, 1);
  assert.match(r.out, /models\/talanta_hero\.glb: sha256/);
  assert.ok(!fs.existsSync(path.join(t.pub, 'models/talanta_hero.glb')));
  assert.ok(!fs.existsSync(path.join(t.pub, 'models/manifest.json')), 'no app manifest after a failure');
});

test('a file missing from the release fails the run', () => {
  const t = setup();
  fs.rmSync(path.join(t.tree, 'ground/tiles.json'));
  execFileSync('tar', ['-cf', path.join(t.release, `${BUNDLE}.tar`), '-C', path.dirname(t.tree), BUNDLE]);
  const r = run(t);
  assert.equal(r.code, 1);
  assert.match(r.out, /ground\/tiles\.json: not found/);
});

test('--from a local folder with flat files and split parts, no gh call', () => {
  const t = setup();
  const from = path.join(t.root, 'from');
  fs.mkdirSync(from);
  for (const e of t.manifest.files) if (!e.file.endsWith('readme.json')) fs.copyFileSync(path.join(t.tree, e.file), path.join(from, path.basename(e.file)));
  // Split the hero GLB into two parts listed in the manifest.
  const hero = t.manifest.files.find((e) => e.file === 'models/talanta_hero.glb');
  const buf = t.content[hero.file];
  hero.parts = [buf.subarray(0, 3), buf.subarray(3)].map((b, i) => {
    fs.writeFileSync(path.join(from, `talanta_hero.glb.part${i}`), b);
    return { file: `models/talanta_hero.glb.part${i}`, bytes: b.length, sha256: sha(b) };
  });
  fs.rmSync(path.join(from, 'talanta_hero.glb'));
  // Flat files cannot carry two readme.json; drop them from this manifest.
  t.manifest.files = t.manifest.files.filter((e) => !e.file.endsWith('readme.json'));
  fs.writeFileSync(t.manifestFile, JSON.stringify(t.manifest));
  const r = run(t, '--from', from);
  assert.equal(r.code, 0, r.out);
  assert.deepEqual(fs.readFileSync(path.join(t.pub, 'models/talanta_hero.glb')), buf);
  assert.equal(fs.readFileSync(t.log, 'utf8'), '');
});

test('--from a folder that holds the bundle tree', () => {
  const t = setup();
  const r = run(t, '--from', t.tree);
  assert.equal(r.code, 0, r.out);
  for (const [file, buf] of Object.entries(t.content)) assert.deepEqual(fs.readFileSync(path.join(t.pub, file)), buf, file);
  assert.equal(fs.readFileSync(t.log, 'utf8'), '');
});

test('a manifest path outside models/, env/ or ground/ is refused', () => {
  const t = setup();
  t.manifest.files.push({ file: '../../etc/x', bytes: 1, sha256: 'a'.repeat(64) });
  fs.writeFileSync(t.manifestFile, JSON.stringify(t.manifest));
  const r = run(t);
  assert.equal(r.code, 1);
  assert.match(r.out, /unexpected file path in manifest/);
});

test('ENV-01: tod sets, phone models and manifest_phone.json are installed from a --from tree', () => {
  const t = setup();
  const extra = { 'lightmaps/1805/roof_light.ktx2': Buffer.from('k1805'), 'lightmaps/2000/roof_light.ktx2': Buffer.from('k2000'),
    'lightmaps_phone/1805/roof_light.ktx2': Buffer.from('p1805'), 'models_phone/talanta_hero_phone.glb': Buffer.from('phone hero') };
  for (const [file, buf] of Object.entries(extra)) { fs.mkdirSync(path.join(t.tree, path.dirname(file)), { recursive: true }); fs.writeFileSync(path.join(t.tree, file), buf); }
  const ent = (f) => ({ file: f, bytes: extra[f].length, sha256: sha(extra[f]) });
  const man = { ...t.manifest, tod: { base: '0730', times: ['0730', '1805', '2000'], dir: 'lightmaps' }, tod_files: ['lightmaps/1805/roof_light.ktx2', 'lightmaps/2000/roof_light.ktx2'].map(ent) };
  fs.writeFileSync(t.manifestFile, JSON.stringify(man));
  const phone = { variant: 'phone', tier1_files: [ent('models_phone/talanta_hero_phone.glb')], tod: { base: '0730', times: ['0730', '1805'], dir: 'lightmaps_phone' },
    tod_files: [ent('lightmaps_phone/1805/roof_light.ktx2')], models: { hero: { file: 'blender/out/x/models_phone/talanta_hero_phone.glb', bytes: 10 } } };
  fs.writeFileSync(t.manifestFile.replace(/manifest\.json$/, 'x_manifest_phone.json'), JSON.stringify(phone));
  const r = run(t, '--from', path.join(t.root, 'tree'), '--manifest-phone', t.manifestFile.replace(/manifest\.json$/, 'x_manifest_phone.json'));
  assert.equal(r.code, 0, r.out);
  assert.deepEqual(fs.readFileSync(path.join(t.pub, 'lightmaps/1805/roof_light.ktx2')), extra['lightmaps/1805/roof_light.ktx2']);
  assert.deepEqual(fs.readFileSync(path.join(t.pub, 'lightmaps/2000/roof_light.ktx2')), extra['lightmaps/2000/roof_light.ktx2'], 'same basename in another time folder');
  assert.deepEqual(fs.readFileSync(path.join(t.pub, 'lightmaps_phone/1805/roof_light.ktx2')), extra['lightmaps_phone/1805/roof_light.ktx2']);
  assert.ok(fs.existsSync(path.join(t.pub, 'models/talanta_hero_phone.glb')));
  const app = JSON.parse(fs.readFileSync(path.join(t.pub, 'models', 'manifest.json'), 'utf8'));
  const pm = JSON.parse(fs.readFileSync(path.join(t.pub, 'models', 'manifest_phone.json'), 'utf8'));
  assert.equal(app.tod.dir, 'lightmaps'); assert.equal(pm.tod.dir, 'lightmaps_phone');
  assert.equal(pm.models.hero.file, 'app/public/models/talanta_hero_phone.glb'); assert.equal(pm.models.hero.bytes, 10);
  assert.equal(app.models.hero.file, 'app/public/models/talanta_hero.glb');
});

test('ENV-01: a bundle without panorama logs gets its environment from the env files', () => {
  const t = setup();
  const m = { ...t.manifest, panoramas: [] };
  fs.writeFileSync(t.manifestFile, JSON.stringify(m));
  assert.equal(run(t).code, 0);
  const app = JSON.parse(fs.readFileSync(path.join(t.pub, 'models', 'manifest.json'), 'utf8'));
  assert.equal(app.environment.file_2048, 'app/public/env/talanta_pano_0730_2048.hdr');
  assert.equal(app.environment.file_exr, 'app/public/env/talanta_pano_0730.exr');
});
