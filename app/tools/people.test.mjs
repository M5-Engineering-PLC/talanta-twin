import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { performance } from 'node:perf_hooks';
import * as THREE from 'three/webgpu';
import { generateSeats } from '../src/people/seats.js';
import { selectSeats, occupancyOrder, waveDistance } from '../src/people/model.js';
import { installSeatedCrowd } from '../src/people/index.js';
import { decodeCrowdAssets } from '../src/people/geometry.js';
import { build } from 'vite';

const crowdManifest = JSON.parse(await readFile(new URL('../public/people/crowd.json', import.meta.url)));
const crowdBinary = await readFile(new URL('../public/people/animation.bin', import.meta.url));
decodeCrowdAssets(crowdManifest, crowdBinary.buffer.slice(crowdBinary.byteOffset, crowdBinary.byteOffset + crowdBinary.byteLength));

const { features } = JSON.parse(await readFile(new URL('../public/data/manifest.json', import.meta.url)));
const seats = generateSeats(features);
const make = (configuration = {}) => {
  const scene = new THREE.Scene(), camera = new THREE.PerspectiveCamera();
  camera.position.set(0, 100, 200);
  return { scene, camera, crowd: installSeatedCrowd({ scene, camera, quality: { seats, width: 1024, ...configuration } }) };
};

test('generator is deterministic and every generated seat has one fan at full fill', () => {
  assert.deepEqual(generateSeats(features), seats);
  const { crowd } = make();
  const meshes = crowd.group.children;
  assert.equal(meshes.reduce((n, mesh) => n + mesh.count, 0), seats.length);
  const positions = new Set();
  const matrix = new THREE.Matrix4();
  for (const mesh of meshes) for (let i = 0; i < mesh.count; i++) { mesh.getMatrixAt(i, matrix); positions.add([matrix.elements[12], matrix.elements[13], matrix.elements[14]].join(',')); }
  assert.equal(positions.size, seats.length);
  console.log(`Generated ${seats.length} unique occupied seat places`);
  crowd.dispose();
});

test('no generated fan origins are closer than 0.45 m', () => {
  const grid = new Map(); let minimum = Infinity;
  for (const s of seats) {
    const cell = [s.x, s.y, s.z].map((v) => Math.floor(v / .45));
    for (let x = -1; x <= 1; x++) for (let y = -1; y <= 1; y++) for (let z = -1; z <= 1; z++) {
      for (const p of grid.get([cell[0] + x, cell[1] + y, cell[2] + z].join(',')) || []) {
        const distance = Math.hypot(s.x - p.x, s.y - p.y, s.z - p.z);
        minimum = Math.min(minimum, distance); assert.ok(distance >= .45, `Distance ${distance}`);
      }
    }
    const key = cell.join(','); if (!grid.has(key)) grid.set(key, []); grid.get(key).push(s);
  }
  console.log(`Minimum nearby origin spacing ${minimum.toFixed(6)} m`);
});

test('fill is exact after rounding, nested, clustered, and clamped', () => {
  const order = occupancyOrder(seats);
  for (const fill of [0, .01, .13, .5, .91, 1]) {
    const picked = selectSeats(seats, fill, 1024, order);
    assert.equal(picked.length, Math.round(seats.length * fill));
    assert.ok(Math.abs(picked.length / seats.length - fill) < .01);
  }
  assert.deepEqual(selectSeats(seats, .2, 1024, order), selectSeats(seats, .5, 1024, order).slice(0, Math.round(seats.length * .2)));
  const occupied = new Set(selectSeats(seats, .5, 1024, order));
  let same = 0, pairs = 0;
  for (let i = 1; i < seats.length; i++) if (seats[i].row === seats[i - 1].row && seats[i].tier === seats[i - 1].tier) { pairs++; same += Number(occupied.has(i) === occupied.has(i - 1)); }
  assert.ok(same / pairs > .8);
  assert.equal(selectSeats(seats, 2, 1024, order).length, seats.length);
  assert.equal(selectSeats(seats, -1, 1024, order).length, 0);
});

test('wave travels at the selected speed and wraps around the circumference', () => {
  const { crowd } = make();
  crowd.update(0, 10); crowd.react('wave', { speed: 12 }); crowd.update(2, 12);
  const u = crowd.group.userData.animation;
  assert.equal(u.speed.value, 12); assert.equal(u.wave.value, 1);
  assert.equal(waveDistance(u.time.value - u.start.value, u.speed.value, u.perimeter.value), 24);
  const attribute = crowd.group.children[0].geometry.attributes.fanAngle;
  assert.ok(attribute.array.every((v) => v >= 0 && v <= Math.PI * 2));
  assert.ok(Math.abs(waveDistance(u.perimeter.value / 12 + 1, 12, u.perimeter.value) - 12) < 1e-8);
  crowd.react('wave', { speed: 7 }); assert.equal(u.speed.value, 7);
  crowd.dispose();
});

