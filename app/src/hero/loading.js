/** Decide whether the tier-1 bake can load. Explicit procedural mode always wins. */
export function heroLoadDecision({ search = '', phone = false, supported = true, failed = false, requested = false } = {}) {
  const params = new URLSearchParams(search);
  if (params.has('procedural')) return { load: false, reason: 'procedural' };
  if (!supported) return { load: false, reason: 'unsupported' };
  if (failed) return { load: false, reason: 'failed' };
  if (phone && !requested && !params.has('hero')) return { load: false, reason: 'phone' };
  return { load: true, reason: 'bake' };
}

/** Wait for a painted first view, then an idle slot. Never start a download before that view. */
export async function scheduleHeroLoad(firstView, load, host = globalThis) {
  await firstView;
  await new Promise((resolve) => {
    if (host.requestIdleCallback) host.requestIdleCallback(resolve, { timeout: 2000 });
    else host.setTimeout(resolve, 0);
  });
  return load();
}
