import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { gzipSync } from 'node:zlib';
import * as THREE from 'three/webgpu';
import { decodeCrowdAssets } from '../src/people/geometry.js';
import { installSeatedCrowd, installStandingCrowd } from '../src/people/index.js';
import { crowdTier, partitionCrowd, standingPlaces } from '../src/people/model.js';

const manifest = JSON.parse(await readFile(new URL('../public/people/crowd.json', import.meta.url)));
const binary = await readFile(new URL('../public/people/animation.bin', import.meta.url));
decodeCrowdAssets(manifest, binary.buffer.slice(binary.byteOffset, binary.byteOffset + binary.byteLength));
const value = (lod, clip, frame, vertex, axis) => THREE.DataUtils.fromHalfFloat(binary.readUInt16LE(
  ((((lod * manifest.clips.length + manifest.clips.findIndex(c => c.name === clip)) * manifest.framesPerClip + frame) * manifest.width + vertex) * 4 + axis) * 2));

test('baked assets fit their dimensions, triangle budgets, and gzip budget', async () => {
  assert.equal(binary.byteLength, manifest.width * manifest.height * 8);
  assert.equal(manifest.height, manifest.framesPerClip * manifest.clips.length * 2);
  assert.ok(manifest.lods[0].bodyTriangles >= 1500 && manifest.lods[0].triangles <= 2500);
  assert.ok(manifest.lods[1].bodyTriangles >= 60 && manifest.lods[1].triangles <= 100);
  for (const lod of manifest.lods) {
    assert.equal(lod.index.length / 3, lod.triangles);
    assert.equal(lod.position.length, lod.vertices * 3);
    assert.ok(lod.index.every(i => i >= 0 && i < lod.vertices));
    assert.ok(lod.vertices <= manifest.width);
  }
  const credits = await readFile(new URL('../public/people/CREDITS.md', import.meta.url));
  const compressed = gzipSync(JSON.stringify(manifest)).length + gzipSync(binary).length + gzipSync(credits).length;
  assert.ok(compressed < 3_000_000);
  console.log(`Software asset result: ${compressed} gzip bytes; LOD0 ${manifest.lods[0].triangles}, LOD1 ${manifest.lods[1].triangles} triangles`);
});

test('all required clip slots exist and the texture contains finite moving human positions', () => {
  const names = ['Sitting_Idle_Loop', 'Sitting_Enter', 'Sitting_Exit', 'Idle_Loop', 'Jump_Start', 'Jump_Loop', 'Jump_Land', 'Dance_Loop', 'Walk_Loop', 'clap', 'cheer', 'wave'];
  assert.deepEqual(manifest.clips.map(c => c.name), names);
  for (const clip of manifest.clips) {
    assert.ok(clip.duration > 0);
    assert.equal(clip.slot, names.indexOf(clip.name));
    for (let lod = 0; lod < 2; lod++) {
      let movement = 0;
      for (let v = 0; v < manifest.lods[lod].vertices; v++) for (let k = 0; k < 3; k++) {
        const a = value(lod, clip.name, 0, v, k), b = value(lod, clip.name, 12, v, k);
        assert.ok(Number.isFinite(a) && Number.isFinite(b));
        movement += Math.abs(a - b);
      }
      assert.ok(movement > .01, `${clip.name} LOD${lod} contains motion`);
    }
  }
  assert.throws(() => decodeCrowdAssets(manifest, new ArrayBuffer(16)), /dimensions/);
});

test('human skin, shirts, trousers, scale, and motion vary per instance', async () => {
  const scene = new THREE.Scene();
  const seats = standingPlaces({ x: -10, z: -10, width: 20, depth: 20 }, 400);
  const crowd = installSeatedCrowd({ scene, seats });
  await crowd.ready;
  for (const mesh of crowd.group.children) {
    for (const name of ['fanSkin', 'fanShirt', 'fanTrousers', 'fanScale', 'fanPhase', 'fanClap']) {
      const a = mesh.geometry.getAttribute(name);
      assert.equal(a.count, mesh.count);
      assert.ok(new Set(Array.from({ length: a.count }, (_, i) => Array.from(a.array.slice(i * a.itemSize, (i + 1) * a.itemSize)).join(','))).size > 1);
    }
    assert.ok(mesh.material.positionNode);
    assert.equal(mesh.material.userData.bakedAnimation, true);
    assert.equal(mesh.isSkinnedMesh, undefined);
  }
  crowd.dispose();
});

