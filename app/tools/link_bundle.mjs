#!/usr/bin/env node
// Read-only bundle mount. Run from the repository root: node app/tools/link_bundle.mjs.
// --bundle <directory> and --public <directory> support isolated local tests.
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { createReadStream } from 'node:fs';
import { normalizeManifest } from '../src/hero/manifest.js';

const app = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
async function present(file) {
  try { return await fs.lstat(file); } catch (error) { if (error.code === 'ENOENT') return null; throw error; }
}
export async function linkBundle({ bundle = path.resolve(app, '../assets/web_hero_v3'), publicRoot = path.join(app, 'public') } = {}) {
  bundle = path.resolve(bundle); publicRoot = path.resolve(publicRoot);
  const links = { models: bundle, env: path.join(bundle, 'env'), ground: path.join(bundle, 'ground'),
    lightmaps: path.join(bundle, 'lightmaps'), lightmaps_phone: path.join(bundle, 'lightmaps_phone') };
  // Preflight every destination before changing any link. Never traverse an existing link to write.
  if ((await present(publicRoot))?.isSymbolicLink()) throw new Error(`Refusing public root symlink: ${publicRoot}`);
  for (const name of Object.keys(links)) {
    const info = await present(path.join(publicRoot, name));
    if (info && !info.isSymbolicLink()) throw new Error(`Refusing to replace a real directory or file: ${path.join(publicRoot, name)}`);
  }
  const read = async file => JSON.parse(await fs.readFile(path.join(bundle, file), 'utf8'));
  const desktop = await read('manifest.json'), phone = await read('manifest_phone.json');
  if (desktop.bundle !== phone.bundle) throw new Error('Bundle manifests name different bundles');
  const all = new Map();
  for (const manifest of [desktop, phone]) for (const entry of [...(manifest.files ?? manifest.tier1_files ?? []), ...(manifest.tod_files ?? [])]) {
    if (!/^(models|models_phone|env|ground|lightmaps|lightmaps_phone)\/[\w./-]+$/.test(entry.file) || entry.file.split('/').includes('..')) throw new Error(`Unsafe manifest path: ${entry.file}`);
    const prior = all.get(entry.file);
    if (prior && (prior.sha256 !== entry.sha256 || prior.bytes !== entry.bytes)) throw new Error(`Conflicting manifest entry: ${entry.file}`);
    all.set(entry.file, entry);
  }
  const fetched = new Set();
  function requireFile(file) {
    if (!all.has(file)) throw new Error(`Fetched path is not listed in either manifest: ${file}`);
    fetched.add(file);
  }
  for (const manifest of [desktop, phone]) {
    const normalized = normalizeManifest(manifest);
    for (const model of Object.values(normalized.models)) requireFile(model.file.replace('app/public/models/', ''));
    if (!manifest.tod?.times?.length) throw new Error('The bundle has no time-of-day sets');
    for (const time of manifest.tod.times) {
      const file = `${manifest.tod.dir}/${time}/tod.json`; requireFile(file);
      const tod = await read(file);
      for (const group of Object.values(tod.groups)) requireFile(`${manifest.tod.dir}/${time}/${group.file}`);
      for (const pano of [tod.panorama?.hdr, tod.panorama?.exr].filter(Boolean)) requireFile(`env/${pano}`);
    }
  }
  requireFile('ground/tiles.json');
  const ground = await read('ground/tiles.json');
  for (const tile of ground.tiles) requireFile(`ground/${tile.file}`);
  for (const file of all.keys()) if (file.startsWith('env/')) requireFile(file);
  // Size and digest checks also detect stale or incomplete bundle copies.
  for (const [file, entry] of all) {
    const source = path.join(bundle, file), stat = await fs.stat(source);
    if (!stat.isFile() || stat.size !== entry.bytes) throw new Error(`Bundle size mismatch: ${file}`);
    const hash = createHash('sha256');
    for await (const chunk of createReadStream(source)) hash.update(chunk);
    if (hash.digest('hex') !== entry.sha256) throw new Error(`Bundle sha256 mismatch: ${file}`);
  }
  await fs.mkdir(publicRoot, { recursive: true });
  for (const [name, target] of Object.entries(links)) {
    const dest = path.join(publicRoot, name);
    const info = await present(dest);
    if (info && !info.isSymbolicLink()) throw new Error(`Refusing to replace a real directory or file: ${dest}`);
    if (info) await fs.unlink(dest);
    await fs.symlink(target, dest, 'dir');
  }
  return `${desktop.bundle}: ${all.size} files match size and sha256; ${fetched.size} fetched paths are listed; ${Object.keys(links).length} public links installed`;
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2), value = key => { const i = args.indexOf(key); return i < 0 ? undefined : args[i + 1]; };
  try { console.log(await linkBundle({ bundle: value('--bundle'), publicRoot: value('--public') })); }
  catch (error) { console.error(`link-bundle: ${error.message}`); process.exitCode = 1; }
}
