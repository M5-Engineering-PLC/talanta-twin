import { lightSetAt, SEQUENCE_LIGHT_SETS } from './sequence.js';

// Apply the latest requested sequence light before playback. Fetch other sets only after a paint opportunity.
export async function prepareSequenceLight(tod, startTime, current, host = globalThis) {
  if (!tod) return;
  let first;
  do {
    first = lightSetAt(startTime());
    const applied = await tod.setTime(first);
    if (!current()) return;
    if (!applied) throw new Error(`Hero light set ${first} unavailable`);
  } while (first !== lightSetAt(startTime()));
  const idle = fn => host.requestIdleCallback ? host.requestIdleCallback(fn, { timeout: 4000 }) : host.setTimeout(fn, 200);
  host.requestAnimationFrame(() => {
    if (!current()) return;
    host.requestAnimationFrame(() => {
      if (!current()) return;
      idle(() => { if (current()) for (const t of SEQUENCE_LIGHT_SETS) if (t !== first) void tod.preload(t); });
    });
  });
}
