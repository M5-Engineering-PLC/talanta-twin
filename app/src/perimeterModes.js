// Serialize mode ownership: a late import is disposed instead of replacing a newer selection.
export function createModeController({ load }) {
  let epoch = 0, active = null;
  return {
    async select(mode) {
      if (!['venue', 'football', 'concert', 'drone'].includes(mode)) throw new Error(`Unknown mode: ${mode}`);
      const version = ++epoch; active?.dispose(); active = null;
      if (mode === 'venue') return;
      const instance = await load(mode);
      if (version !== epoch) { instance.dispose(); return; }
      active = instance;
    },
    update(dt) { active?.update(dt); },
    dispose() { ++epoch; active?.dispose(); active = null; },
  };
}
