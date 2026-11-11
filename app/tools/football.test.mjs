import test from 'node:test';
import assert from 'node:assert/strict';
import { footballGeometry } from '../src/events/football.js';

test('match ball has regulation scale and the two classic panel colors', () => {
  const geometry = footballGeometry();
  geometry.computeBoundingSphere();
  const circumference = geometry.boundingSphere.radius * 2 * Math.PI;
  assert.ok(circumference >= .68 && circumference <= .70);
  const colors = geometry.getAttribute('color'), counts = new Map();
  for (let i = 0; i < colors.count; i += 3) {
    const shade = colors.getX(i);
    counts.set(shade, (counts.get(shade) ?? 0) + 1);
  }
  assert.deepEqual([...counts.values()].sort((a, b) => a - b), [12 * 5, 20 * 6]);
  geometry.dispose();
});
