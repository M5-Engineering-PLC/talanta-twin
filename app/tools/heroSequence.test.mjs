// Software tests. No GPU output or physical measurement is asserted here.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import * as THREE from 'three/webgpu';
import { state, BEATS, createSequencePlayer, installHeroSequence } from '../src/hero/sequence.js';
import { resolveSequencePoses, SEQUENCE_POSES } from '../src/hero/sequencePoses.js';
import { MODULES } from '../src/modules/registry.js';
import { matchState, match_cues } from '../src/events/match.js';

const manifest = JSON.parse(readFileSync(new URL('../cameras/manifest.json', import.meta.url)));
// Focus target fixtures use the same stadium frame as main.js.
const focus = [
  { id: 'top', pose: { pos: [0, 606.12, -.01], target: [0, 6.12, 0], fov: 42 } },
  { id: 'seating', pose: { pos: [-100, 48.12, 0], target: [30, 12.12, 0], fov: 42 } },
  { id: 'pitch', pose: { pos: [117, 136.17, 0], target: [0, 6.12, 0], fov: 42 } },
];
function trustedEvent(type) { const event = new Event(type); Object.defineProperty(event, 'isTrusted', { value: true }); return event; }
const poses = resolveSequencePoses(manifest, focus);
const sample = t => state(t, { poses, crowdFraction: .25 });
const distance = (a, b) => Math.hypot(...a.map((x, i) => x - b[i]));

test('hero state is deterministic in any seek order and clamps endpoints', () => {
  const times = [0, 25, 49, 70, 90, 12, 49, 70];
  const baseline = times.map(sample);
  for (const i of [7, 2, 5, 1, 0, 6, 4, 3]) assert.deepEqual(sample(times[i]), baseline[i]);
  const frame = sample(49); frame.camera.position[0] = Infinity; frame.labels.length = 0;
  assert.deepEqual(sample(49), baseline[2]);
  assert.deepEqual(sample(-10), sample(0)); assert.deepEqual(sample(100), sample(90));
  for (const t of [NaN, Infinity, -Infinity]) assert.throws(() => sample(t), /finite/);
});

test('all seven beats follow the required boundaries and captions stay short', () => {
  assert.deepEqual(BEATS.map(b => [b.start, b.end]), [[0, 14], [14, 24], [24, 36], [36, 48], [48, 62], [62, 78], [78, 90]]);
  BEATS.forEach((b, i) => {
    assert.equal(sample(b.start).beat, i); assert.equal(sample(b.end - .001).beat, i);
    assert.ok(b.caption.split(/\s+/).length <= 8); assert.doesNotMatch(b.caption, /60,?000/);
  });
  assert.equal(sample(0).minutes, 1060); assert.equal(sample(24).minutes, 1085); assert.equal(sample(36).minutes, 1170);
  assert.equal(sample(0).lightSet, '1805'); assert.equal(sample(36).lightSet, '2000');
  assert.equal(sample(36).fill, 0); assert.equal(sample(48).fill, .25);
  assert.equal(sample(24).floodLevel, 0); assert.equal(sample(36).floodLevel, 1);
  assert.ok(sample(21).shieldGlow > sample(14).shieldGlow);
  assert.equal(sample(90).ended, true);
});

test('eased camera segments have no jump larger than 3.5 metres per 1/30 second', () => {
  let largest = 0;
  for (let frame = 0; frame < 2700; frame++) {
    const a = sample(frame / 30).camera, b = sample((frame + 1) / 30).camera;
    largest = Math.max(largest, distance(a.position, b.position));
    assert.ok(distance(a.position, b.position) < 3.5);
    assert.ok(distance(a.target, b.target) < 1.5);
    assert.ok(Math.abs(a.fov - b.fov) < .2);
    assert.ok(distance(a.position, a.target) > 10);
  }
  assert.ok(largest > 0);
});

test('reduced motion holds cameras and fades between holds, including the night city', () => {
  const hold = t => state(t, { poses, reducedMotion: true });
  BEATS.forEach(b => assert.deepEqual(hold(b.start).camera, hold(b.end - .001).camera));
  assert.equal(hold(14).crossfade, 0); assert.equal(hold(14.8).crossfade, 1);
  assert.equal(hold(0).crossfade, 1);
  assert.deepEqual(hold(78).camera.position, manifest.cameras.find(c => c.id === 'L07').position);
});