test('phones use only LOD1, cap the drawn fans, and preserve full occupancy on desktop', () => {
  const { crowd } = make({ width: 767 });
  assert.equal(crowd.group.children.length, 1);
  assert.equal(crowd.group.children[0].name, 'crowd-lod1');
  assert.equal(crowd.group.children[0].count, 15000);
  crowd.setFill(.1); assert.equal(crowd.group.children[0].count, Math.round(seats.length * .1));
  crowd.dispose();
  assert.equal(selectSeats(seats, 1, 768).length, seats.length);
});

test('reactions, palettes, LOD selection, label, and disposal work through the public API', () => {
  const labels = [];
  globalThis.document = { createElement: () => ({ style: {}, dataset: {}, remove() { this.removed = true; } }), body: { appendChild(label) { labels.push(label); } } };
  try {
    const { crowd, camera, scene } = make();
    const u = crowd.group.userData.animation;
    assert.equal(labels[0].textContent, 'Visualization');
    crowd.react('cheer'); assert.equal(u.cheer.value, 1);
    crowd.react('goal', { end: 'away' }); assert.equal(u.goal.value, 1); assert.equal(u.end.value, -1);
    crowd.react('scarves'); assert.equal(u.scarves.value, 1);
    crowd.react('phones'); crowd.setNight(true); assert.equal(u.phones.value * u.night.value, 1);
    crowd.setNight(false); assert.equal(u.phones.value * u.night.value, 0);
    crowd.setPalette('#0000ff', '#ff0000');
    assert.ok(crowd.group.children[0].geometry.attributes.fanShirt.array.some((v) => v === 1));
    camera.position.set(0, 0, 600); crowd.update(1, 1);
    assert.equal(crowd.group.children.filter((m) => m.visible).length, 1);
    assert.equal(crowd.group.children.find((m) => m.visible).name, 'crowd-lod1');
    camera.position.set(0, 100, 200); crowd.update(1, 2);
    assert.ok(crowd.group.children.every(m => m.userData.lod === 1), 'No detailed fans beyond the near range');
    camera.position.set(seats[0].x, seats[0].y + 3, seats[0].z); crowd.update(1, 2.5);
    assert.ok(crowd.group.children.some(m => m.name === 'crowd-figures'));
    crowd.setFill(0); assert.equal(labels[0].hidden, true);
    crowd.setFill(1); scene.visible = false; crowd.update(1, 3); assert.equal(labels[0].hidden, true);
    crowd.dispose(); crowd.dispose(); assert.equal(labels[0].removed, true); assert.equal(scene.children.length, 0);
  } finally { delete globalThis.document; }
});

test('crowd module bundles with its TSL imports', async () => {
  const result = await build({ configFile: false, logLevel: 'error', build: { write: false, minify: false,
    lib: { entry: new URL('../src/people/index.js', import.meta.url).pathname, formats: ['es'], fileName: 'people' } } });
  const output = Array.isArray(result) ? result[0].output : result.output;
  assert.ok(output.some((o) => o.type === 'chunk' && o.code.includes('installSeatedCrowd')));
});

test('report geometry budgets and CPU update timing for 60000 fans', () => {
  const sample = Array.from({ length: 60000 }, (_, i) => ({ ...seats[i % seats.length] }));
  const { crowd, camera } = make({ seats: sample });
  camera.position.set(sample[0].x, sample[0].y + 3, sample[0].z); crowd.update(0, 0);
  assert.equal(crowd.group.children.length, 2);
  let triangleTotal = 0;
  for (const mesh of crowd.group.children) {
    const triangles = (mesh.geometry.index?.count ?? mesh.geometry.attributes.position.count) / 3;
    triangleTotal += triangles * mesh.count;
    console.log(`${mesh.name}: 1 draw call, ${triangles} triangles/fan, ${triangles * mesh.count} triangles at ${mesh.count} fans`);
  }
  assert.ok(triangleTotal < 6_000_000, 'Detailed plus distant fans retain the previous near-view triangle cost');
  console.log(`Software high-tier total: ${triangleTotal} triangles in 2 draw calls`);
  crowd.react('wave');
  for (let i = 0; i < 100; i++) crowd.update(1 / 60, i / 60);
  const start = performance.now();
  for (let i = 0; i < 10000; i++) crowd.update(1 / 60, i / 60);
  console.log(`60000 fans: ${((performance.now() - start) / 10000).toFixed(6)} ms/update, Node ${process.version}; CPU only, no GPU rendering`);
  crowd.dispose();
});
