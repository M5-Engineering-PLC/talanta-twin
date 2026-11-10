// Software tests of the real monitor, with a slow synthetic clock.
import test from 'node:test';
import assert from 'node:assert/strict';
import { createFpsMonitor, TIERS } from '../src/perf.js';

test('every valid URL tier stays pinned in both behavior and the FPS readout', () => {
  const previous = { document: globalThis.document, location: globalThis.location };
  globalThis.document = { createElement: () => ({ style: {} }), body: { appendChild() {} } };
  try {
    for (const tier of Object.keys(TIERS)) {
      globalThis.location = { search: `?tier=${tier}&fps` };
      const changes = [], monitor = createFpsMonitor({ tier, onDowngrade: t => changes.push(t) });
      for (let now = 0; now <= 24000; now += 100) monitor.update(now);
      assert.deepEqual(changes, []); assert.match(monitor.element.textContent, new RegExp(`${tier}$`));
    }
    for (const search of ['?fps', '?tier=invalid&fps']) {
      globalThis.location = { search };
      const changes = [], monitor = createFpsMonitor({ tier: 'high', onDowngrade: t => changes.push(t) });
      for (let now = 0; now <= 16000; now += 100) monitor.update(now);
      assert.deepEqual(changes, ['medium', 'low']); assert.match(monitor.element.textContent, /low$/);
    }
  } finally { Object.assign(globalThis, previous); }
});
