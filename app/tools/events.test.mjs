import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import * as THREE from 'three/webgpu';
import { concert_cues, match_cues } from '../src/events/cues.js';
import { concertState, concertBudget } from '../src/events/concert-state.js';
import { matchState } from '../src/events/match-state.js';
import { crossedReactions } from '../src/events/state.js';
import { playback } from '../src/events/playback.js';
import { installConcert } from '../src/events/concert.js';
import { installMatch } from '../src/events/match.js';
import { installSeatedCrowd } from '../src/people/index.js';

const concert = t => concertState(concert_cues, t, concertBudget('low'));
const match = t => matchState(match_cues, t);

test('event state stays deterministic, JSON-safe, and leaves cue data unchanged', () => {
  const before = JSON.stringify([concert_cues, match_cues]);
  for (const sample of [concert, match]) {
    for (const t of [0, 8, 24, 36, 59.999, 60, 64, 76, 90, 123.5]) {
      const expected = sample(t);
      sample(t + 17);
      assert.deepEqual(sample(t), expected);
      assert.deepEqual(JSON.parse(JSON.stringify(expected)), expected);
    }
  }
  assert.equal(JSON.stringify([concert_cues, match_cues]), before);
});

test('cue boundaries switch phases exactly and both timelines loop', () => {
  for (const [cues, sample] of [[concert_cues, concert], [match_cues, match]]) {
    cues.forEach((cue, i) => {
      assert.equal(sample(cue.start).phase, cue.params.mode);
      if (i) assert.equal(sample(cue.start - .00001).phase, cues[i - 1].params.mode);
      assert.equal(sample(cue.start + cue.duration - .00001).phase, cue.params.mode);
    });
    const duration = cues.at(-1).start + cues.at(-1).duration;
    assert.deepEqual(sample(duration), sample(0));
    assert.deepEqual(sample(duration + 5), sample(5));
  }
});

test('concert counts follow tiers and the phone width boundary', () => {
  // The floor crowd count is budget.crowd. More concert checks are in concert.test.mjs.
  for (const [tier, count, heads] of [['high', 5000, 16], ['medium', 2000, 12], ['low', 700, 8]]) {
    for (const width of [390, 767, 768, 1280]) {
      const budget = concertBudget(tier, width), frame = concertState(concert_cues, 25, budget);
      assert.equal(frame.floor.count, width < 768 ? count / 2 : count);
      assert.equal(frame.lights.length, width < 768 ? 8 : heads);
      assert.equal(budget.lights, 0);
      assert.equal(frame.screens.length, 3);
    }
  }
});

test('concert places the stage south facing north and takes BPM from cues', () => {
  const s = concert(24.25);
  assert.equal(s.stage.position[2], 46);
  assert.equal(s.stage.heading, Math.PI);
  assert.equal(s.beat, 48.5);
  assert.ok(s.lights.every(l => l.target[2] < l.position[2] && l.intensity > 0));
  const cues = structuredClone(concert_cues); cues[2].params.bpm = 60;
  assert.equal(concertState(cues, 24.25).beat, 24.25);
});

test('football keeps 22 players plus one referee and the ball within the pitch except during the goal', () => {
  for (let tick = 0; tick < 9000; tick++) {
    const t = tick / 100, s = match(t);
    assert.equal(s.players.length, 22);
    assert.equal(new Set(s.players.map(p => p.id)).size, 22);
    assert.equal(s.players.filter(p => p.color === '#b92332').length, 11);
    assert.equal(s.players.filter(p => p.color === '#18733d').length, 11);
    assert.equal(s.referee.color, '#111111');
    assert.equal(s.referee.id, 22);
    assert.ok(s.players.every(p => Math.abs(p.position[0]) <= 34 && Math.abs(p.position[2]) <= 52.5));
    const [x, y, z] = s.ball.position;
    assert.ok(Math.abs(x) <= 34 && y >= .22);
    assert.ok(Math.abs(z) <= 52.5 || s.phase === 'goal', `${t}: ball outside pitch during ${s.phase}`);
    if (s.phase === 'goal') assert.ok(Math.abs(x) < 3.66 && y < 2.44 && z >= -54.5 && z < -52.5);
  }
});

