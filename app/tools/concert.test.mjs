import { fileURLToPath } from 'node:url';
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { join, relative } from 'node:path';
import { execFileSync } from 'node:child_process';
import * as THREE from 'three/webgpu';
import { addConcertBackline } from '../src/events/concert-backline.js';
import { addConcertBarricades } from '../src/events/concert-barricades.js';
import { addConcertDecking, PITCH_DECKING } from '../src/events/concert-decking.js';
import { addConcertCableRoute, addConcertFoh } from '../src/events/concert-foh.js';
import { concert_cues } from '../src/events/cues.js';
import { concertState, concertBudget, concertCost, floorZones, AISLE, CATWALK, BSTAGE, PITCH_HALF, FOH, FOH_CABLE, BARRICADES, PART_COST } from '../src/events/concert-state.js';
import { standingPlaces } from '../src/people/model.js';

const dir = fileURLToPath(new URL('../public/concert/', import.meta.url));
const files = d => readdirSync(d).flatMap(n => statSync(join(d, n)).isDirectory() ? files(join(d, n)) : [join(d, n)]);

test('concertState is deterministic, JSON-safe and leaves the cues unchanged', () => {
  const before = JSON.stringify(concert_cues);
  for (const tier of ['high', 'medium', 'low']) for (let t = 0; t < 130; t += 1.7) {
    const budget = concertBudget(tier, 1280), a = concertState(concert_cues, t, budget);
    assert.deepEqual(JSON.parse(JSON.stringify(a)), a);
    assert.deepEqual(concertState(concert_cues, t, budget), a);
    assert.deepEqual(concertState(concert_cues, t + 60, budget).stage, a.stage);
  }
  assert.equal(JSON.stringify(concert_cues), before);
});

test('the new parts exist in the state and keep the stage end', () => {
  const s = concertState(concert_cues, 30, concertBudget('high', 1280));
  assert.equal(s.stage.position[2], 46); assert.equal(s.stage.heading, Math.PI); assert.equal(s.stage.size[0], 60);
  assert.deepEqual(s.backdrop.size.slice(0, 2), [60, 14]);
  assert.equal(s.wings.length, 2); assert.ok(s.wings.every(w => w.radius > 0 && w.arc > 0));
  assert.equal(s.flown.length, 48); assert.equal(s.bars.length, 24); assert.equal(s.speakers.length, 24);
  assert.ok(s.catwalk && s.bstage && s.truss && s.performer && s.floor);
  assert.equal(s.performer.kind, 'generic');
  assert.equal(s.performer.position[1], CATWALK.top);
  assert.ok(s.performer.position[2] > CATWALK.toZ && s.performer.position[2] < CATWALK.fromZ);
  assert.equal(BSTAGE.height, CATWALK.top);
  assert.ok(s.lights.every(l => l.target[2] < l.position[2] && l.intensity > 0));
  assert.deepEqual(s.screens.map(x => x.id), ['backdrop', 'wing-left', 'wing-right']);
  // Labels: the score line reads the phase and the clock.
  assert.equal(s.phase, 'drop'); assert.equal(s.duration, 60);
});

test('LED content follows the cues and the beat, with no text or image data', () => {
  assert.deepEqual(concert_cues.map(c => c.params.pattern), [0, 1, 2, 3, 4]);
  assert.equal(concertState(concert_cues, 25).led.pattern, 2);
  assert.equal(concertState(concert_cues, 11).led.pattern, 1);
  const source = ['concert.js', 'concert-led.js', 'concert-state.js', 'cues.js'].map(f => readFileSync(new URL(`../src/events/${f}`, import.meta.url), 'utf8')).join('\n');
  assert.ok(!/TextureLoader|CanvasTexture|fillText|\.png|\.jpe?g/i.test(source));
});

