// First-load budget (demo milestone task 2). Software tests only: no GPU output is asserted here.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { lightSetAt, SEQUENCE_LIGHT_SETS, createSequencePlayer } from '../src/hero/sequence.js';
import { loadHero } from '../src/hero/loadHero.js';
import { prepareSequenceLight } from '../src/hero/sequenceLight.js';

test('the sequence uses its light sets in order, the start frame needs only 1805', () => {
  assert.equal(lightSetAt(0), '1805');
  assert.equal(lightSetAt(30.9), '1805');
  assert.equal(lightSetAt(31), '2000');
  assert.equal(lightSetAt(90), '2000');
  assert.deepEqual([...SEQUENCE_LIGHT_SETS], ['1805', '2000']);
});

test('prepare learns the requested start time, also after a seek during loading', async () => {
  const seen = [];
  let release;
  const player = createSequencePlayer({ input: null, sample: (t) => ({ time: t }),
    prepare: async (current, startTime) => { seen.push(startTime()); await new Promise((r) => { release = r; }); seen.push(startTime()); } });
  const pending = player.start(0);
  await Promise.resolve();
  player.seek(50);
  release(); await pending;
  assert.deepEqual(seen, [0, 50]);
  assert.equal(lightSetAt(seen[1]), '2000');
});

test('applies the latest seek before starting and defers other sets until after paint', async () => {
  const calls = [], frames = [], idle = []; let seek = 0, release;
  const tod = { async setTime(t) { calls.push(`set:${t}`); if (t === '1805') await new Promise(r => { release = r; }); return true; },
    async preload(t) { calls.push(`preload:${t}`); } };
  const host = { requestAnimationFrame: fn => frames.push(fn), requestIdleCallback: fn => idle.push(fn) };
  const pending = prepareSequenceLight(tod, () => seek, () => true, host);
  await Promise.resolve(); seek = 50; release(); await pending;
  assert.deepEqual(calls, ['set:1805', 'set:2000']);
  frames.shift()(); assert.equal(idle.length, 0); frames.shift()(); assert.equal(idle.length, 1);
  await idle.shift()(); assert.deepEqual(calls, ['set:1805', 'set:2000', 'preload:1805']);
});

test('cancellation prevents deferred loads and a failed start set aborts preparation', async () => {
  const frames = [], calls = []; let active = true;
  const host = { requestAnimationFrame: fn => frames.push(fn), setTimeout: fn => { calls.push('timer'); fn(); } };
  await prepareSequenceLight({ setTime: async () => true, preload: async () => calls.push('preload') }, () => 0, () => active, host);
  active = false; frames.shift()(); assert.deepEqual(calls, []);
  await assert.rejects(prepareSequenceLight({ setTime: async () => false }, () => 0, () => true, host), /light set/);
});

test('a phone reads manifest_phone.json only and never falls back to the desktop models', async () => {
  const urls = [], fetch0 = globalThis.fetch, warn0 = console.warn;
  globalThis.fetch = async (url) => { urls.push(String(url)); return new Response('missing', { status: 404 }); };
  console.warn = () => {};
  try {
    const renderer = { isWebGPURenderer: true, hasFeature: () => false, backend: {} };
    assert.equal(await loadHero({ renderer, phone: true }), null);
    assert.deepEqual(urls, ['./models/manifest_phone.json']);
    urls.length = 0;
    assert.equal(await loadHero({ renderer, phone: false }), null);
    assert.deepEqual(urls, ['./models/manifest.json']);
  } finally { globalThis.fetch = fetch0; console.warn = warn0; }
});
