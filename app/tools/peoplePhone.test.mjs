import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { decodeCrowdAssets, isPhoneProfile, crowdFiles, crowdAssets, figureGeometry, crowdLevelIndex } from '../src/people/geometry.js';

const dir = new URL('../public/people/', import.meta.url);
const manifest = JSON.parse(await readFile(new URL('crowd_phone.json', dir)));
const binary = await readFile(new URL('animation_phone.bin', dir));

test('phone animation file matches its JSON', () => {
  const { width, height, framesPerClip, clips, lods, lodLevels } = manifest;
  assert.equal(binary.length, lodLevels.length * clips.length * framesPerClip * width * 8);
  assert.equal(binary.length, width * height * 8);
  assert.equal(framesPerClip, 12);
  assert.deepEqual(lodLevels, [1]);
  assert.equal(lods.length, lodLevels.length);
  assert.ok(lods.every(l => l.vertices <= width));
  assert.ok(binary.length + JSON.stringify(manifest).length <= 1_000_000);
});

test('phone file decodes and exposes only LOD1', () => {
  decodeCrowdAssets(manifest, binary.buffer.slice(binary.byteOffset, binary.byteOffset + binary.byteLength));
  assert.deepEqual(crowdAssets().levels, [1]);
  assert.equal(crowdLevelIndex(1), 0);
  assert.throws(() => crowdLevelIndex(0), /not in the loaded/);
  assert.throws(() => figureGeometry(0), /not in the loaded/);
  assert.equal(figureGeometry(1).index.count, manifest.lods[0].index.length);
});

test('phone loader path is chosen for phones and the low tier', () => {
  const desktop = { userAgent: 'Mozilla/5.0 (X11; Linux x86_64) Chrome/120', width: 1440 };
  assert.equal(isPhoneProfile('high', desktop), false);
  assert.equal(isPhoneProfile('high', { ...desktop, userAgent: 'Mozilla/5.0 (Linux; Android 14; Pixel 8) Mobile' }), true);
  assert.equal(isPhoneProfile('high', { ...desktop, userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)' }), true);
  assert.equal(isPhoneProfile('high', { ...desktop, userAgent: 'Mozilla/5.0 (iPad; CPU OS 17_0)' }), true);
  assert.equal(isPhoneProfile('high', { ...desktop, width: 600 }), true);
  assert.equal(isPhoneProfile('low', desktop), true);
  assert.equal(isPhoneProfile({ tier: 'low' }, desktop), true);
  assert.equal(isPhoneProfile('medium', desktop), false);
  assert.equal(crowdFiles(true).bin, '/people/animation_phone.bin');
  assert.equal(crowdFiles(true).json, '/people/crowd_phone.json');
  assert.equal(crowdFiles(false).bin, '/people/animation.bin');
});
