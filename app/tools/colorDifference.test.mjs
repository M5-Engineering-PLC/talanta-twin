import test from 'node:test';
import assert from 'node:assert/strict';
import { rgbToLab, ciede2000, meanColorDifference } from './colorDifference.mjs';

test('CIEDE2000 matches Sharma reference pairs, including neutral and hue wrapping', () => {
  const pairs = [
    [[50, 2.6772, -79.7751], [50, 0, -82.7485], 2.0425],
    [[50, 3.1571, -77.2803], [50, 0, -82.7485], 2.8615],
    [[50, 2.8361, -74.02], [50, 0, -82.7485], 3.4412],
    [[50, -1.3802, -84.2814], [50, 0, -82.7485], 1],
    [[50, 0, 0], [50, -1, 2], 2.3669],
    [[50, 2.49, -0.001], [50, -2.49, 0.001], 7.1792],
    [[50, -0.001, 2.49], [50, 0.001, -2.49], 4.8045],
    [[50, 2.5, 0], [50, 0, -2.5], 4.3065],
    [[50, 2.5, 0], [73, 25, -18], 27.1492],
    [[60.2574, -34.0099, 36.2677], [60.4626, -34.1751, 39.4387], 1.2644],
  ];
  for (const [a, b, expected] of pairs) {
    assert.ok(Math.abs(ciede2000(a, b) - expected) < 0.0001, `${a}: ${ciede2000(a, b)} != ${expected}`);
    assert.ok(Math.abs(ciede2000(b, a) - expected) < 0.0001);
    assert.equal(ciede2000(a, a), 0);
  }
});
test('sRGB uses D65 white, black and the sRGB transfer function', () => {
  assert.deepEqual(rgbToLab(0, 0, 0), [0, 0, 0]);
  const [l, a, b] = rgbToLab(255, 255, 255);
  assert.ok(Math.abs(l - 100) < 0.0001 && Math.abs(a) < 0.0001 && Math.abs(b) < 0.0001);
  assert.ok(Math.abs(rgbToLab(255, 0, 0)[0] - 53.2408) < 0.0001);
});
test('full frame averages every pixel; rectangles exclude pixels outside their bounds', () => {
  const black = new Uint8Array([0, 0, 0, 255, 0, 0, 0, 255]);
  const mixed = new Uint8Array([255, 255, 255, 255, 0, 0, 0, 255]);
  assert.equal(meanColorDifference(black, black, 2, 1).mean, 0);
  assert.equal(meanColorDifference(black, mixed, 2, 1, [0.5, 0, 1, 1]).mean, 0);
  const left = meanColorDifference(black, mixed, 2, 1, [0, 0, 0.5, 1]);
  assert.ok(Math.abs(left.mean - 100) < 0.0001);
  assert.equal(meanColorDifference(black, mixed, 2, 1).mean, left.mean / 2);
  assert.throws(() => meanColorDifference(black, mixed, 4, 1), /dimensions/);
  assert.throws(() => meanColorDifference(black, mixed, 2, 1, [1, 0, 0, 1]), /rectangle/);
});
