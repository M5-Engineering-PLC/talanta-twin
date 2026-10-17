// Guided tour and touch controls. Software (browser camera) behaviour only.
import * as THREE from 'three/webgpu';

const TOTAL_MS = 90000, TRANS_MS = 2800, MIN_HOLD_MS = 5500;
const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches;

// views: array of ids, or of { id, name, k } objects. Ids fall back to the #focuslist text for name and line.
function describe(v) {
  if (typeof v === 'object') return { id: v.id, name: v.name ?? v.id, k: v.k ?? '' };
  const el = document.querySelector(`#focuslist [data-focus="${v}"]`);
  return { id: v, name: el?.firstElementChild?.firstChild?.textContent?.trim() || v, k: el?.querySelector('.k')?.textContent || '' };
}

export function createTour({ camera, controls, views, focus, onStop }) {
  const list = views.map(describe);
  const stage = document.querySelector('#stage') || document.body;
  let cap = null, raf = 0, steps = null, i = 0, tStep = 0, tPrev = 0, dir = 1, cut = false;
  const api = { start, stop, get running() { return !!steps; } };

  function mkCaption() {
    cap = document.createElement('div');
    cap.setAttribute('role', 'status'); cap.setAttribute('aria-live', 'polite');
    cap.style.cssText = 'position:absolute;left:16px;bottom:16px;max-width:min(440px,calc(100% - 32px));padding:10px 14px 11px;border-left:4px solid #f2b33d;border-radius:4px;background:rgba(20,20,18,.78);color:#fff;font:13px/1.35 system-ui,sans-serif;pointer-events:none;z-index:4;opacity:0;transform:translateY(8px);transition:opacity .6s,transform .6s';
    cap.innerHTML = '<b style="display:block;font-size:15px;letter-spacing:.2px"></b><span style="opacity:.85"></span>';
    stage.appendChild(cap);
  }
  function caption(v, on) {
    if (!cap) return;
    if (v) { cap.firstChild.textContent = v.name; cap.lastChild.textContent = v.k; }
    cap.style.opacity = on ? '1' : '0'; cap.style.transform = on ? 'none' : 'translateY(8px)';
  }

  function go(n) {
    i = n % list.length; tStep = performance.now(); dir = i % 2 ? -1 : 1;
    caption(list[i], true);
    focus(list[i].id, cut ? 1 : TRANS_MS);
  }

  function frame(now) {
    if (!steps) return;
    raf = requestAnimationFrame(frame);
    const dt = Math.min(0.1, (now - tPrev) / 1000); tPrev = now;
    const el = now - tStep, hold = steps.slot - (cut ? 0 : TRANS_MS);
    if (el >= steps.slot) { if (i + 1 >= list.length) return stop(); caption(null, false); return go(i + 1); }
    if (cut || el < TRANS_MS) return;
    if (steps.slot - el < 700) caption(null, false);
    // Hold phase: slow orbit about the target with a gentle push-in, eased in and out.
    const u = (el - TRANS_MS) / Math.max(1, hold), w = Math.sin(Math.PI * Math.min(1, u)) * 0.07 * dt * dir;
    const off = camera.position.clone().sub(controls.target);
    off.applyAxisAngle(THREE.Object3D.DEFAULT_UP, w).multiplyScalar(1 - 0.012 * dt * Math.sin(Math.PI * Math.min(1, u)));
    camera.position.copy(controls.target).add(off);
  }

  const onInput = (e) => {
    if (e.type === 'keydown' && ['Shift', 'Control', 'Alt', 'Meta'].includes(e.key)) return;
    stop();
  };
  const EV = [['pointerdown', stage], ['wheel', stage], ['touchstart', stage], ['keydown', window]];

  function start() {
    if (steps || !list.length) return;
    cut = reduced();
    steps = { slot: Math.max(MIN_HOLD_MS + (cut ? 0 : TRANS_MS), TOTAL_MS / list.length) };
    mkCaption();
    for (const [t, el] of EV) el.addEventListener(t, onInput, { passive: true });
    tPrev = performance.now();
    void cap.offsetWidth; // flush style so the caption fades in
    go(0);
    raf = requestAnimationFrame(frame);
  }

  function stop() {
    if (!steps) return;
    steps = null; cancelAnimationFrame(raf);
    for (const [t, el] of EV) el.removeEventListener(t, onInput);
    const c = cap; cap = null;
    if (c) { c.style.opacity = '0'; setTimeout(() => c.remove(), 700); }
    onStop?.();
  }
  return api;
}

// Phone controls: one finger rotates, two fingers pinch and pan; swipe on the views bar steps views; double-tap centres.
export function enableTouchUX({ stage, controls, onPrev, onNext, onCentre }) {
  controls.touches = { ONE: THREE.TOUCH.ROTATE, TWO: THREE.TOUCH.DOLLY_PAN };
  controls.screenSpacePanning = true; controls.enableDamping = true;
  const canvas = () => stage.querySelector('canvas') || stage;
  const noScroll = (el) => { el.style.touchAction = 'none'; el.style.overscrollBehavior = 'contain'; el.style.userSelect = 'none'; el.style.webkitUserSelect = 'none'; el.style.webkitTouchCallout = 'none'; };
  noScroll(stage);
  const cv = canvas(); noScroll(cv);
  const off = [];
  const on = (el, t, fn, o) => { el.addEventListener(t, fn, o); off.push(() => el.removeEventListener(t, fn, o)); };
  on(cv, 'contextmenu', (e) => e.preventDefault());
  on(stage, 'touchmove', (e) => { if (e.target === cv || cv.contains(e.target)) e.preventDefault(); }, { passive: false });

  // Double-tap on the canvas (single finger, short, small movement).
  let last = null, down = null;
  on(cv, 'pointerdown', (e) => { if (e.pointerType === 'touch') down = { t: performance.now(), x: e.clientX, y: e.clientY, n: (down?.n || 0) }; });
  on(cv, 'pointerup', (e) => {
    if (e.pointerType !== 'touch' || !down) return;
    const now = performance.now();
    if (now - down.t > 250 || Math.hypot(e.clientX - down.x, e.clientY - down.y) > 12) { down = null; return; }
    if (last && now - last.t < 320 && Math.hypot(e.clientX - last.x, e.clientY - last.y) < 30) { last = null; onCentre?.(); }
    else last = { t: now, x: e.clientX, y: e.clientY };
    down = null;
  });

  // Horizontal swipe on the views bar: left = next, right = previous.
  const bar = stage.querySelector('#focusbar');
  if (bar) {
    bar.style.touchAction = 'pan-y';
    let s = null;
    on(bar, 'touchstart', (e) => { const t = e.touches[0]; s = e.touches.length === 1 ? { x: t.clientX, y: t.clientY, t: performance.now() } : null; }, { passive: true });
    on(bar, 'touchend', (e) => {
      if (!s) return; const t = e.changedTouches[0], dx = t.clientX - s.x, dy = t.clientY - s.y; const ok = performance.now() - s.t < 700; s = null;
      if (ok && Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy) * 1.5) { dx < 0 ? onNext?.() : onPrev?.(); }
    }, { passive: true });
  }
  return () => off.forEach((f) => f());
}
