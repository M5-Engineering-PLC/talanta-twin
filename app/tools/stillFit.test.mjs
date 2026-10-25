import test from 'node:test';
import assert from 'node:assert/strict';
import { PerspectiveCamera, Vector3 } from 'three/webgpu';
import { stillFit } from '../src/ui/stillFit.js';
import { STILLS } from '../src/ui/landing.js';
const near = (a, b) => assert.ok(Math.abs(a - b) < 1e-8, `${a} != ${b}`);

test('center cover fits 16:9, 21:9, 4:3 and 9:16 without distortion', () => {
  for (const [w, h] of [[1920, 1080], [2520, 1080], [1440, 1080], [1080, 1920]]) {
    const fit = stillFit(32.269, w, h);
    near(fit.rect.width / fit.rect.height, w / h);
    near(fit.rect.x + fit.rect.width / 2, 960);
    near(fit.rect.y + fit.rect.height / 2, 540);
    const expected = 2 * Math.atan(Math.tan(32.269 * Math.PI / 360) * Math.min(1, (1920 / 1080) / (w / h))) * 180 / Math.PI;
    near(fit.fov, expected); assert.equal(fit.offset, null);
  }
});
test('both measured portrait crops project source features into the same image pixels', () => {
  for (const [id, left, vfov] of [['lead06', 695, 32.269], ['lead07', 820, 29.839]]) {
    assert.equal(STILLS[id].crop.x, left);
    for (const [width, height] of [[1080, 1920], [390, 844], [768, 1024]]) {
      const fit = stillFit(vfov, width, height, STILLS[id].crop);
      if (width === 1080 && height === 1920) { near(fit.rect.x, left); near(fit.rect.width, 607); near(fit.rect.height, 1080); }
      const camera = new PerspectiveCamera(fit.fov, width / height, 0.1, 1000);
      const o = fit.offset;
      camera.setViewOffset(o.fullWidth, o.fullHeight, o.x, o.y, o.width, o.height);
      near(fit.rect.x + fit.rect.width / 2, left + 607 / 2);
      // Project three pixels from the original Cycles frame through the app matrix.
      for (const [x, y] of [[left + 100, 400], [left + 303.5, 540], [left + 500, 700]]) {
        const z = 100, halfH = z * Math.tan(vfov * Math.PI / 360);
        const point = new Vector3((x / 1920 * 2 - 1) * halfH * 1920 / 1080, (1 - y / 1080 * 2) * halfH, -z).project(camera);
        near((point.x + 1) / 2 * width, (x - fit.rect.x) / fit.rect.width * width);
        near((1 - point.y) / 2 * height, (y - fit.rect.y) / fit.rect.height * height);
      }
      camera.clearViewOffset(); assert.equal(camera.view.enabled, false);
    }
  }
});
test('invalid viewport dimensions fail explicitly', () => {
  for (const args of [[32, 0, 1080], [32, 100, -1], [NaN, 100, 100]]) assert.throws(() => stillFit(...args), RangeError);
});
