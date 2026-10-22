// Bloom estimate: one bright pass, ten blur passes, and one composite pass at half resolution or smaller.
// The 2 ms high-tier target needs device timing. Medium and low create no post passes.
const TIER_ORDER = ['high', 'medium', 'low'];

// These fields control renderer.setPixelRatio, shadowMap.enabled, the RenderPipeline, makeTrees count at the "trees" line, crowd and traffic counts, and loadEnvironment preferSmall.
export const TIERS = {
  high: { pixelRatio: 1.5, shadowSize: 2048, shadowExtent: 420, shadowFar: 2600, shadows: true, postProcessing: true, bloomResolutionScale: 0.5, treeCount: 60000, crowdFraction: 1, trafficCount: 1200, panoramaSize: '4096' },
  medium: { pixelRatio: 1.25, shadowSize: 1024, shadowExtent: 300, shadowFar: 2300, shadows: true, postProcessing: false, treeCount: 18000, crowdFraction: 0.25, trafficCount: 180, panoramaSize: '2048' },
  low: { pixelRatio: 1, shadowSize: 512, shadowExtent: 240, shadowFar: 2100, shadows: false, postProcessing: false, treeCount: 4000, crowdFraction: 0, trafficCount: 40, panoramaSize: '2048' },
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
  // Conservative startup for the 1366px, shared-memory laptop class; this is a hint, not a GPU benchmark.
  if (memory <= 8 && threads <= 8 && width <= 1600) return 'low';

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
  // An explicit ?tier= pins the tier: no automatic downgrade.
  if (new URLSearchParams(location.search).has('tier')) onDowngrade = () => {};
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

/** Count submitted geometry before culling, without rendering or GPU timing. */
export function profileGeometry(root) {
  let drawCalls = 0, triangles = 0;
  const visit = (node) => {
    if (!node || !node.visible) return;
    if (node.isMesh) {
      const g = node.geometry, instances = node.isInstancedMesh ? node.count : 1;
      const end = Math.min(g.index?.count ?? g.attributes.position.count, g.drawRange.start + g.drawRange.count);
      const groups = Array.isArray(node.material) ? g.groups : [{ start: 0, count: end, materialIndex: 0 }];
      for (const part of groups) {
        const material = Array.isArray(node.material) ? node.material[part.materialIndex] : node.material;
        const count = Math.max(0, Math.min(end, part.start + part.count) - Math.max(g.drawRange.start, part.start));
        if (instances > 0 && count > 0 && material?.visible) { drawCalls++; triangles += count / 3 * instances; }
      }
    }
    for (const child of node.children ?? []) visit(child);
  };
  visit(root);
  return { claim: 'derived', drawCalls, triangles };
}

// Software-derived snapshot from the bundled data, 2026-10-18. Counts precede culling and exclude extra passes.
const seats = 56972;
export const PROFILE_BY_TIER = Object.fromEntries(Object.entries(TIERS).map(([tier, quality]) => {
  const low = tier === 'low', high = tier === 'high';
  return [tier, {
    claim: 'derived',
    seats: { drawCalls: 1, triangles: seats * (high ? 36 : low ? 2 : 24), cpuPerFrame: 'No matrix writes; static instances.' },
    bowl: { drawCalls: 50, triangles: 149232, cpuPerFrame: 'No mesh rebuild; construction mutations only when state changes.' },
    context: { drawCalls: 6, triangles: 168741 + 12401 + (high ? 4691840 : low ? 403200 : 1564800), cpuPerFrame: 'Static trees, buildings and roads; traversal and culling only.' },
    site: { drawCalls: low ? 13 : 14, triangles: low ? 13785 : 44697, cpuPerFrame: '73 jets, 146 matrix writes, 40 walking updates; skipped while hidden or in hero mode.' },
    traffic: { claim: 'derived', proxyDrawCalls: 24, proxyTriangles: high ? 154428 : low ? 5228 : 23132, count: quality.trafficCount, cpuPerFrame: 'Lane sorting O(N log N), vehicle transforms and instance uploads; setLimit still visits the original fleet.' },
    crowd: { drawCalls: low ? 0 : 7, triangles: high ? 2945840 : low ? 0 : 738272, cpuPerFrame: low ? 'Disabled; no crowd build or updates.' : 'Three uniforms, 25 player transforms and 75 matrix writes; fan motion runs on the GPU.' },
    shadows: { claim: 'estimated', casterDrawCalls: low ? 0 : 65, casterTriangles: high ? 5017288 : low ? 0 : 1758952, mapSize: quality.shadows ? quality.shadowSize : 0, extent: quality.shadowExtent, far: quality.shadowFar, cpuPerFrame: quality.shadows ? 'One directional-light caster pass; extra draws and triangles depend on the shadow frustum.' : 'No shadow pass.' },
  }];
}));