test('rain and clouds occur only in beat five, with continuous wetness', () => {
  for (let i = 0; i <= 2700; i++) {
    const t = i / 30, q = sample(t);
    if (t <= 48 || t >= 62) { assert.equal(q.rain, 0); assert.equal(q.overcast, 0); }
    else assert.ok(q.rain > 0);
    assert.ok(q.wet >= 0 && q.wet <= 1);
  }
  assert.equal(sample(52).rain, 1); assert.equal(sample(62).wet, 1);
  assert.equal(sample(90).wet, 0);
});

test('the scripted match reaches the real goal cue and keeps its claim', () => {
  assert.equal(sample(61).matchTime, null);
  assert.equal(matchState(match_cues, sample(62).matchTime).phase, 'shot');
  const goal = matchState(match_cues, sample(70).matchTime);
  assert.equal(goal.phase, 'goal'); assert.deepEqual(goal.score, [1, 0]);
  assert.equal(sample(70).goalElapsed, 0); assert.equal(sample(77).goalElapsed, 7);
  assert.equal(sample(78).matchTime, 68); assert.equal(sample(78).goalElapsed, null);
});

test('crowd, match, facade and floodlights carry exact registry labels', () => {
  const crowd = MODULES.find(m => m.id === 'PPL-01').claim, show = MODULES.find(m => m.id === 'SHW-01').claim;
  for (let t = 0; t <= 90; t += 1 / 30) {
    const q = sample(t);
    assert.ok(q.labels.includes(crowd));
    if (q.floodLevel > 0 || q.shieldGlow > 0) assert.ok(q.labels.includes(show));
  }
});

test('pose data references only the selected virtual views and fails on missing targets', () => {
  assert.deepEqual(SEQUENCE_POSES.filter(p => p.manifest).map(p => p.manifest), ['C16', 'L06', 'C06', 'L07']);
  assert.throws(() => resolveSequencePoses(manifest, []), /pose unavailable/);
});

test('pointer, wheel, touch, any key and Escape stop playback and restore the host', async () => {
  for (const type of ['pointerdown', 'wheel', 'touchstart', 'keydown']) {
    const input = new EventTarget(); let stopped = 0, delivered = 0;
    const player = createSequencePlayer({ input, sample, now: () => 0, onState() { delivered++; }, onStop() { stopped++; } });
    await player.start(); player.tick(1000); const before = delivered;
    const event = trustedEvent(type); if (type === 'keydown') Object.defineProperty(event, 'key', { value: 'Escape' });
    input.dispatchEvent(event); player.tick(2000);
    assert.equal(player.active, false); assert.equal(stopped, 1); assert.equal(delivered, before);
    input.dispatchEvent(event); assert.equal(stopped, 1);
  }
});

test('input during loading cancels autoplay before a late prepare completes', async () => {
  const input = new EventTarget(); let resolve, frames = 0;
  const player = createSequencePlayer({ input, sample, prepare: () => new Promise(r => { resolve = r; }), onState() { frames++; } });
  const pending = player.start(); input.dispatchEvent(trustedEvent('wheel')); resolve();
  assert.equal(await pending, null); assert.equal(frames, 0); assert.equal(player.active, false);
});

test('seeking freezes the requested frame and the final state stays still', async () => {
  let clock = 0;
  const player = createSequencePlayer({ sample, input: new EventTarget(), now: () => clock });
  await player.seek(70); clock = 200000; assert.deepEqual(player.tick(clock), sample(70));
  await player.seek(90); assert.equal(player.phase, 'held'); assert.deepEqual(player.tick(clock), sample(90));
  await player.start(); clock += 90000; assert.deepEqual(player.tick(clock), sample(90));
  assert.deepEqual(player.tick(clock + 6000), sample(90)); player.stop();
});

test('failed preparation stops the player and allows a retry', async () => {
  let first = true;
  const player = createSequencePlayer({ sample, input: new EventTarget(), prepare: async () => {
    if (first) { first = false; throw new Error('Asset unavailable'); }
  } });
  await assert.rejects(player.start(), /Asset unavailable/); assert.equal(player.active, false);
  await player.start(); assert.equal(player.active, true); player.stop();
});

