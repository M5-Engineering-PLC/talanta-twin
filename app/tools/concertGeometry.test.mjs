import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three/webgpu';
import { mergeConcertGeometry } from '../src/events/concert.js';

test('concert merge reads interleaved vertices and normalized normals from optimized models', () => {
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.InterleavedBufferAttribute(
    new THREE.InterleavedBuffer(new Int16Array([0, 32767, 0, 99, 32767, 0, 0, 99, 0, 0, 32767, 99]), 4), 3, 0, true));
  geometry.setAttribute('normal', new THREE.InterleavedBufferAttribute(
    new THREE.InterleavedBuffer(new Int8Array([0, 127, 0, 0, 0, 127, 0, 0, 0, 127, 0, 0]), 4), 3, 0, true));
  geometry.setIndex([2, 1, 0]);
  const matrix = new THREE.Matrix4().makeTranslation(10, 20, 30);
  const result = mergeConcertGeometry([{ geometry, matrix }, { geometry, matrix }]);
  assert.deepEqual([...result.attributes.position.array], [10, 21, 30, 11, 20, 30, 10, 20, 31, 10, 21, 30, 11, 20, 30, 10, 20, 31]);
  assert.deepEqual([...result.attributes.normal.array], [0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0]);
  assert.deepEqual([...result.index.array], [2, 1, 0, 5, 4, 3]);
});
