import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import * as THREE from 'three/webgpu';
import { buildBowl } from '../src/world/bowl.js';
import { installSeatedCrowd } from '../src/people/index.js';
import { decodeCrowdAssets, figureGeometry } from '../src/people/geometry.js';

const crowdManifest = JSON.parse(await readFile(new URL('../public/people/crowd.json', import.meta.url)));
const crowdBinary = await readFile(new URL('../public/people/animation.bin', import.meta.url));
decodeCrowdAssets(crowdManifest, crowdBinary.buffer.slice(crowdBinary.byteOffset, crowdBinary.byteOffset + crowdBinary.byteLength));

const { features } = JSON.parse(await readFile(new URL('../public/data/manifest.json', import.meta.url)));
// Canvas drawing is irrelevant to matrix alignment. The real bowl geometry still runs.
function mockDocument() {
  const labels = [];
  const context = new Proxy({}, { get: (_, key) => key === 'createLinearGradient' ? () => ({ addColorStop() {} }) : () => {}, set: () => true });
  return { labels, createElement: () => ({ style: {}, dataset: {}, getContext: () => context, remove() {} }), body: { appendChild(label) { labels.push(label); } } };
}

test('drawn bowl seats override fallback data and align all fan origins in bowl local space', () => {
  const saved = globalThis.document; globalThis.document = mockDocument();
  const scene = new THREE.Scene(), camera = new THREE.PerspectiveCamera();
  const bowl = buildBowl(features);
  bowl.group.position.set(17, 8.5, -31); bowl.group.rotation.y = .27;
  scene.add(bowl.group);
  // A child transform catches accidental use of source-local or world coordinates.
  bowl.seats.position.set(.07, .04, -.08);
  let crowd;
  try {
    crowd = installSeatedCrowd({ scene, camera, bowlGroup: bowl.group, features,
      seats: [{ x: 900, y: 900, z: 900, facing_deg: 0 }], quality: { width: 1024 } });
    assert.equal(crowd.group.parent, bowl.group);
    const batches = crowd.group.children;
    assert.equal(batches.reduce((n, mesh) => n + mesh.count, 0), bowl.seats.count, 'Crowd must use drawn seats, not explicit or generated fallbacks');
    const cells = new Map(), matrix = new THREE.Matrix4(), local = new THREE.Matrix4();
    for (let i = 0; i < bowl.seats.count; i++) {
      bowl.seats.getMatrixAt(i, matrix); local.multiplyMatrices(bowl.seats.matrix, matrix);
      const p = new THREE.Vector3().setFromMatrixPosition(local);
      const key = [p.x, p.y, p.z].map((v) => Math.floor(v / .3)).join(',');
      if (!cells.has(key)) cells.set(key, []);
      cells.get(key).push({ p, forward: new THREE.Vector3(0, 0, 1).transformDirection(local) });
    }
    let maxDistance = 0;
    for (const figures of batches) {
    const origins = figures.geometry.getAttribute('fanOrigin');
    assert.ok(origins, 'GPU origins must be explicit so local pose changes cannot rotate seat positions');
    for (let i = 0; i < figures.count; i++) {
      figures.getMatrixAt(i, matrix);
      const p = new THREE.Vector3().setFromMatrixPosition(matrix), cell = [p.x, p.y, p.z].map((v) => Math.floor(v / .3));
      let nearest, distance = Infinity;
      for (let x = -1; x <= 1; x++) for (let y = -1; y <= 1; y++) for (let z = -1; z <= 1; z++) {
        for (const seat of cells.get([cell[0] + x, cell[1] + y, cell[2] + z].join(',')) || []) {
          const d = p.distanceTo(seat.p); if (d < distance) { distance = d; nearest = seat; }
        }
      }
      assert.ok(distance < .3, `Fan ${i} is ${distance} m from a drawn seat`);
      assert.ok(Math.abs(distance - .02) < .00001);
      assert.ok(new THREE.Vector3(0, 0, 1).transformDirection(matrix).dot(nearest.forward) > .99999);
      assert.ok(nearest.forward.dot(new THREE.Vector3(-nearest.p.x, 0, -nearest.p.z).normalize()) > .99, 'Fan faces the pitch');
      assert.ok(new THREE.Vector3().fromBufferAttribute(origins, i).distanceTo(p) < .00001);
      maxDistance = Math.max(maxDistance, distance);
    }
    }
    console.log(`${bowl.seats.count} fan origins match drawn seats; maximum offset ${maxDistance.toFixed(6)} m; unit scale and pitch-facing yaw`);
    assert.equal(globalThis.document.labels[0].style.bottom, undefined);
    assert.equal(globalThis.document.labels[0].style.top, '78px');
  } finally {
    crowd?.dispose();
    const geometries = new Set(), materials = new Set(), textures = new Set();
    bowl.group.traverse((o) => { if (o.geometry) geometries.add(o.geometry); if (o.material) materials.add(o.material); });
    for (const material of materials) { for (const value of Object.values(material)) if (value?.isTexture) textures.add(value); material.dispose(); }
    geometries.forEach((g) => g.dispose()); textures.forEach((t) => t.dispose());
    globalThis.document = saved;
  }
});

test('baked seated body fits a human scale above the tread', () => {
  const g = figureGeometry(), p = g.attributes.position, kind = g.attributes.kind;
  let top = -Infinity, bottom = Infinity, torsoBottom = Infinity;
  for (let i = 0; i < p.count; i++) if (kind.getX(i) < 3) {
    top = Math.max(top, p.getY(i)); bottom = Math.min(bottom, p.getY(i));
    if (kind.getX(i) === 0 && Math.abs(p.getX(i)) < .17) torsoBottom = Math.min(torsoBottom, p.getY(i));
  }
  assert.ok(top - bottom > 1.2 && top - bottom < 1.5);
  // bowl.js pan top = 0.45 m. Fan origin is 0.02 m above the seat origin.
  assert.ok(torsoBottom + .02 >= .45 && torsoBottom + .02 < .8);
  console.log(`Seated figure height ${(top - bottom).toFixed(3)} m; torso base ${(torsoBottom + .02).toFixed(3)} m above tread`);
  g.dispose();
});
