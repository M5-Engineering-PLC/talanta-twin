import { MODULES } from '../modules/registry.js';
import { resolveSequencePoses } from './sequencePoses.js';
import { installRain, installWetLook } from '../weather/rain.js';
import { installOvercast } from '../weather/sky.js';

export const DURATION = 90;
export const BEATS = Object.freeze([
  { start: 0, end: 14, caption: 'Over Ngong Road, toward the hills' },
  { start: 14, end: 24, caption: 'The roof catches the last sun' },
  { start: 24, end: 36, caption: 'Sunset. The floodlights come on' },
  { start: 36, end: 48, caption: 'The stands fill' },
  { start: 48, end: 62, caption: 'Rain falls. The concourse shines' },
  { start: 62, end: 78, caption: 'A goal. The crowd celebrates' },
  { start: 78, end: 90, caption: 'The stadium in the night city' },
]);
const CROWD = MODULES.find(m => m.id === 'PPL-01').claim;
const SHOW = MODULES.find(m => m.id === 'SHW-01').claim;
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const ease = x => { const t = clamp(x); return t * t * (3 - 2 * t); };
const ramp = (a, b, t) => ease((t - a) / (b - a));

// Eased segments have zero velocity at each shared pose. There are no camera cuts.
function cameraAt(t, poses, reducedMotion, beat) {
  if (reducedMotion) return structuredClone(beat === 6 ? poses.at(-1) : poses[Math.min(beat, poses.length - 1)]);
  const i = Math.max(0, poses.findLastIndex(p => p.time <= t));
  const a = poses[i], b = poses[Math.min(i + 1, poses.length - 1)];
  const u = a === b ? 0 : ramp(a.time, b.time, t);
  const lerp = (x, y) => x + (y - x) * u;
  return { position: a.position.map((v, j) => lerp(v, b.position[j])),
    target: a.target.map((v, j) => lerp(v, b.target[j])), fov: lerp(a.fov, b.fov) };
}

// Pure absolute-time state. All times are seconds, positions are app-local metres.
// A caller supplies resolved poses so this function needs no browser or renderer.
export function state(t, { poses, crowdFraction = 1, reducedMotion = false } = {}) {
  if (!Number.isFinite(t)) throw new Error('Hero time must be finite');
  if (!poses?.length) throw new Error('Hero poses are required');
  t = clamp(t, 0, DURATION);
  const beat = Math.min(6, BEATS.findIndex(b => t < b.end) < 0 ? 6 : BEATS.findIndex(b => t < b.end));
  const rain = t >= 48 && t < 62 ? ramp(48, 50, t) * (1 - ramp(60, 62, t)) : 0;
  const minutes = t < 24 ? 1060 + 25 * ramp(14, 24, t) : 1085 + 85 * ramp(24, 36, t);
  const fill = clamp(crowdFraction) * ramp(36, 48, t);
  const floodLevel = ramp(24, 36, t), shieldGlow = 1.5 * ramp(14, 21, t);
  // Jump to the attack, reach the existing 60 s goal cue at hero 70 s, then celebrate.
  const matchTime = t < 62 ? null : t < 78 ? 52 + (t - 62) : 68;
  return { time: t, beat, camera: cameraAt(t, poses, reducedMotion, beat), minutes,
    lightSet: t < 31 ? '1805' : '2000', fill, rain, overcast: rain,
    wet: t < 48 ? 0 : t < 62 ? ramp(48, 52, t) : 1 - ramp(62, 90, t),
    floodLevel, shieldGlow, matchTime, goalElapsed: t >= 70 && t < 78 ? t - 70 : null,
    caption: BEATS[beat].caption,
    // Scale figures can already be visible in the site. Keep their claim throughout.
    labels: [CROWD, ...((floodLevel > 0 || shieldGlow > 0) ? [SHOW] : [])],
    reducedMotion, crossfade: reducedMotion && beat > 0 ? ramp(BEATS[beat].start, BEATS[beat].start + .8, t) : 1,
    ended: t === DURATION };
}