test('goal scores and reacts at 60 seconds at the north end and resets on the loop', () => {
  assert.deepEqual(match(59.999).score, [0, 0]);
  assert.deepEqual(match(60).score, [1, 0]);
  assert.deepEqual(match(60).crowdReactions, [{ start: 60, duration: 4, name: 'goal', params: { duration: 4, end: -1 } }]);
  assert.equal(match(59.999).crowdReactions.length, 0);
  assert.equal(match(64).crowdReactions.length, 0);
  assert.deepEqual(match(76).ball.position, [0, .24, 0]);
  assert.deepEqual(match(90).score, [0, 0]);
  assert.deepEqual(crossedReactions(match_cues, 59.8, 60.2), [{ name: 'goal', params: { duration: 4, end: -1 } }]);
  assert.equal(crossedReactions(match_cues, 60.2, 61).length, 0);
  assert.equal(crossedReactions(match_cues, 149.8, 150.2)[0].params.end, -1);
});

test('playback fires one goal per crossing, supports seeking, and stops after disposal', () => {
  const reactions = [], frames = []; let disposals = 0;
  const player = playback({ cues: match_cues, sample: match, draw: s => frames.push(s.time),
    getCrowd: () => ({ react: (...args) => reactions.push(args) }), dispose: () => disposals++ });
  player.update(59.9); player.update(.2); player.update(.2);
  assert.equal(reactions.length, 1); assert.equal(reactions[0][0], 'goal'); assert.equal(reactions[0][1].end, -1);
  player.update(90); assert.equal(reactions.length, 2);
  player.seek(59); player.update(1); assert.equal(reactions.length, 3);
  player.seek(70); player.update(1); assert.equal(reactions.length, 3);
  player.dispose(); player.dispose(); const count = frames.length; player.update(1);
  assert.equal(frames.length, count); assert.equal(disposals, 1);
});

test('software renderers consume state, apply the pitch frame, resize, and release roots', () => {
  const scene = new THREE.Scene();
  const event = installConcert({ scene, bearing: 17, pad: 8, tier: 'medium', width: 1024 });
  const root = scene.getObjectByName('EVT-01');
  assert.equal(root.position.y, 8); assert.equal(root.rotation.y, -17 * Math.PI / 180);
  assert.equal(root.children.filter(o => o.name === 'standing-crowd').length, 4);
  assert.equal(root.getObjectByName('concert-performer').name, 'concert-performer');
  event.seek(36); event.setTier('low', 390);
  assert.equal(root.children.filter(o => o.name === 'standing-crowd').length, 4);
  assert.equal(event.sample(36).lights.length, 8);
  root.traverse(o => { if (o.isInstancedMesh) assert.ok(o.instanceMatrix.array.every(Number.isFinite)); });
  event.dispose(); event.dispose(); assert.equal(scene.children.length, 0);
  const football = installMatch({ scene, bearing: 17, pad: 8 });
  const state = football.seek(60);
  const matchRoot = scene.getObjectByName('SPT-01');
  assert.deepEqual(matchRoot.children.filter(o => o.isInstancedMesh).map(o => o.count), [23, 23, 92]);
  const ball = matchRoot.children.find(o => !o.isInstancedMesh);
  assert.deepEqual(ball.position.toArray(), state.ball.position);
  football.dispose(); assert.equal(scene.children.length, 0);
});

