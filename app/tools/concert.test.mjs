import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { join, relative } from 'node:path';
import { execFileSync } from 'node:child_process';
import { concert_cues } from '../src/events/cues.js';
import { concertState, concertBudget, concertCost, floorZones, AISLE, CATWALK, BSTAGE, PITCH_HALF } from '../src/events/concert-state.js';
import { standingPlaces } from '../src/people/model.js';

const dir = new URL('../public/concert/', import.meta.url).pathname;
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
    const name = relative(dir, file); total += statSync(file).size;
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
