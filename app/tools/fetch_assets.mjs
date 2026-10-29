#!/usr/bin/env node
// Download the baked web hero bundle from its GitHub release, check it against the manifest, and install it.
// Run from app/: npm run fetch-assets [-- options]
//
//   --bundle <tag>      release tag and bundle name (default web_hero_v2)
//   --repo <owner/name> GitHub repository (default M5-Engineering-PLC/talanta-twin)
//   --manifest <file>   bundle manifest with size and sha256 per file
//                       (default ../blender/web_hero/<bundle>_manifest.json)
//   --from <dir>        use the files in a local folder instead of the release (no network)
//   --public <dir>      install root (default app/public)
//   --manifest-phone <file>  phone manifest (default <bundle>_manifest_phone.json next to the manifest; optional): installs
//                       models_phone/*.glb into public/models and writes public/models/manifest_phone.json
//   --check             verify the installed files only; download nothing
//
// Installed layout: public/models/*.glb, public/env/*, public/ground/* and the app manifest public/models/manifest.json.
// Release assets can be flat files (asset name = file basename), split parts listed in the manifest (entry.parts),
// or tar archives (.tar, .tar.gz, .tgz) that hold the bundle tree. Files that already match are not downloaded again.
// The binaries are git-ignored (app/.gitignore). Never commit them.
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const opt = (name, fallback) => { const i = args.indexOf(`--${name}`); return i < 0 ? fallback : args[i + 1]; };
const BUNDLE = opt('bundle', 'web_hero_v2');
const REPO = opt('repo', 'M5-Engineering-PLC/talanta-twin');
const MANIFEST = path.resolve(opt('manifest', path.join(APP, '..', 'blender', 'web_hero', `${BUNDLE}_manifest.json`)));
const MANIFEST_PHONE = path.resolve(opt('manifest-phone', MANIFEST.replace(/_manifest\.json$/, '_manifest_phone.json')));
const FROM = opt('from', null);
const PUBLIC = path.resolve(opt('public', path.join(APP, 'public')));
const CHECK_ONLY = args.includes('--check');
const CACHE = path.join(APP, '.fetch-cache', BUNDLE);
const GH = process.env.GH_BIN || 'gh';

const fail = (msg) => { console.error(`fetch-assets: ${msg}`); process.exit(1); };
const rel = (p) => path.relative(process.cwd(), p) || '.';

// Bundle path (models/x, env/x, ground/x) to the install path under public/.
const SUBDIRS = new Set(['models', 'env', 'ground']);
// ENV-01: lightmaps/<HHMM>/x and lightmaps_phone/<HHMM>/x keep their folders; models_phone/x goes next to the other models.
function installPath(file) {
  const parts = file.split('/');
  if (parts.length === 3 && /^lightmaps(_phone)?$/.test(parts[0]) && /^\d{4}$/.test(parts[1]) && /^[\w.-]+$/.test(parts[2])) return path.join(PUBLIC, ...parts);
  if (parts.length === 2 && parts[0] === 'models_phone' && /^[\w.-]+$/.test(parts[1])) return path.join(PUBLIC, 'models', parts[1]);
  if (parts.length !== 2 || !SUBDIRS.has(parts[0]) || !/^[\w.-]+$/.test(parts[1])) fail(`unexpected file path in manifest: ${file}`);
  return path.join(PUBLIC, parts[0], parts[1]);
}

function sha256(file) {
  const hash = createHash('sha256');
  const fd = fs.openSync(file, 'r'); const buf = Buffer.alloc(1 << 20);
  try { let n; while ((n = fs.readSync(fd, buf, 0, buf.length, null)) > 0) hash.update(buf.subarray(0, n)); } finally { fs.closeSync(fd); }
  return hash.digest('hex');
}
function matches(file, entry) {
  if (!fs.existsSync(file)) return false;
  if (fs.statSync(file).size !== entry.bytes) return false;
  return sha256(file) === entry.sha256;
}

if (!fs.existsSync(MANIFEST)) fail(`manifest not found: ${rel(MANIFEST)}`);
const manifest = JSON.parse(fs.readFileSync(MANIFEST, 'utf8'));
if (!Array.isArray(manifest.files) || !manifest.files.length) fail('manifest.files is missing or empty');
const phoneManifest = MANIFEST_PHONE !== MANIFEST && fs.existsSync(MANIFEST_PHONE) ? JSON.parse(fs.readFileSync(MANIFEST_PHONE, 'utf8')) : null;
const phoneModelFiles = (phoneManifest?.tier1_files ?? []).filter((e) => e.file.startsWith('models_phone/'));
// What gets installed: the bundle files, the time-of-day sets (manifest.tod_files) and, with a phone manifest, the phone models and phone sets.
const installList = [...manifest.files, ...(manifest.tod_files ?? []), ...phoneModelFiles, ...(phoneManifest?.tod_files ?? [])];
for (const e of installList) {
  if (!e.file || !Number.isInteger(e.bytes) || !/^[0-9a-f]{64}$/.test(e.sha256 ?? '')) fail(`bad manifest entry: ${JSON.stringify(e)}`);
  for (const p of e.parts ?? []) if (!p.file || !Number.isInteger(p.bytes) || !/^[0-9a-f]{64}$/.test(p.sha256 ?? '')) fail(`bad part entry for ${e.file}`);
}