test('night-show entry excludes other events and cancels a stale asynchronous load', async () => {
  const source = readFileSync(new URL('../src/main.js', import.meta.url), 'utf8');
  const section = source.slice(source.indexOf('function excludeEventsForShow()'), source.indexOf("document.querySelectorAll('#modes button')"));
  let releaseImport, stopped = 0, played = 0;
  const imported = new Promise(resolve => { releaseImport = resolve; });
  const installShows = () => ({ play() { played++; }, dispose() {} });
  const body = section.replace("await import('./shows/index.js')", 'await imported').replaceAll('import.meta.env.DEV', 'false');
  const api = new Function('imported', 'onStop', `${body}; return {startShow, stopShow};`.replace('function excludeEventsForShow()', `let shows = null, modeVersion = 0;
    const state = { matchday: true }, flood = [], scene = {}, camera = {}, renderer = {}, hero = null, bowl = { group: {} };
    const document = { querySelector: () => null }; function stopLiveClock() {} function stopEvent() { onStop(); }
    function excludeEventsForShow()`))(imported, () => stopped++);
  const pending = api.startShow();
  assert.equal(stopped, 1);
  api.stopShow(); releaseImport({ installShows }); await pending;
  assert.equal(played, 0);
  await api.startShow(); assert.equal(played, 1); assert.equal(stopped, 2);
});

function crowdHost({ hero = null, imported, scene, bowl, eventMode = 'concert', fraction = 0 }) {
  const source = readFileSync(new URL('../src/main.js', import.meta.url), 'utf8');
  const section = source.slice(source.indexOf('async function ensureCrowd()'), source.indexOf('const fpsMonitor'));
  const stop = source.slice(source.indexOf('function stopEvent()'), source.indexOf('async function startEvent('));
  const body = (section + stop).replace("await import('./people/index.js')", 'await imported').replaceAll('import.meta.env.DEV', 'false');
  return new Function('hero', 'imported', 'scene', 'bowl', 'eventMode', 'fraction', `
    let crowd = null, crowdLoading = null, liveEvent = null;
    const camera = {}, renderer = {}, tier = 'low', quality = { crowdFraction: fraction }, F = {};
    const state = { matchday: false }, eventHUD = { hidden: false };
    ${body}
    return {ensureCrowd, stopEvent, setEvent(value) { liveEvent = value; }, get crowd() { return crowd; }};
  `)(hero, imported, scene, bowl, eventMode, fraction);
}

test('event crowd uses procedural seats and its own world-space root outside the full model', async () => {
  const scene = new THREE.Scene(), bowl = { group: new THREE.Group(), seats: true }, hero = { group: new THREE.Group() };
  bowl.group.position.y = 6.12; scene.add(bowl.group, hero.group);
  const baked = new THREE.Mesh(new THREE.BoxGeometry(), new THREE.MeshBasicMaterial({ color: '#18733d' })); hero.group.add(baked);
  const baseline = baked.material.color.toArray();
  let options;
  const imported = Promise.resolve({ installSeatedCrowd(args) {
    options = args;
    const group = new THREE.Group(); group.name = 'seated-crowd';
    (args.bowlGroup || args.heroGroup).add(group);
    return { group, setFill() {}, dispose() { group.removeFromParent(); } };
  } });
  const host = crowdHost({ scene, bowl, hero, imported });
  const crowd = await host.ensureCrowd();
  assert.equal(options.bowlGroup, bowl.group);
  assert.equal(options.heroGroup, undefined);
  assert.equal(crowd.group.parent, scene);
  assert.equal(crowd.group.getWorldPosition(new THREE.Vector3()).y, 6.12);
  assert.deepEqual(hero.group.children, [baked]);
  assert.deepEqual(baked.material.color.toArray(), baseline);
  host.setEvent(installConcert({ scene, tier: 'low', width: 390 }));
  host.stopEvent();
  assert.equal(scene.getObjectByName('EVT-01'), undefined);
  assert.equal(crowd.group.parent, null);
  assert.equal(host.crowd, null);
  assert.deepEqual(hero.group.children, [baked]);
});

