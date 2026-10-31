// Software tests. Vite returns index.html with HTTP 200 for a missing asset.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { dropInvalidCompressedMaps, readManifest } from '../src/hero/manifest.js';

test('manifest parsing rejects HTML even with status 200 or a misleading JSON content type', async () => {
  for (const headers of [{ 'content-type': 'text/html' }, { 'content-type': 'application/json' }, {}]) {
    await assert.rejects(readManifest(new Response(' <!doctype html><html>Vite</html>', { headers }), './models/manifest_phone.json'), /expected a JSON manifest, received HTML.*link_bundle/);
  }
  await assert.rejects(readManifest(new Response('bad json'), 'manifest.json'), /invalid JSON/);
  await assert.rejects(readManifest(new Response('{}'), 'manifest.json'), /models/);
});

test('desktop and phone release manifests resolve the linked models and time sets', async () => {
  for (const name of ['manifest.json', 'manifest_phone.json']) {
    const source = await readFile(new URL(`../../assets/web_hero_v3/${name}`, import.meta.url), 'utf8');
    const manifest = await readManifest(new Response(source), name);
    assert.equal(manifest.bundle, 'web_hero_v3');
    assert.equal(manifest.look.look, JSON.parse(source).look.look);
    assert.deepEqual(manifest.tod.times, ['0730', '1030', '1805', '2000']);
    for (const model of Object.values(manifest.models)) {
      const file = model.file.replace('app/public/models/', '');
      assert.ok(file.startsWith(name.includes('phone') ? 'models_phone/' : 'models/'));
      await readFile(new URL(`../../assets/web_hero_v3/${file}`, import.meta.url));
    }
    assert.equal(manifest.ground.index, 'app/public/ground/tiles.json');
  }
});

test('compressed maps below one block are dropped and valid maps stay', () => {
  const tiny = { isCompressedTexture: true, image: { width: 1, height: 1 } }, good = { isCompressedTexture: true, image: { width: 512, height: 1024 } };
  const plain = { image: { width: 1, height: 1 } }, material = { name: 'shield_paint', map: tiny, lightMap: good, aoMap: plain };
  const warn = console.warn; console.warn = () => {};
  try { assert.deepEqual(dropInvalidCompressedMaps(material), ['map']); } finally { console.warn = warn; }
  assert.equal(material.map, null); assert.equal(material.lightMap, good); assert.equal(material.aoMap, plain);
});
