import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three/webgpu';
import { createVehicleGeometry, VEHICLE_SPECS } from '../src/hero/vehicles.js';
import { buildTraffic } from '../src/hero/traffic.js';

for (const spec of VEHICLE_SPECS) test(`${spec.name} dimensions and parts`, () => {
  const geometry = createVehicleGeometry(spec), size = new THREE.Vector3();
  geometry.boundingBox.getSize(size);
  for (const [actual, expected] of [[size.x, spec.length], [size.y, spec.height], [size.z, spec.width]]) {
    assert.ok(Math.abs(actual - expected) / expected < .03, `${actual} differs from ${expected}`);
  }
  assert.equal(geometry.groups.length, 0);
  const paint = geometry.getAttribute('paintMask'), light = geometry.getAttribute('lightMask');
  assert.ok(paint && light && geometry.getAttribute('color'));
  assert.equal(paint.count, geometry.getAttribute('position').count);
  assert.equal(light.count, paint.count);
  const parts = geometry.userData.parts;
  for (const part of parts) for (let i = part.start; i < part.start + part.count; i++) {
    assert.equal(paint.getX(i), Number(part.kind === 'body' || part.kind === 'mirror'));
    assert.equal(light.getX(i), Number(part.kind === 'headlight' || part.kind === 'taillight'));
  }
  for (const [kind, count] of Object.entries({ glass: 1, tyre: 4, rim: 4, headlight: 2, taillight: 2, frontPlate: 1, rearPlate: 1, mirror: 2 })) {
    assert.ok(parts.filter((p) => p.kind === kind).length >= count, kind);
  }
  const position = geometry.getAttribute('position');
  const centers = parts.filter((p) => p.kind === 'tyre' && p.role !== 'right-hand steering').map((part) => {
    let min = Infinity, max = -Infinity;
    for (let i = part.start; i < part.start + part.count; i++) { min = Math.min(min, position.getX(i)); max = Math.max(max, position.getX(i)); }
    return (min + max) / 2;
  });
  assert.ok(Math.abs((Math.max(...centers) - Math.min(...centers)) / spec.wheelbase - 1) < .03);
  assert.ok(position.count / 3 < 3000);
  console.log(`${spec.name}: ${position.count / 3} triangles`);
});

test('traffic switches between detailed cars and box cars by camera distance', () => {
  const camera = { position: new THREE.Vector3(0, 0, 0) };
  const traffic = buildTraffic({ lines: [{ name: 'Other', points: [[0, 0, 0], [10000, 0, 0]] }], camera, count: 100, proxyDistance: 20000 });
  const detailed = traffic.group.children.filter((child) => child.name.startsWith('near-car-'));
  assert.equal(detailed.length, 5);
  assert.equal(typeof traffic.setNight, 'function');
  for (const mesh of detailed) {
    assert.equal(Array.isArray(mesh.material), false);
    assert.equal(mesh.geometry.groups.length, 0);
    assert.equal(mesh.material.userData.nightUniform.value, 0);
  }
  traffic.setNight(1);
  for (const mesh of detailed) assert.equal(mesh.material.userData.nightUniform.value, 1);
  traffic.setNight(.4);
  for (const mesh of detailed) assert.equal(mesh.material.userData.nightUniform.value, .4);
  assert.equal(typeof buildTraffic({ lines: [] }).setNight, 'function');
  const matrix = new THREE.Matrix4();
  assert.ok(detailed.some((mesh) => { for (let i = 0; i < mesh.count; i++) { mesh.getMatrixAt(i, matrix); if (matrix.elements[0] !== 0 || matrix.elements[8] !== 0) return true; } return false; }));
  camera.position.set(100000, 0, 100000); traffic.update(0);
  for (const mesh of detailed) for (let i = 0; i < mesh.count; i++) { mesh.getMatrixAt(i, matrix); assert.equal(matrix.elements[0], 0); assert.equal(matrix.elements[8], 0); }
  assert.equal(traffic.group.userData.claim, 'Visualization');
});