test('an event that stops during a crowd import leaves no late crowd root', async () => {
  const scene = new THREE.Scene(), bowl = { group: new THREE.Group(), seats: true };
  let resolve, installs = 0;
  const imported = new Promise(done => { resolve = done; });
  const host = crowdHost({ scene, bowl, imported });
  const pending = host.ensureCrowd(); host.stopEvent();
  resolve({ installSeatedCrowd() { installs++; return { setFill() {} }; } });
  await pending;
  assert.equal(installs, 0);
  assert.equal(host.crowd, null);
});

test('the landing Event dropdown lists both new events before scene data loads', () => {
  const source = readFileSync(new URL('../src/main.js', import.meta.url), 'utf8');
  const registration = source.slice(source.indexOf("for (const [mode, name] of [['concert'"), source.indexOf('\n// end event controls'));
  // Keep this registration before asynchronous boot so the tier-0 menu is complete.
  assert.ok(source.indexOf("for (const [mode, name] of [['concert'") < source.indexOf('await loadData(progress)'));
  const nodes = new Map([['#modes', { children: [], append(node) { this.children.push(node); } }], ['#landing-event', { children: [], append(node) { this.children.push(node); } }]]);
  const document = { createElement() { return { dataset: {} }; }, getElementById(id) { return nodes.get(`#${id}`); } };
  new Function('document', '$', registration)(document, selector => nodes.get(selector));
  assert.deepEqual(nodes.get('#landing-event').children.map(o => o.value), ['concert', 'football']);
  assert.deepEqual(nodes.get('#modes').children.map(b => b.dataset.mode), ['concert', 'football']);
});


test('real crowd API keeps fan positions, scale, and colors in the drawn seat frame', async () => {
  const scene = new THREE.Scene(), hero = { group: new THREE.Group() }, group = new THREE.Group();
  group.position.y = 6.12; group.rotation.y = .2; scene.add(group, hero.group);
  const seats = new THREE.InstancedMesh(new THREE.BoxGeometry(.5, .5, .5), new THREE.MeshBasicMaterial(), 4);
  seats.name = 'seats'; group.add(seats);
  const points = [[-45, 4, -60], [45, 4, -60], [-45, 24, 60], [45, 24, 60]];
  points.forEach((p, i) => seats.setMatrixAt(i, new THREE.Matrix4().makeTranslation(...p)));
  const host = crowdHost({ scene, hero, bowl: { group, seats }, fraction: 1,
    imported: Promise.resolve({ installSeatedCrowd }) });
  const crowd = await host.ensureCrowd();
  scene.updateMatrixWorld(true); group.visible = false;
  assert.equal(crowd.group.parent, scene);
  assert.equal(hero.group.children.length, 0);
  for (const mesh of crowd.group.children) {
    assert.equal(mesh.count, 4);
    assert.equal(mesh.material.isMeshBasicNodeMaterial, true);
    const origin = mesh.geometry.getAttribute('fanOrigin'), shirt = mesh.geometry.getAttribute('fanShirt');
    for (let i = 0; i < mesh.count; i++) {
      const world = new THREE.Vector3().fromBufferAttribute(origin, i).applyMatrix4(crowd.group.matrixWorld);
      assert.ok(points.some(p => world.distanceTo(new THREE.Vector3(...p).add(new THREE.Vector3(0, .02, 0)).applyMatrix4(group.matrixWorld)) < .0001));
      assert.ok([shirt.getX(i), shirt.getY(i), shirt.getZ(i)].every(v => Number.isFinite(v) && v > 0 && v <= 1));
      const matrix = new THREE.Matrix4(); mesh.getMatrixAt(i, matrix);
      assert.ok(new THREE.Vector3().setFromMatrixScale(matrix).distanceTo(new THREE.Vector3(1, 1, 1)) < .0001);
    }
  }
  host.stopEvent(); assert.equal(scene.getObjectByName('seated-crowd'), undefined);
  assert.equal(group.getObjectByName('seats'), seats);
});
