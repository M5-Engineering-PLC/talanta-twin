import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { seatPalette } from '../src/world/seatPalette.js';
import { buildBowl, createSeatColorPicker } from '../src/world/bowl.js';

const appDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const repoDir = path.resolve(appDir, '..');
const generator = path.join(appDir, 'tools', 'make_seat_palette.mjs');
const { features } = JSON.parse(await readFile(new URL('../public/data/manifest.json', import.meta.url)));

function mockDocument() {
  const context = new Proxy({}, {
    get: (_, key) => key === 'createLinearGradient' ? () => ({ addColorStop() {} }) : () => {},
    set: () => true,
  });
  return { createElement: () => ({ style: {}, dataset: {}, getContext: () => context, remove() {} }), body: { appendChild() {} } };
}

test('generated palette matches the ledger values', async () => {
  const csv = await readFile(path.join(repoDir, 'gis', 'parameter_ledger.csv'), 'utf8');
  const rows = new Map(csv.trimEnd().split(/\r?\n/).slice(1).map((line) => {
    const comma = line.indexOf(',');
    return [line.slice(0, comma), line.slice(comma + 1).split(',')[0]];
  }));
  const value = (name) => rows.get(`bowl.seat.${name}`);
  assert.deepEqual(seatPalette, {
    greenHex: value('green_hex'), redHex: value('red_hex'),
    mixLowerRedTop: Number(value('mix_lower_red_top')),
    mixMiddleGreen: Number(value('mix_middle_green')),
    lower: { tones: value('lower_tones').split(';'), weights: value('lower_tone_weights').split(';').map(Number) },
    middle: { tones: value('middle_tones').split(';'), weights: value('middle_tone_weights').split(';').map(Number) },
    upper: { tones: value('upper_tones').split(';'), weights: value('upper_tone_weights').split(';').map(Number) },
  });
});

test('regenerating the palette writes the same file', async () => {
  const before = await readFile(path.join(appDir, 'src/world/seatPalette.js'), 'utf8');
  const result = spawnSync(process.execPath, [generator], { cwd: appDir, encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr);
  const after = await readFile(path.join(appDir, 'src/world/seatPalette.js'), 'utf8');
  assert.equal(after, before);
});

test('seeded tone and speckle shares follow the ledger rules and repeat exactly', () => {
  for (const [tierName, rowCount] of [['lower', 24], ['middle', 13], ['upper', 21]]) {
    const sample = (seed) => {
      const pick = createSeatColorPicker(seatPalette, seed);
      const results = [];
      for (let row = 0; row < rowCount; row++) {
        const fraction = row / Math.max(rowCount - 1, 1);
        for (let seat = 0; seat < 1000; seat++) results.push(pick(tierName, fraction));
      }
      return results;
    };
    const seats = sample(303);
    assert.deepEqual(seats, sample(303));
    const tier = seatPalette[tierName];
    const toneCounts = tier.tones.map((tone) => seats.filter((seat) => seat.tone === tone).length);
    toneCounts.forEach((count, i) => assert.ok(Math.abs(count / seats.length - tier.weights[i]) <= 0.02, `${tierName} tone ${i} share was ${count / seats.length}`));
    const expectedSpeckles = Array.from({ length: rowCount }, (_, row) => {
      const f = row / Math.max(rowCount - 1, 1);
      return tierName === 'lower'
        ? seatPalette.mixLowerRedTop * Math.max(0, Math.min(1, (f - 0.6) / 0.4))
        : tierName === 'middle' ? seatPalette.mixMiddleGreen * 2 * (1 - f) : 0;
    }).reduce((sum, chance) => sum + chance, 0) / rowCount;
    const measuredSpeckles = seats.filter((seat) => seat.speckled).length / seats.length;
    assert.ok(Math.abs(measuredSpeckles - expectedSpeckles) <= 0.02, `${tierName} speckle share was ${measuredSpeckles}; expected ${expectedSpeckles}`);
  }
});

test('seat placement matrices stay identical across builds', () => {
  const savedDocument = globalThis.document;
  globalThis.document = mockDocument();
  let first, second;
  try {
    first = buildBowl(features);
    second = buildBowl(features);
    assert.deepEqual(second.seats.instanceMatrix.array, first.seats.instanceMatrix.array);
    assert.equal(first.seats.instanceMatrix.array.length % 16, 0);
  } finally {
    for (const bowl of [first, second].filter(Boolean)) {
      const geometries = new Set(), materials = new Set(), textures = new Set();
      bowl.group.traverse((object) => {
        if (object.geometry) geometries.add(object.geometry);
        if (object.material) materials.add(object.material);
      });
      for (const material of materials) {
        for (const value of Object.values(material)) if (value?.isTexture) textures.add(value);
        material.dispose();
      }
      geometries.forEach((geometry) => geometry.dispose());
      textures.forEach((texture) => texture.dispose());
    }
    globalThis.document = savedDocument;
  }
});
