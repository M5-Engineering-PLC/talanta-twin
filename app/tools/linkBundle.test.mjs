// Software filesystem tests. No asset contents are changed.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { linkBundle } from './link_bundle.mjs';
import { readManifest } from '../src/hero/manifest.js';

const bundle = fileURLToPath(new URL('../../assets/web_hero_v3', import.meta.url));
test('linker mounts both manifests and resolves model fetch paths without changing bundle files', async () => {
  const publicRoot = await fs.mkdtemp(path.join(os.tmpdir(), 'talanta-links-'));
  const source = await fs.readFile(path.join(bundle, 'manifest.json'));
  // Replace an existing directory link without requiring Windows symlink privileges.
  const old = await fs.mkdtemp(path.join(os.tmpdir(), 'talanta-old-'));
  await fs.symlink(old, path.join(publicRoot, 'models'), process.platform === 'win32' ? 'junction' : 'dir');
  const report = await linkBundle({ bundle, publicRoot });
  assert.match(report, /398 files match size and sha256; 398 fetched paths are listed; 5 public links installed/);
  for (const name of ['models', 'env', 'ground', 'lightmaps', 'lightmaps_phone']) assert.equal((await fs.lstat(path.join(publicRoot, name))).isSymbolicLink(), true);
  for (const name of ['manifest.json', 'manifest_phone.json']) {
    const raw = await fs.readFile(path.join(publicRoot, 'models', name), 'utf8');
    const manifest = await readManifest(new Response(raw), name);
    for (const model of Object.values(manifest.models)) {
      const file = path.join(publicRoot, model.file.replace('app/public/', ''));
      assert.equal((await fs.stat(file)).size, model.bytes);
    }
  }
  assert.deepEqual(await fs.readFile(path.join(bundle, 'manifest.json')), source);
});

test('linker refuses any real destination before replacing an earlier symlink', async () => {
  const publicRoot = await fs.mkdtemp(path.join(os.tmpdir(), 'talanta-refuse-'));
  const old = await fs.mkdtemp(path.join(os.tmpdir(), 'talanta-old-'));
  await fs.symlink(old, path.join(publicRoot, 'models'), process.platform === 'win32' ? 'junction' : 'dir');
  await fs.mkdir(path.join(publicRoot, 'ground'));
  await assert.rejects(linkBundle({ bundle, publicRoot }), /Refusing to replace a real directory or file/);
  assert.equal(await fs.realpath(path.join(publicRoot, 'models')), await fs.realpath(old));
});
