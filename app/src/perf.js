const TIER_ORDER = ['high', 'medium', 'low'];

// These fields control renderer.setPixelRatio, shadowMap.enabled, the RenderPipeline, makeTrees count at the "trees" line, crowd and traffic counts, and loadEnvironment preferSmall.
export const TIERS = {
  high: { pixelRatio: 2, shadows: true, postProcessing: true, treeCount: 60000, crowdFraction: 1, trafficCount: 1200, panoramaSize: '4096' },
  medium: { pixelRatio: 1.5, shadows: true, postProcessing: false, treeCount: 18000, crowdFraction: 0.5, trafficCount: 500, panoramaSize: '2048' },
  low: { pixelRatio: 1, shadows: false, postProcessing: false, treeCount: 4000, crowdFraction: 0.2, trafficCount: 150, panoramaSize: '2048' },
};

/** Detect a quality tier from the renderer and available device hints. */
export function detectTier(renderer) {
  const params = new URLSearchParams(location.search);
  if (params.has('lite')) return 'low';
  const override = params.get('tier');
  if (TIER_ORDER.includes(override)) return override;

  const backend = renderer?.backend;
  const webgpu = Boolean(backend?.isWebGPUBackend || backend?.isWebGPU);
  const webgl2 = Boolean(backend?.isWebGLBackend || backend?.isWebGL2Backend || backend?.isWebGL2);
  const threads = navigator.hardwareConcurrency || 4;
  const memory = navigator.deviceMemory || 4;
  const width = Math.max(screen.width, screen.height);
  const pixels = screen.width * screen.height;
  const touch = navigator.maxTouchPoints > 0 || 'ontouchstart' in window;

  let score = 0;
  if (webgpu) score += 2;
  else if (webgl2) score += 1;
  if (threads >= 8) score += 2;
  else if (threads >= 4) score += 1;
  if (memory >= 8) score += 2;
  else if (memory >= 4) score += 1;
  if (width >= 2560 || pixels >= 5000000) score += 1;
  if (touch) score -= 1;
  if (threads <= 4 || memory <= 4) score -= 1;

  return score >= 5 ? 'high' : score >= 2 ? 'medium' : 'low';
}

/** Create a four-second FPS readout and a one-way quality downgrade monitor. */
export function createFpsMonitor({ onDowngrade, tier = 'high' }) {
  const visible = new URLSearchParams(location.search).has('fps');
  const element = document.createElement('div');
  Object.assign(element.style, {
    position: 'fixed', right: '12px', bottom: '12px', zIndex: '10000',
    padding: '6px 9px', borderRadius: '5px', color: '#fff',
    background: 'rgba(0,0,0,.72)', font: '12px/1.3 monospace',
    pointerEvents: 'none', display: visible ? 'block' : 'none',
  });
  document.body.appendChild(element);

  let currentTier = TIER_ORDER.includes(tier) ? tier : 'high';
  let samples = [];
  let lastFrame = null;
  const sent = new Set();

  return {
    update(now) {
      if (lastFrame !== null && now > lastFrame) samples.push({ time: now, delta: now - lastFrame });
      lastFrame = now;
      const cutoff = now - 4000;
      samples = samples.filter((sample) => sample.time >= cutoff);
      const span = samples.length ? now - (samples[0].time - samples[0].delta) : 0;
      const fps = span > 0 ? samples.reduce((sum, sample) => sum + sample.delta, 0) / samples.length : 0;
      const average = span > 0 ? 1000 / fps : 0;
      if (visible) element.textContent = `${average ? average.toFixed(0) : '--'} FPS · ${currentTier}`;

      if (span >= 4000 && average < 28) {
        const index = TIER_ORDER.indexOf(currentTier);
        const nextTier = TIER_ORDER[Math.min(index + 1, TIER_ORDER.length - 1)];
        if (nextTier !== currentTier && !sent.has(nextTier)) {
          sent.add(nextTier);
          currentTier = nextTier;
          onDowngrade?.(nextTier);
          samples = []; // a fresh 4 s window before judging the new tier
        }
      }
    },
    element,
  };
}
