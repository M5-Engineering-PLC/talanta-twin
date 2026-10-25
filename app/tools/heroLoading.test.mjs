import test from 'node:test';
import assert from 'node:assert/strict';
import { heroLoadDecision, scheduleHeroLoad } from '../src/hero/loading.js';

test('desktop defaults to bake and hero stays supported', () => {
  for (const search of ['', '?hero', '?time=17:30']) assert.deepEqual(heroLoadDecision({ search }), { load: true, reason: 'bake' });
});
test('procedural wins over hero and phone consent', () => {
  for (const search of ['?procedural', '?hero&procedural']) assert.deepEqual(heroLoadDecision({ search, requested: true }), { load: false, reason: 'procedural' });
});
test('unsupported devices and failed loads retain fallback', () => {
  assert.deepEqual(heroLoadDecision({ supported: false, search: '?hero' }), { load: false, reason: 'unsupported' });
  assert.deepEqual(heroLoadDecision({ failed: true }), { load: false, reason: 'failed' });
});
test('phones require explicit full scene request', () => {
  assert.deepEqual(heroLoadDecision({ phone: true }), { load: false, reason: 'phone' });
  assert.equal(heroLoadDecision({ phone: true, requested: true }).load, true);
  assert.equal(heroLoadDecision({ phone: true, search: '?hero' }).load, true);
});
test('tier 1 waits for first view and idle before any download', async () => {
  let paint, idle, started = false;
  const ready = new Promise((resolve) => { paint = resolve; });
  const task = scheduleHeroLoad(ready, () => { started = true; return 'bake'; }, { requestIdleCallback(callback) { idle = callback; } });
  await Promise.resolve(); assert.equal(started, false); assert.equal(idle, undefined);
  paint(); await Promise.resolve(); assert.equal(started, false);
  idle(); assert.equal(await task, 'bake'); assert.equal(started, true);
});
test('without idle callbacks a later timer starts tier 1', async () => {
  const calls = [];
  await scheduleHeroLoad(Promise.resolve(), () => calls.push('load'), { setTimeout(callback, delay) { calls.push(`timer:${delay}`); callback(); } });
  assert.deepEqual(calls, ['timer:0', 'load']);
});