test('high and medium bound detailed fans; low tier and phone width use LOD1 only', async () => {
  const places = standingPlaces({ x: -5, z: -5, width: 10, depth: 10 }, 600);
  for (const [quality, limit] of [['high', 384], ['medium', 128], ['low', 0]]) {
    const crowd = installSeatedCrowd({ scene: new THREE.Scene(), seats: places, quality });
    await crowd.ready;
    assert.equal(crowd.group.children.find(m => m.userData.lod === 0)?.count ?? 0, limit);
    assert.equal(crowd.group.children.reduce((n, m) => n + m.count, 0), 600);
    assert.ok(crowd.group.children.length <= 2);
    crowd.dispose();
  }
  assert.equal(crowdTier('high', 767), 'low');
  assert.equal(crowdTier({ tier: 'low' }, 1200), 'low');
  assert.deepEqual(partitionCrowd(places, [0, 1], 'low', { x: 0, y: 0, z: 0 }), [[], [0, 1]]);
});

function inside(point, polygon) {
  let hit = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const a = polygon[i], b = polygon[j];
    if ((a[1] > point.z) !== (b[1] > point.z) && point.x < (b[0] - a[0]) * (point.z - a[1]) / (b[1] - a[1]) + a[0]) hit = !hit;
  }
  return hit;
}

test('standing figures stay inside rectangle and concave polygon in parent-local meters', async () => {
  const polygon = [[-6, -4], [6, -4], [6, 0], [0, 0], [0, 8], [-6, 8]];
  for (const area of [{ x: 11, z: -20, width: 13, depth: 9, y: 2 }, { polygon, y: 2 }]) {
    const parent = new THREE.Group(); parent.position.set(90, 10, -40); parent.rotation.y = .4;
    const crowd = installStandingCrowd({ parent, area, count: 1000, colours: { home: '#123456', away: '#abcdef' } });
    await crowd.ready;
    assert.equal(crowd.group.parent, parent);
    assert.equal(crowd.group.userData.claim, 'Visualization');
    const matrix = new THREE.Matrix4(); let count = 0;
    for (const mesh of crowd.group.children) for (let i = 0; i < mesh.count; i++) {
      mesh.getMatrixAt(i, matrix);
      const p = new THREE.Vector3().setFromMatrixPosition(matrix);
      assert.ok(Math.abs(p.y - 2.02) < .00001);
      if (area.polygon) assert.ok(inside(p, polygon));
      else assert.ok(p.x >= 11 && p.x <= 24 && p.z >= -20 && p.z <= -11);
      count++;
    }
    assert.equal(count, 1000);
    const u = crowd.group.userData.animation;
    crowd.react('wave'); crowd.update(1, 1); assert.equal(u.wave.value, 1);
    crowd.react('phones'); crowd.setNight(true); assert.equal(u.phones.value * u.night.value, 1);
    crowd.dispose();
  }
  const empty = installStandingCrowd({ parent: new THREE.Group(), area: { x: 0, z: 0, width: 1, depth: 1 }, count: 0 });
  await empty.ready; assert.equal(empty.group.children.length, 0); empty.dispose();
  assert.equal(standingPlaces({ x: 0, z: 0, width: 1, depth: 1 }, 0).length, 0);
  assert.throws(() => standingPlaces({ x: 0, z: 0, width: 0, depth: 0 }, 1), /positive area/);
});

test('hand-keyed wave returns to sitting and clap brings the hands together', () => {
  for (let lod = 0; lod < 2; lod++) {
    const body = manifest.lods[lod].kind.map((kind, i) => ({ kind, i })).filter(v => v.kind < 3);
    const top = frame => Math.max(...body.map(v => value(lod, 'wave', frame, v.i, 1)));
    assert.ok(top(12) - top(0) > .4);
    assert.ok(Math.abs(top(23) - top(0)) < .01);
    const handVertices = body.filter(v => v.kind === 1 && value(lod, 'clap', 0, v.i, 1) < 1.15);
    assert.ok(handVertices.length > 0);
    const spread = frame => {
      const xs = handVertices.map(v => value(lod, 'clap', frame, v.i, 0));
      return Math.max(...xs) - Math.min(...xs);
    };
    assert.ok(Math.abs(spread(0) - spread(3)) > .04);
  }
});
