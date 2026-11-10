import test from 'node:test';
import assert from 'node:assert/strict';
import { createViewStills } from '../src/ui/landing.js';

function setup(t, { reduced = false, allowed = true, decode = () => Promise.resolve() } = {}) {
  const saved = Object.fromEntries(['document', 'window', 'matchMedia'].map((key) => [key, Object.getOwnPropertyDescriptor(globalThis, key)]));
  const classes = new Set(), events = new Map();
  const image = { src: '', style: {}, hidden: true, decode };
  const claim = { textContent: '' };
  const classList = { add: (...names) => names.forEach((name) => classes.add(name)),
    remove: (...names) => names.forEach((name) => classes.delete(name)), contains: (name) => classes.has(name) };
  Object.assign(globalThis, {
    document: { getElementById: (id) => id === 'landing-still' ? image : claim, body: { classList } },
    window: { addEventListener: (type, callback, options) => { assert.equal(options.capture, true); events.set(type, callback); } },
    matchMedia: () => ({ matches: reduced }),
  });
  t.after(() => {
    for (const [key, descriptor] of Object.entries(saved)) {
      if (descriptor) Object.defineProperty(globalThis, key, descriptor); else delete globalThis[key];
    }
  });
  const times = [], projections = []; let releases = 0;
  const controller = createViewStills({ onTime: (...args) => times.push(args), onProjection: (id) => projections.push(id),
    onRelease: () => releases++, allowed: () => allowed });
  return { controller, classes, image, claim, times, projections, events, releases: () => releases };
}

test('P4 shows only after arrival, snaps time, fades in for 0.6s and releases after 0.3s', async (t) => {
  t.mock.timers.enable({ apis: ['setTimeout'] });
  const f = setup(t); f.controller.select('lead06');
  assert.deepEqual(f.times, []); assert.equal(f.classes.has('cycles-still'), false);
  f.controller.arrive(); await Promise.resolve();
  assert.deepEqual(f.times, [[1085, 'lead06']]); assert.deepEqual(f.projections, ['lead06']);
  assert.equal(f.image.style.transitionDuration, '0.6s'); assert.equal(f.classes.has('cycles-still'), true);
  assert.match(f.claim.textContent, /people, vehicles and lighting are illustrative/);
  const releases = f.releases();
  f.events.get('pointerdown')(); f.events.get('touchstart')();
  assert.equal(f.image.style.transitionDuration, '0.3s');
  assert.equal(f.classes.has('cycles-still'), false); assert.equal(f.classes.has('cycles-still-claim'), true);
  t.mock.timers.tick(299); assert.equal(f.releases(), releases);
  t.mock.timers.tick(1); assert.equal(f.releases(), releases + 1);
  assert.equal(f.claim.textContent, 'Visualization'); assert.equal(f.classes.has('cycles-still-claim'), false);
});
test('first wheel/key input cancels a pending decode without reviving the still', async (t) => {
  let resolve; const f = setup(t, { decode: () => new Promise((r) => { resolve = r; }) });
  f.controller.select('lead07'); f.controller.arrive(); assert.deepEqual(f.times, [[630, 'lead07']]);
  f.events.get('wheel')(); f.events.get('keydown')(); resolve(); await Promise.resolve();
  assert.equal(f.classes.has('cycles-still'), false); assert.equal(f.controller.selected, null);
});
test('reduced motion shows and dismisses without a fade', async (t) => {
  const f = setup(t, { reduced: true }); f.controller.select('lead07'); f.controller.arrive(); await Promise.resolve();
  assert.equal(f.classes.has('cycles-still'), true); assert.equal(f.image.style.transitionDuration, '0s');
  const releases = f.releases(); f.events.get('keydown')();
  assert.equal(f.image.style.transitionDuration, '0s'); assert.equal(f.releases(), releases + 1);
});
test('tour/parity/event guard prevents the still and the time snap', async (t) => {
  const f = setup(t, { allowed: false }); f.controller.select('lead06'); f.controller.arrive(); await Promise.resolve();
  assert.deepEqual(f.times, []); assert.equal(f.classes.has('cycles-still'), false);
});