// 1. What is already installed and correct?
const missing = installList.filter((e) => !matches(installPath(e.file), e));
console.log(`fetch-assets: ${BUNDLE}: ${installList.length - missing.length} of ${installList.length} files already installed and verified`);
if (CHECK_ONLY) {
  for (const e of missing) console.log(`  missing or changed: ${e.file}`);
  process.exit(missing.length ? 1 : 0);
}

// 2. Get the missing files into the staging folder.
const base = (f) => f.split('/').at(-1);
const wanted = new Set(missing.flatMap((e) => (e.parts?.length ? e.parts.map((p) => base(p.file)) : [base(e.file)])));
let source = CACHE;
if (missing.length) {
  if (FROM) {
    source = path.resolve(FROM);
    if (!fs.existsSync(source)) fail(`--from folder not found: ${rel(source)}`);
  } else {
    fs.mkdirSync(CACHE, { recursive: true });
    let assets;
    try {
      assets = JSON.parse(execFileSync(GH, ['release', 'view', BUNDLE, '--repo', REPO, '--json', 'assets'], { encoding: 'utf8' })).assets.map((a) => a.name);
    } catch (error) {
      fail(`cannot read release ${BUNDLE} on ${REPO} (${error.message.split('\n')[0]}). Is it published, and is gh logged in?`);
    }
    const flat = assets.filter((a) => wanted.has(a));
    const archives = assets.filter((a) => /\.(tar|tar\.gz|tgz)$/.test(a));
    const patterns = flat.length === wanted.size ? flat : [...flat, ...archives];
    if (!patterns.length) fail(`release ${BUNDLE} has none of the ${wanted.size} needed files and no tar archive`);
    console.log(`fetch-assets: downloading ${patterns.length} asset(s) from ${REPO} release ${BUNDLE}`);
    execFileSync(GH, ['release', 'download', BUNDLE, '--repo', REPO, '--dir', CACHE, '--clobber', ...patterns.flatMap((p) => ['--pattern', p])], { stdio: 'inherit' });
  }
}

// Archives in the source folder are unpacked into <source>/.unpacked (the bundle tree, or a folder that holds it).
const unpacked = path.join(FROM ? path.join(CACHE, 'unpacked-from') : CACHE, '.unpacked');
if (missing.length) {
  const archives = fs.readdirSync(source).filter((a) => /\.(tar|tar\.gz|tgz)$/.test(a));
  if (archives.length) {
    fs.rmSync(unpacked, { recursive: true, force: true }); fs.mkdirSync(unpacked, { recursive: true });
    for (const a of archives) execFileSync('tar', ['-xf', path.join(source, a), '-C', unpacked, '--no-same-owner'], { stdio: 'inherit' });
  }
}
function walk(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((d) => (d.isDirectory() ? walk(path.join(dir, d.name)) : [path.join(dir, d.name)]));
}
// A --from folder can also hold the bundle tree itself (models/, env/, ground/), e.g. an archive unpacked by hand.
const unpackedFiles = [...walk(unpacked), ...(FROM ? walk(source) : [])];
// Find a file by its bundle path: flat by basename first, then in an unpacked archive or a --from tree (path suffix match).
function locate(file) {
  const flat = path.join(source, base(file));
  if (!/^lightmaps/.test(file) && fs.existsSync(flat)) return flat;  // the same basename sits in every time folder
  const suffix = path.sep + file.split('/').join(path.sep);
  return unpackedFiles.find((f) => f.endsWith(suffix)) ?? unpackedFiles.find((f) => path.basename(f) === base(file)) ?? null;
}

// 3. Rejoin split parts, verify each file, and install it.
const bad = [];
for (const e of missing) {
  const dest = installPath(e.file);
  const tmp = `${dest}.part-${process.pid}`;
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  try {
    if (e.parts?.length) {
      const out = fs.openSync(tmp, 'w');
      try {
        for (const p of e.parts) {
          const src = locate(p.file);
          if (!src) throw new Error(`part ${p.file} not found`);
          if (!matches(src, p)) throw new Error(`part ${p.file} has the wrong size or sha256`);
          fs.writeSync(out, fs.readFileSync(src));
        }
      } finally { fs.closeSync(out); }
    } else {
      const src = locate(e.file);
      if (!src) throw new Error('not found in the release or source folder');
      fs.copyFileSync(src, tmp);
    }
    const size = fs.statSync(tmp).size;
    if (size !== e.bytes) throw new Error(`size ${size}, manifest ${e.bytes}`);
    const digest = sha256(tmp);
    if (digest !== e.sha256) throw new Error(`sha256 ${digest.slice(0, 12)}..., manifest ${e.sha256.slice(0, 12)}...`);
    fs.renameSync(tmp, dest);
    console.log(`  ok ${e.file} (${e.bytes} bytes)`);
  } catch (error) {
    fs.rmSync(tmp, { force: true });
    bad.push(`${e.file}: ${error.message}`);
  }
}
if (bad.length) fail(`${bad.length} file(s) failed:\n  ${bad.join('\n  ')}\nThose files were not installed. Fix the release and run again.`);

