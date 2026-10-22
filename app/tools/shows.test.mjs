import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three/webgpu';
import { Timeline } from '../src/shows/timeline.js';
import { fallbackFacadeLines, validFacadeLines } from '../src/shows/geometry.js';
import { flagBand, limits, shapePoints, droneFrame } from '../src/shows/shapes.js';
import { installShows } from '../src/shows/index.js';

test('timeline orders cues and preserves overlaps with latest cue last', () => {
  const t = new Timeline([{ start: 3, duration: 4, module: 'a' }, { start: 0, duration: 8, module: 'a' }]);
  assert.deepEqual(t.seek(4).map(c => c.start), [0, 3]); assert.equal(t.seek(7).length, 1);
});
test('seek is deterministic across play, pause and loop', () => {
  const t = new Timeline(); const expected = t.seek(20); t.play(); t.update(7); t.pause(); t.update(8);
  assert.equal(t.time, 27); assert.deepEqual(t.seek(20), expected);
  t.loop = true; t.seek(59); t.play(); t.update(3); assert.equal(t.time, 2);
  t.loop = false; t.seek(59); t.update(3); assert.equal(t.time, 60); assert.equal(t.playing, false);
});
test('flag bands follow normalized rib angles', () => {
  assert.deepEqual([0.1, 0.32, 0.5, 0.67, 0.85].map(f => flagBand(f * Math.PI * 2)), ['black', 'white', 'red', 'white', 'green']);
  assert.equal(flagBand(-Math.PI / 2), 'green');
});
test('point counts, landings and phone limits', () => {
  for (const count of [200, 300, 480, 600]) for (const shape of ['flag', 'shield', 'TALANTA']) {
    const points = shapePoints(shape, count); assert.equal(points.length, count); assert.ok(points.every(p => p.position.every(Number.isFinite)));
  }
  assert.deepEqual(droneFrame(0, 200).map(p => p.position), droneFrame(32, 200).map(p => p.position));
  assert.deepEqual(droneFrame(17, 200), droneFrame(17, 200));
  assert.deepEqual(limits(767), { drones: 200, lights: 2 }); assert.equal(limits(768).drones, 480);
});
test('fallback V bays and merged facade geometry', () => {
  const g = fallbackFacadeLines(); assert.equal(g.ribs.length, 48); assert.ok(validFacadeLines(g));
  for (const rib of g.ribs) { const p = rib.at(-1); assert.ok(g.ribs.some(other => Math.abs(Math.atan2(other[0][2], other[0][0]) - Math.atan2(p[2], p[0])) < 1e-6)); }
});
test('software scene lifecycle and geometry budget report', () => {
  for (const width of [390, 1280]) {
    globalThis.innerWidth = width;
    const scene = new THREE.Scene(), shows = installShows({ scene });
    shows.play('night_show'); shows.timeline.seek(20); shows.update(0);
    const root = scene.children[0], report = {};
    root.traverse(o => { if (!o.isMesh) return; const name = o.name || (o.count === limits(width).drones ? 'SHW-03' : 'SHW-01'); report[name] = { drawCalls: 1, triangles: (o.geometry.index?.count ?? o.geometry.attributes.position.count) / 3 * (o.count ?? 1) }; });
    assert.equal(root.children.filter(o => o.isLight).length, limits(width).lights);
    assert.equal(report['SHW-02'].drawCalls, 1); assert.equal(report['SHW-03'].triangles, limits(width).drones * 8);
    console.log(`SOFTWARE width=${width} ${JSON.stringify(report)}`);
    shows.setEnabled('SHW-01', false); assert.ok(root.children.filter(o => o.isLight).every(l => l.intensity === 0));
    shows.dispose(); shows.dispose(); assert.equal(scene.children.length, 0);
  }
  delete globalThis.innerWidth;
});
