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

test('drone formations stay above the forecourt in world space and face both landing cameras', async () => {
  const { DRONE_CENTER, faceDronePoint } = await import('../src/shows/shapes.js');
  const { readFileSync } = await import('node:fs');
  const cameras = JSON.parse(readFileSync(new URL('../cameras/manifest.json', import.meta.url)));
  for (const width of [390, 1280]) {
    const count = limits(width).drones;
    for (const id of ['L06', 'L07']) {
      const pose = cameras.cameras.find(c => c.id === id);
      const camera = new THREE.PerspectiveCamera(pose.vfov_deg, 16 / 9, 0.5, 60000);
      camera.position.fromArray(pose.position); camera.lookAt(new THREE.Vector3(...pose.target)); camera.updateMatrixWorld();
      for (const shape of ['flag', 'shield', 'TALANTA']) {
        for (const point of shapePoints(shape, count)) {
          const p = faceDronePoint(point.position, camera.position);
          assert.ok(p[1] >= 60 && p[1] <= 140, `${shape} height ${p[1]}`);
          assert.ok(Math.hypot(p[0] - DRONE_CENTER[0], p[2] - DRONE_CENTER[2]) <= 61);
          const projected = new THREE.Vector3(p[0], p[1] + 6.12, p[2]).project(camera);
          assert.ok(Math.abs(projected.x) < 1 && Math.abs(projected.y) < 1 && Math.abs(projected.z) < 1, `${id} ${shape} outside view: ${projected.toArray()}`);
        }
      }
      const scene = new THREE.Scene(), bowlGroup = new THREE.Group(); bowlGroup.position.y = 6.12;
      globalThis.innerWidth = width;
      const shows = installShows({ scene, camera, bowlGroup }); shows.play('night_show'); shows.timeline.seek(25); shows.update(0); scene.updateMatrixWorld(true);
      const drones = scene.getObjectByName('SHW-03'); assert.equal(drones.visible, true);
      const matrix = new THREE.Matrix4();
      for (let i = 0; i < count; i++) {
        drones.getMatrixAt(i, matrix); const p = new THREE.Vector3().setFromMatrixPosition(matrix).applyMatrix4(drones.matrixWorld);
        assert.ok(p.y >= 66.11 && p.y <= 146.13); assert.ok(Math.hypot(p.x - DRONE_CENTER[0], p.z - DRONE_CENTER[2]) <= 61);
      }
      assert.ok(drones.instanceColor); assert.ok(scene.getObjectByName('SHW-01').instanceColor);
      const { instanceColor } = await import('three/tsl');
      assert.equal(drones.material.emissiveNode.node.aNode, instanceColor);
      assert.equal(scene.getObjectByName('SHW-01').material.emissiveNode.node.aNode, instanceColor);
      shows.dispose();
    }
  }
  delete globalThis.innerWidth;
});

test('show start holds original floodlights dark across applyTime writes and stop restores them', async () => {
  const { readFileSync } = await import('node:fs');
  const source = readFileSync(new URL('../src/main.js', import.meta.url), 'utf8');
  const section = source.slice(source.indexOf('async function startShow()'), source.indexOf("document.querySelectorAll('#modes button')"));
  const flood = [new THREE.SpotLight(0xffffff, 9000), new THREE.SpotLight(0xffffff, 4500)];
  const stubShows = { play() {}, dispose() {} };
  const body = section.replace("await import('./shows/index.js')", '({ installShows: () => stubShows })').replaceAll('import.meta.env.DEV', 'false');
  const api = new Function('flood', 'stubShows', `let shows = null; const scene = {}, camera = {}, renderer = {}, hero = null, bowl = { group: {} }, state = {}; const document = { querySelector: () => null }; function stopLiveClock() {} ${body}; return {startShow, stopShow};`)(flood, stubShows);
  await api.startShow(); flood.forEach(l => { assert.equal(l.intensity, 0); l.intensity = 9000; assert.equal(l.intensity, 0); });
  await api.startShow(); api.stopShow(); assert.deepEqual(flood.map(l => l.intensity), [9000, 4500]);
  flood[0].intensity = 123; assert.equal(flood[0].intensity, 123); api.stopShow();
});