test('software host adapter seeks match, restores controls and anchors crowd reaction time', async () => {
  const priorDocument = globalThis.document, priorWindow = globalThis.window, priorMedia = globalThis.matchMedia;
  const element = () => ({ hidden: true, textContent: '', style: {}, dataset: {}, append() {} });
  const caption = element(), claims = element(), replay = element(), button = element();
  const strip = { ...element(), querySelector: s => s === '[data-caption]' ? caption : s === '[data-claims]' ? claims : replay };
  globalThis.document = { getElementById: () => strip, querySelectorAll: () => [button], createElement: element };
  globalThis.window = new EventTarget(); globalThis.matchMedia = () => ({ matches: false });
  const scene = new THREE.Scene(), camera = new THREE.PerspectiveCamera();
  const controls = { target: new THREE.Vector3(), enabled: true, enableDamping: true, update() {} };
  const fills = [], group = new THREE.Group(); group.userData.animation = { start: { value: 0 } };
  const crowd = { group, setFill: f => fills.push(f), update(dt, t) { this.time = t; }, react(name, p) { if (name === 'goal') this.goal = p; }, setNight() {} };
  let hostFrame;
  try {
    const director = installHeroSequence({ scene, camera, controls, canvas: { toDataURL: () => 'data:image/png;base64,AA' }, stage: element(),
      manifest, focus, sky: {}, paintSky() {}, bearing: 0, pad: 6.12,
      tier: () => 'medium', fraction: () => .25, crowd: () => crowd, roots: () => [], night: () => 1,
      prepare: async () => {}, dismiss() {}, frame: q => { hostFrame = q; }, stop() {}, lights() {}, error() {} });
    await director.seek(70); director.tick(100000); director.render(100000);
    assert.equal(controls.enabled, false); assert.equal(controls.enableDamping, false);
    assert.equal(scene.getObjectByName('SPT-01').visible, true);
    assert.equal(crowd.time, 70); assert.equal(crowd.goal.duration, 8); assert.equal(group.userData.animation.start.value, 70);
    assert.deepEqual(camera.position.toArray(), hostFrame.camera.position);
    assert.match(claims.textContent, /Illustrative crowd behaviour/);
    await director.seek(50); assert.equal(scene.getObjectByName('SPT-01').visible, false); assert.equal(crowd.goal.duration, 0);
    await director.seek(90); assert.equal(controls.enabled, true); assert.equal(controls.enableDamping, true); assert.equal(replay.hidden, false);
    const held = camera.position.clone(); director.tick(900000); assert.ok(camera.position.equals(held));
    await director.seek(55);
    assert.equal(button.textContent, 'Stop hero'); assert.equal(strip.hidden, false); assert.equal(controls.enabled, false);
    await director.seek(85); assert.equal(strip.hidden, false); assert.equal(button.textContent, 'Stop hero');
    await director.seek(90);
    const replayInput = trustedEvent('pointerdown'); Object.defineProperty(replayInput, 'target', { value: replay });
    globalThis.window.dispatchEvent(replayInput);
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(director.active, true); assert.equal(controls.enabled, false);
    globalThis.window.dispatchEvent(trustedEvent('wheel'));
    assert.equal(director.active, false); assert.equal(scene.getObjectByName('SPT-01'), undefined); assert.equal(strip.hidden, true);
    assert.ok(fills.length <= 3);
  } finally { globalThis.document = priorDocument; globalThis.window = priorWindow; globalThis.matchMedia = priorMedia; }
});

// Synthetic input can come from capture automation or UI synchronization.
test('synthetic input preserves seeks at 55 and 85 seconds', async () => {
  const input = new EventTarget(), player = createSequencePlayer({ input, sample });
  for (const t of [55, 85]) {
    await player.seek(t);
    for (const type of ['pointerdown', 'wheel', 'keydown', 'touchstart']) input.dispatchEvent(new Event(type));
    assert.equal(player.active, true); assert.equal(player.frame.time, t);
    assert.equal(player.tick(999999).time, t);
  }
  player.stop();
});

test('concurrent seeks share preparation and hold the latest requested time', async () => {
  let ready, preparations = 0;
  const player = createSequencePlayer({ sample, input: new EventTarget(), prepare: () => {
    preparations++; return new Promise(resolve => { ready = resolve; });
  } });
  const first = player.seek(55), second = player.seek(85); ready();
  assert.equal((await first).time, 85); assert.equal((await second).time, 85);
  assert.equal(preparations, 1); assert.equal(player.tick(999999).time, 85); player.stop();
});