// The player is independent of rendering so input, loading races, and seeking can be tested.
export function createSequencePlayer({ sample, prepare = async () => {}, onState = () => {}, onStop = () => {},
  input = globalThis.window, now = () => performance.now() }) {
  let phase = 'idle', epoch = 0, origin = 0, frame = null, seeking = false, pending = null, requestedTime = 0;
  const events = ['pointerdown', 'wheel', 'keydown', 'touchstart'];
  const options = { capture: true, passive: true };
  const onInput = event => { if (event.isTrusted) stop(event); };
  function listen(on) { for (const type of events) input?.[on ? 'addEventListener' : 'removeEventListener'](type, onInput, options); }
  function emit(t) { frame = sample(t); onState(frame); if (frame.ended) phase = 'held'; return frame; }
  function start(t = 0, seek = false) {
    stop(); phase = 'loading'; seeking = seek; requestedTime = t; const version = ++epoch; listen(true);
    pending = (async () => {
      try {
        await prepare(() => version === epoch);
        if (version !== epoch) return null;
        phase = 'playing'; origin = now() - clamp(requestedTime, 0, DURATION) * 1000;
        return emit(requestedTime);
      } catch (error) { if (version === epoch) stop(); throw error; }
      finally { if (version === epoch) pending = null; }
    })();
    return pending;
  }
  function stop(reason) {
    const active = phase !== 'idle'; ++epoch; phase = 'idle'; frame = null; listen(false);
    if (active) onStop(reason);
  }
  return { start, stop,
    async seek(t) {
      if (!Number.isFinite(t)) throw new Error('Hero time must be finite');
      if (phase === 'idle') return start(t, true);
      if (phase === 'loading') { requestedTime = t; seeking = true; return pending; }
      seeking = true; phase = 'playing'; return emit(t);
    },
    tick(time = now()) { if (phase === 'playing' && !seeking) emit((time - origin) / 1000); return frame; },
    get active() { return phase !== 'idle'; }, get phase() { return phase; }, get frame() { return frame; },
  };
}