// 4. Write the app manifest (format read by src/hero/loadHero.js, environment.js and ground.js).
const appFile = (p) => `app/public/${p}`;
// src/hero/environment.js loads panoramas with HDRLoader only, so `file` must be a Radiance .hdr. Until the app can
// read EXR, the 2048 HDR serves both sizes (as in stage_app_preview.py) and the 8K EXR stays listed under file_exr.
// A bundle built without panorama logs (web_hero_v3) lists none: derive them from the env files, 07:30 first.
const derived = [...new Set(manifest.files.filter((e) => /^env\/.+_2048\.hdr$/.test(e.file)).map((e) => base(e.file).replace(/_2048\.hdr$/, '')))].sort().map((stem) => {
  const exr = manifest.files.find((e) => e.file === `env/${stem}.exr`);
  return { preset: stem.replace(/^talanta_pano_/, ''), file: exr ? `env/${stem}.exr` : `env/${stem}_2048.hdr`, file_2048: `env/${stem}_2048.hdr`, resolution: exr ? [8192, 4096] : undefined };
});
const panoramas = (manifest.panoramas?.length ? manifest.panoramas : derived).map((p) => {
  const full = appFile(`env/${base(p.file)}`);
  const small = p.file_2048 ? appFile(`env/${base(p.file_2048)}`) : null;
  const hdr = full.endsWith('.hdr') ? full : small;
  return {
    preset: p.preset,
    file: hdr,
    file_2048: small ?? hdr,
    file_exr: full.endsWith('.exr') ? full : null,
    resolution: p.resolution, sun_dir_app: p.sun_dir_app, near_cut_m: p.near_cut_m, camera_app: p.camera_app,
    centre_of_image_looks: p.centre_of_image_looks, colour: p.colour,
  };
});
const models = Object.fromEntries(Object.entries(manifest.models ?? {}).map(([k, v]) => {
  const file = `models/${base(v.file)}`;
  return [k, { ...v, file: appFile(file), bytes: manifest.files.find((e) => e.file === file)?.bytes ?? v.bytes }];
}));
const hasTiles = manifest.files.some((e) => e.file === 'ground/tiles.json');
const appManifest = {
  bundle: BUNDLE, generated: manifest.generated, installed: new Date().toISOString(),
  source: `GitHub release ${BUNDLE} on ${REPO}, checked against ${path.relative(path.join(APP, '..'), MANIFEST)}`,
  frame: manifest.frame,
  time: { date: manifest.sun?.date, local: manifest.sun?.local },
  sun: manifest.sun,
  files: manifest.files.map((e) => ({ file: appFile(e.file), bytes: e.bytes, sha256: e.sha256 })),
  models,
  lightmaps: manifest.lightmaps,
  // The first entry (07:30, morning_golden) is the default and matches the baked lightmaps.
  environment: panoramas[0] ?? null,
  environments: Object.fromEntries(panoramas.map((p) => [p.preset, p])),
  ...(manifest.tod ? { tod: manifest.tod } : {}),
  ground: hasTiles ? { index: appFile('ground/tiles.json') } : null,
  tone_mapping: { blender_view_transform: 'AgX', blender_exposure_ev: -1.0, three: 'AgXToneMapping, toneMappingExposure = 2^-1 (approved morning look)' },
  labels: manifest.labels,
};
fs.mkdirSync(path.join(PUBLIC, 'models'), { recursive: true });
fs.writeFileSync(path.join(PUBLIC, 'models', 'manifest.json'), `${JSON.stringify(appManifest, null, 1)}\n`);
if (phoneManifest) {  // phone: same app manifest, the phone models and the phone time-of-day sets (read by loadHero with phone: true)
  const phoneModels = Object.fromEntries(Object.entries(phoneManifest.models ?? {}).map(([k, v]) => {
    const e = phoneModelFiles.find((f) => base(f.file) === base(v.file));
    return [k, { ...v, file: appFile(`models/${base(v.file)}`), bytes: e?.bytes ?? v.bytes }];
  }));
  const phoneApp = { ...appManifest, variant: 'phone', models: phoneModels,
    files: [...appManifest.files, ...phoneModelFiles.map((e) => ({ file: appFile(`models/${base(e.file)}`), bytes: e.bytes, sha256: e.sha256 }))] };
  if (phoneManifest.tod) phoneApp.tod = phoneManifest.tod; else delete phoneApp.tod;
  fs.writeFileSync(path.join(PUBLIC, 'models', 'manifest_phone.json'), `${JSON.stringify(phoneApp, null, 1)}\n`);
}
console.log(`fetch-assets: ${BUNDLE} installed in ${rel(PUBLIC)} (${installList.length} files, ${manifest.total_bytes ?? '?'} bytes); app manifest written`);
fs.rmSync(path.join(APP, '.fetch-cache'), { recursive: true, force: true });