test('the floor crowd stays on the pitch, in front of the stage, and keeps the catwalk aisle clear', () => {
  for (const tier of ['high', 'medium', 'low']) for (const width of [390, 1280]) {
    const budget = concertBudget(tier, width), zones = floorZones(budget.crowd);
    assert.equal(zones.reduce((n, z) => n + z.count, 0), budget.crowd);
    let places = 0;
    for (const zone of zones) {
      for (const p of standingPlaces({ polygon: zone.polygon }, zone.count)) {
        places++;
        assert.ok(Math.abs(p.x) <= PITCH_HALF.x && Math.abs(p.z) <= PITCH_HALF.z, `${zone.id} off the pitch`);
        assert.ok(p.z < 40.5, 'in front of the stage deck');
        for (let i = 1; i < FOH_CABLE.length; i++) {
          const [x1, z1] = FOH_CABLE[i - 1], [x2, z2] = FOH_CABLE[i];
          const dx = Math.max(Math.min(x1, x2) - p.x, p.x - Math.max(x1, x2), 0);
          const dz = Math.max(Math.min(z1, z2) - p.z, p.z - Math.max(z1, z2), 0);
          assert.ok(Math.hypot(dx, dz) > .7, 'cable protector kept clear');
        }
        for (const [[x1, z1], [x2, z2]] of BARRICADES) {
          const dx = Math.max(Math.min(x1, x2) - p.x, p.x - Math.max(x1, x2), 0);
          const dz = Math.max(Math.min(z1, z2) - p.z, p.z - Math.max(z1, z2), 0);
          assert.ok(Math.hypot(dx, dz) >= .7, 'barricade kept clear');
        }
        assert.ok(!(Math.abs(p.x) < FOH.width / 2 + FOH.clearance && p.z < FOH.z + FOH.depth / 2 + FOH.clearance), 'FOH and rear access kept clear');
        assert.ok(!(Math.abs(p.x) < AISLE.halfWidth && p.z > AISLE.toZ), `${zone.id} in the catwalk aisle`);
        assert.ok(!(Math.abs(p.x) < AISLE.bstageHalfWidth && p.z > AISLE.toZ && p.z < AISLE.bstageFromZ + 2), `${zone.id} around the B-stage`);
        assert.ok(!(Math.abs(p.x) < CATWALK.halfWidth + 1 && p.z > BSTAGE.centreZ - BSTAGE.depth / 2 && p.z < CATWALK.fromZ + 5), 'on the catwalk');
      }
    }
    assert.equal(places, budget.crowd);
  }
});

test('the floor crowd is denser near the stage', () => {
  const zones = floorZones(5000), density = id => zones.find(z => z.id === id).density;
  assert.ok(density('front-left') > density('middle') && density('middle') > density('back'));
  assert.ok(density('front-right') > density('middle'));
});

test('budget counts per tier and width', () => {
  for (const [tier, count, heads] of [['high', 5000, 16], ['medium', 2000, 12], ['low', 700, 8]]) {
    for (const width of [390, 767, 768, 1280]) {
      const b = concertBudget(tier, width), phone = width < 768;
      assert.equal(b.crowd, phone ? count / 2 : count); assert.equal(b.heads, phone ? 8 : heads);
      assert.equal(concertState(concert_cues, 25, b).floor.count, b.crowd);
    }
  }
  assert.equal(concertBudget('unknown', 1280).crowd, 700);
  assert.deepEqual(concertBudget('ultra', 1280), concertBudget('high', 1280));
});

test('the front-of-house booth meets its pitch footprint and geometry budget', () => {
  const parent = new THREE.Group();
  const booth = addConcertFoh(parent);
  const bounds = new THREE.Box3().setFromObject(booth);
  assert.deepEqual(bounds.getSize(new THREE.Vector3()).toArray().map(n => Number(n.toFixed(3))), [6, 3.2, 4]);
  assert.equal(bounds.getCenter(new THREE.Vector3()).z, FOH.z);
  const route = addConcertCableRoute(parent);
  const meshes = [...booth.children, ...route.children];
  assert.equal(meshes.length, PART_COST.foh.draws);
  assert.equal(meshes.reduce((sum, mesh) => sum + mesh.count * mesh.geometry.index.count / 3, 0), PART_COST.foh.triangles);
  const routeBounds = new THREE.Box3().setFromObject(route);
  assert.ok(routeBounds.max.x < PITCH_HALF.x);
  assert.ok(routeBounds.min.z > -PITCH_HALF.z);
  const decking = addConcertDecking(parent);
  const deckBounds = new THREE.Box3().setFromObject(decking);
  assert.deepEqual(deckBounds.getSize(new THREE.Vector3()).toArray().map(n => Math.round(n)), [80, 0, 90]);
  assert.ok(Math.abs(deckBounds.max.y - PITCH_DECKING.top) < .001);
  assert.ok(Math.abs(routeBounds.min.y - PITCH_DECKING.top) < .001);
  assert.ok(routeBounds.min.x >= deckBounds.min.x && routeBounds.max.x <= deckBounds.max.x);
  assert.ok(routeBounds.min.z >= deckBounds.min.z && routeBounds.max.z <= deckBounds.max.z);
  const barricades = addConcertBarricades(parent);
  const barricadeBounds = new THREE.Box3().setFromObject(barricades);
  assert.ok(Math.abs(barricadeBounds.min.y - PITCH_DECKING.top) < .001);
  assert.ok(Math.abs(barricadeBounds.max.y - PITCH_DECKING.top - 1.2) < .001);
  assert.equal(barricades.children.length, PART_COST.barricades.draws);
  assert.equal(barricades.children.reduce((sum, mesh) => sum + mesh.count * mesh.geometry.index.count / 3, 0), PART_COST.barricades.triangles);
});