// On-demand CAM-01 adapter. Weather remains usable after the sequence stops.
export function installHeroSequence(host) {
  const { scene, camera, controls, canvas, stage, manifest, focus, paintSky, sky } = host;
  const poses = resolveSequencePoses(manifest, focus);
  const rain = installRain({ scene, camera, tier: host.tier() });
  const wet = installWetLook(), overcast = installOvercast({ scene, sky, paintSky });
  const strip = document.getElementById('hero-caption'), caption = strip.querySelector('[data-caption]');
  const labels = strip.querySelector('[data-claims]'), replay = strip.querySelector('button');
  const buttons = [...document.querySelectorAll('[data-hero]')];
  const snapshot = document.createElement('img'); snapshot.className = 'hero-crossfade'; snapshot.alt = ''; snapshot.hidden = true; stage.append(snapshot);
  let match = null, matchRoot = null, lastFill = -1, lastBeat = -1, lastCrowd = null, manualRain = false;
  let reduced = false, savedControls = null, scanAt = -Infinity, prepared = false;
  let holdImage = '', capturedBeat = -1;
  function restoreControls() {
    if (!savedControls) return;
    Object.assign(controls, savedControls); savedControls = null;
  }
  function takeControl() {
    if (!savedControls) savedControls = { enabled: controls.enabled, enableDamping: controls.enableDamping };
    controls.enableDamping = false; controls.update(); controls.enabled = false;
  }
  const player = createSequencePlayer({
    sample: t => state(t, { poses, reducedMotion: reduced, crowdFraction: host.fraction() }),
    async prepare(current) {
      reduced = globalThis.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false;
      buttons.forEach(b => { b.textContent = 'Loading hero…'; }); strip.hidden = false; caption.textContent = 'Loading the hero sequence';
      labels.textContent = `${CROWD} ${SHOW}`;
      const [module] = await Promise.all([import('../events/match.js'), host.prepare(current)]);
      if (!current()) return;
      match = module.installMatch({ scene, bearing: host.bearing, pad: host.pad, getCrowd: host.crowd });
      matchRoot = scene.getObjectByName('SPT-01'); matchRoot.visible = false;
      prepared = true; lastBeat = -1; lastFill = -1; holdImage = ''; capturedBeat = -1; takeControl(); host.dismiss();
      buttons.forEach(b => { b.textContent = 'Stop hero'; });
    },
    onState(q) {
      strip.hidden = false;
      if (!q.ended) { if (!savedControls) takeControl(); buttons.forEach(b => { b.textContent = 'Stop hero'; }); }
      if (q.reducedMotion && q.beat !== lastBeat && lastBeat >= 0) {
        snapshot.src = holdImage; snapshot.hidden = !holdImage;
      }
      snapshot.style.opacity = String(1 - q.crossfade);
      if (q.crossfade === 1) snapshot.hidden = true;
      lastBeat = q.beat;
      camera.position.fromArray(q.camera.position); controls.target.fromArray(q.camera.target);
      camera.clearViewOffset(); camera.fov = q.camera.fov; camera.lookAt(controls.target); camera.updateProjectionMatrix();
      const crowd = host.crowd();
      // setFill rebuilds crowd batches. Limit this to 2% steps rather than every frame.
      const fill = q.fill === host.fraction() ? q.fill : Math.floor(q.fill * 50) / 50;
      if (crowd && (fill !== lastFill || crowd !== lastCrowd)) { crowd.setFill(fill); lastFill = fill; lastCrowd = crowd; }
      if (crowd) {
        const u = crowd.group.userData.animation;
        // react() reads its existing clock. Anchor the reaction to hero 70 s on every seek.
        crowd.update(0, 70); crowd.react('goal', { end: -1, duration: q.goalElapsed === null ? 0 : 8 });
        crowd.update(0, q.time); crowd.setNight(q.floodLevel > .5); crowd.react('phones', { on: q.floodLevel > .5 });
        if (u) u.start.value = 70;
      }
      matchRoot.visible = q.matchTime !== null; if (matchRoot.visible) match.seek(q.matchTime);
      host.frame(q);
      if (caption.textContent !== q.caption) caption.textContent = q.caption;
      const claim = q.labels.join(' '); if (labels.textContent !== claim) labels.textContent = claim;
      replay.hidden = !q.ended;
      if (q.ended) { restoreControls(); buttons.forEach(b => { b.textContent = 'Hero'; }); }
    },
    onStop(event) {
      const button = event?.target?.closest?.('[data-hero]');
      if (button && (event.type === 'pointerdown' || event.type === 'keydown' && ['Enter', ' '].includes(event.key))) button.dataset.heroStopped = '1';
      const replayInput = event?.target === replay && (event.type === 'pointerdown' || event.type === 'keydown' && ['Enter', ' '].includes(event.key));
      restoreControls(); wet.restore(); overcast.restore(); snapshot.hidden = true;
      match?.dispose(); match = null; matchRoot = null;
      strip.hidden = true; replay.hidden = true; buttons.forEach(b => { b.textContent = 'Hero'; });
      prepared = false; host.stop();
      // Hiding Replay on pointerdown can prevent its later click. Restart from that input.
      if (replayInput) queueMicrotask(() => { void player.start().catch(host.error); });
    },
  });
  replay.onclick = () => { if (player.phase === 'held' || !player.active) void player.start().catch(host.error); };
  return { get active() { return player.active; }, get frame() { return player.frame; },
    start: () => player.start(), stop: () => player.stop(), seek: t => player.seek(t),
    setRain(on) { manualRain = Boolean(on); },
    tick(now) { wet.restore(); overcast.restore(); player.tick(now); },
    afterRender() {
      const q = player.frame;
      if (!q?.reducedMotion || q.crossfade < 1 || capturedBeat === q.beat) return;
      // Capture inside the render callback, before WebGL discards the drawing buffer.
      try { holdImage = canvas.toDataURL(); capturedBeat = q.beat; } catch { holdImage = ''; }
    },
    render(now) {
      if (now - scanAt > 1000) { for (const root of host.roots()) wet.collect(root); scanAt = now; }
      const q = prepared ? player.frame : null, amount = q ? q.rain : Number(manualRain);
      const seconds = q?.time ?? now / 1000;
      rain.update(seconds, amount, host.tier());
      wet.update(q?.wet ?? amount, q?.floodLevel ?? null, q?.shieldGlow ?? 0);
      overcast.update(q?.overcast ?? amount, q ? q.floodLevel : host.night());
      if (q) host.lights(q);
    },
  };
}