test('stage backline geometry stays inside its draw and triangle budget', () => {
  const { group: props, draw } = addConcertBackline(new THREE.Group());
  assert.equal(props.children.length, PART_COST.backline.draws);
  const triangles = props.children.reduce((sum, mesh) => sum + mesh.count * mesh.geometry.index.count / 3, 0);
  assert.equal(triangles, PART_COST.backline.triangles);
  assert.ok(triangles < 35000);
  const { instanceMatrix, instanceColor } = props.getObjectByName('console-indicators');
  draw(concertState(concert_cues, 25));
  const matrixAtDrop = instanceMatrix.array.slice();
  const colorAtDrop = instanceColor.array.slice();
  draw(concertState(concert_cues, 44.5));
  assert.notDeepEqual(instanceMatrix.array, matrixAtDrop, 'waveform scrolls with the cue');
  assert.notDeepEqual(instanceColor.array, colorAtDrop, 'mixer meters respond to the cue');
});

test('laser visuals are synchronized with the drop and chorus', () => {
  for (const second of [0, 12, 54]) assert.equal(concertState(concert_cues, second).lasers.length, 0);
  for (const second of [24, 36]) {
    const lasers = concertState(concert_cues, second).lasers;
    assert.equal(lasers.length, 8);
    assert.ok(lasers.every(ray => ray.target[1] > ray.position[1] && ray.intensity > 0));
    assert.notDeepEqual(lasers, concertState(concert_cues, second + .4).lasers);
  }
});

test('draw call and triangle estimate stays inside the budget', () => {
  const high = concertCost(concertBudget('high', 1280)), medium = concertCost(concertBudget('medium', 1280)), low = concertCost(concertBudget('low', 390));
  assert.ok(high.draws <= 60, `draws ${high.draws}`);
  assert.ok(high.triangles > medium.triangles && medium.triangles > low.triangles);
  assert.ok(high.triangles < 1_000_000);
});

test('every file in public/concert has an entry in CREDITS.md and the size budget holds', () => {
  const credits = readFileSync(join(dir, 'CREDITS.md'), 'utf8'), all = files(dir);
  let total = 0;
  for (const file of all) {
    const name = relative(dir, file).split('\\').join('/'); total += statSync(file).size;
    if (name !== 'CREDITS.md') assert.ok(credits.includes(name), `${name} is missing from CREDITS.md`);
    assert.ok(!/speaker|sofi/i.test(name), `${name} must not be in the repository`);
  }
  assert.ok(all.length > 5);
  assert.ok(total <= 6 * 1024 * 1024, `concert download ${total} bytes`);
  for (const must of ['mertart3D', 'JanoschR', 'Pitrako', 'Maxime GUINARD', 'iPoly3D']) assert.ok(credits.includes(must), must);
  assert.ok(credits.includes('by mertart3D (https://sketchfab.com/mertbbicak) licensed under CC-BY-4.0'));
  assert.ok(!credits.includes('by gluttonia'));
  for (const f of ['simple-concert-stage', 'truss-structure', 'led-25-x-4', 'stage-lights', 'ipoly3d-concert-stage']) assert.ok(existsSync(join(dir, f, 'model.glb')));
  const main = readFileSync(new URL('../src/main.js', import.meta.url), 'utf8');
  for (const author of ['mertart3D', 'JanoschR', 'Pitrako', 'Maxime GUINARD', 'iPoly3D']) assert.ok(main.includes(author), `${author} missing from the in-app credits`);
});

test('no speaker model file or sofi frame is tracked or staged in the repository', () => {
  const list = execFileSync('git', ['ls-files', '--cached', '--others', '--exclude-standard', '--', dir], { encoding: 'utf8' });
  assert.ok(!/speaker|sofi/i.test(list), list);
  assert.ok(!/stage-speaker|small_speaker/i.test(readFileSync(new URL('../src/events/concert.js', import.meta.url), 'utf8')));
});
