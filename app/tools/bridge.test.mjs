import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import * as THREE from 'three/webgpu';
import { Timeline } from '../src/shows/timeline.js';
import { fallbackFacadeLines, padY } from '../src/shows/geometry.js';
import { showState, ribColor, linearColor } from '../src/shows/state.js';
import { exportModule } from '../src/bridge/export.js';
import { packChannels, unpackChannel } from '../src/bridge/format.js';
import { fanPose, fanLayout, reactionAt, occupancyOrder, selectSeats } from '../src/people/model.js';
import { installShows } from '../src/shows/index.js';
import { generateSeats } from '../src/people/seats.js';
import { buildBowl } from '../src/world/bowl.js';
import { installSeatedCrowd } from '../src/people/index.js';
import { writeExport, parseArgs, loadGeometry, loadCrowdSeats } from './export_bridge.mjs';

const data = fallbackFacadeLines();
// Captured from the original installShows before the refactor. No viewer, 480 drones.
const golden = [
  [0, false, [0,0,0], [0,0,0]], [2, false, [0,0,0], [0,0,0]], [8, false, [0,0,0], [0,0,0]],
  [12, true, [-16.149999618530273,1.5,-155], [.012000000104308128,.012000000104308128,.012000000104308128]],
  [20, true, [-60,130,-140], [.012000000104308128,.012000000104308128,.012000000104308128]],
  [30, true, [.001156577724032104,129.99925231933594,-140], [1,1,1]],
  [44, false, [0,0,0], [0,0,0]], [50, false, [0,0,0], [0,0,0]], [58, false, [0,0,0], [0,0,0]], [60, false, [0,0,0], [0,0,0]],
];
test('software showState preserves captured original show values', () => {
  for (const [t, visible, position, rgb] of golden) {
    const state = showState(new Timeline().sample(t), t, data, { drones: 480 });
    assert.equal(state['SHW-03'].visible, visible);
    if (visible) { assert.deepEqual(state['SHW-03'].position.slice(0,3).map(Math.fround), position); assert.deepEqual(state['SHW-03'].rgb.slice(0,3).map(Math.fround), rgb); }
    assert.deepEqual(state['SHW-01'].rgb.slice(0,6), t === 0 ? [1,1,1,0,0,0] : t >= 58 ? [0,0,0,0,0,0] : [1,1,1,1,1,1]);
  }
});

test('software floodlight state matches the original inline formula for every lamp', () => {
  for (const mode of ['sequence', 'flash', 'on']) for (const t of [0, .125, .126, 1, 2, 7.99, 8, 10]) {
    const cues = [{ module: 'SHW-01', params: { mode, color: '#b92332' }, localTime: t }];
    const state = showState(cues, t, data, { drones: 200 })['SHW-01'];
    const color = new THREE.Color('#b92332').toArray();
    const original = data.floodlights.map((_, i) => mode === 'flash' ? +(Math.sin(t * Math.PI * 8) >= 0) : mode === 'sequence' ? +(i / data.floodlights.length <= Math.min(1,t / 8)) : 1);
    assert.deepEqual(state.intensity, original);
    state.rgb.forEach((v, i) => assert.ok(Math.abs(v - color[i % 3] * original[Math.floor(i / 3)]) < 1e-9));
  }
});

test('software per-rib RGB agrees with documented TSL step/mix formula', () => {
  const step = (a,b) => +(b >= a), mix = (a,b,t) => a * (1-t) + b*t;
  for (const angle of [0,.299,.3,.35,.65,.7,.99]) for (const index of [0,5,49]) for (const mode of [0,1,2,3]) for (const t of [0,2.5,44,58]) {
    const band = [0,1,2].map(() => mix(.012,1,step(.3,angle)));
    const red = band.map((v,k) => mix(v,[1,.015,.025][k],step(.35,angle)));
    const edge = red.map(v => mix(v,1,step(.65,angle)));
    const flag = edge.map((v,k) => mix(v,[.01,.65,.08][k],step(.7,angle)));
    const color = flag.map(v => mix(1,v,step(.5,mode)));
    const pulse = mix(mix(1,step(.65,Math.sin(index*.45-t*4))*.9+.1,step(1.5,mode)),Math.sin(angle*Math.PI*8-t*2)*.45+.55,step(2.5,mode));
    const tint = [.2,.4,.6];
    ribColor(angle,index,mode,t,tint).forEach((v,k) => assert.ok(Math.abs(v-color[k]*pulse*tint[k]*5) < 1e-12));
  }
});

test('software app instance buffers consume the shared state, including fixed viewer', () => {
  const scene = new THREE.Scene(), camera = new THREE.PerspectiveCamera(); camera.position.set(100,200,300);
  const shows = installShows({ scene, camera }); shows.play('night_show'); shows.timeline.seek(25); shows.update(0);
  const state = showState(new Timeline().sample(25),25,data,{ drones: 480 },{ viewer: camera.position });
  assert.deepEqual(Array.from(scene.getObjectByName('SHW-03').instanceColor.array), state['SHW-03'].rgb.map(Math.fround));
  const matrix = new THREE.Matrix4();
  for (let i = 0; i < 480; i++) { scene.getObjectByName('SHW-03').getMatrixAt(i,matrix); assert.deepEqual(matrix.elements.slice(12,15),state['SHW-03'].position.slice(i*3,i*3+3).map(Math.fround)); }
  shows.dispose();
});

test('software binary file round-trip, frame counts and byte offsets', async () => {
  const out = await mkdtemp(join(tmpdir(),'talanta-bridge-test-'));
  for (const module of ['SHW-01','SHW-02','SHW-03']) {
    const exported = exportModule({ module,data,fps:24,duration:49/24,start:12,drones:200,pad:padY });
    const sizes = await writeExport(out,exported);
    const header = JSON.parse(await readFile(join(out,`${module}.json`),'utf8'));
    const bytes = await readFile(join(out,header.binary));
    assert.equal(header.frame_count,49); assert.equal(header.fps,24); assert.equal(sizes.bin_bytes,bytes.length);
    let offset = 0;
    for (const channel of header.channels) {
      assert.equal(channel.offset,offset); offset += channel.length*4;
      assert.deepEqual(unpackChannel(bytes,channel),unpackChannel(exported.bytes,channel));
      if (channel.name !== 'visible') {
        const first = showState(new Timeline().sample(12),12,data,{ drones:200 })[module][channel.name];
        assert.deepEqual(unpackChannel(bytes,channel).slice(0,first.length),first.map(Math.fround));
      }
    }
    assert.equal(offset,bytes.length);
    if (module === 'SHW-03') { assert.equal(header.static.drone_count,200); assert.equal(header.channels.find(c => c.name === 'position').length,49*200*3); }
  }
  const packed = packChannels([{name:'test',components:2,values:[1,-2,Math.PI]}]);
  assert.deepEqual(Array.from(packed.bytes.slice(0,4)),[0,0,128,63]);
  assert.deepEqual(unpackChannel(packed.bytes,packed.channels[0]),[1,-2,Math.fround(Math.PI)]);
  assert.throws(() => unpackChannel(packed.bytes,{ dtype:'float32', offset:4,length:100 }));
});

test('software crowd attributes match the live instance attributes and reaction semantics', async () => {
  const seats = [0,1,2,3].map((_,i) => ({x:Math.cos(i*Math.PI/2)*50,y:10,z:Math.sin(i*Math.PI/2)*50,facing_deg:0,tier:0,row:0}));
  const camera = new THREE.PerspectiveCamera(), scene = new THREE.Scene();
  const crowd = installSeatedCrowd({scene,camera,seats,quality:{width:1024}}); await crowd.ready;
  const { fans, perimeter } = fanLayout(seats), order = occupancyOrder(seats);
  const mesh = crowd.group.children[0];
  order.forEach((seat,j) => { for (const [key,attr] of [['phase','fanPhase'],['angle','fanAngle'],['end','fanEnd']]) assert.equal(fans[seat][key],mesh.geometry.attributes[attr].array[j]); });
  for (const name of ['cheer','goal','wave','scarves','phones']) {
    crowd.update(0,5); crowd.react(name,{duration:8,end:'away',speed:12});
    const cues = [{name,start:5,duration:8,params:{end:'away',speed:12}}];
    const u = reactionAt(cues,6,{perimeter,night:1});
    for (const fan of fans) {
      const pose = fanPose(fan,u,6);
      if (name === 'cheer') assert.equal(pose.lift,1);
      if (name === 'goal') assert.equal(pose.lift,+(fan.end === -1));
      if (name === 'scarves') { assert.equal(pose.scarf,1); assert.equal(pose.raised,1); }
      if (name === 'phones') assert.equal(pose.phone,1);
      if (name !== 'phones') assert.equal(fanPose(fan,u,13).lift,0);
    }
  }
  assert.equal(fanPose({phase:0,angle:0,end:1},{wave:1},0).lift,1);
  assert.equal(fanPose({phase:0,angle:Math.PI,end:1},{wave:1},0).lift,0);
  assert.equal(fanPose(fans[0],reactionAt([{name:'phones',start:0,duration:1,params:{}}],20,{night:0}),20).phone,0);
  const exported = exportModule({module:'PPL-02',seats,fps:24,duration:2,fill:.5,cues:[],night:true,pad:padY});
  assert.equal(exported.header.static.selected_count,2);
  assert.deepEqual(unpackChannel(exported.bytes,exported.header.channels.find(c => c.name === 'fan_phase')),fans.map(f => f.phase));
  crowd.dispose();
});

test('software exporter chooses app fallback and generates bowl parent coordinates without document', async () => {
  const geometry = await loadGeometry(); assert.ok(geometry.geometrySource.startsWith('fallback: invalid'));
  assert.equal(typeof globalThis.document, 'undefined');
  const seats = await loadCrowdSeats(); assert.equal(seats.length, 56972); assert.equal(seats[0].tier,0); assert.equal(seats[0].row,120);
  console.log(`SOFTWARE crowd seats=${seats.length} first_y=${seats[0].y}`);
});

test('software CLI rejects invalid inputs and preserves requested sampling', () => {
  const options = parseArgs(['--module','SHW-03','--out','/tmp/bridge','--fps','30','--drones','123','--duration','1.1','--viewer','1,2,3']);
  const exported = exportModule({...options,data}); assert.equal(exported.header.frame_count,33); assert.equal(exported.header.fps,30); assert.equal(exported.header.static.drone_count,123); assert.equal(exported.header.static.facing,'fixed-viewer');
  assert.throws(() => parseArgs(['--module','SHW-03','--out','/tmp/bridge','--viewer','1,2']));
  assert.throws(() => exportModule({...options,data,fps:0}));
});


test('software generateSeats matches every bowl instance position and facing', async () => {
  const { features } = JSON.parse(await readFile(new URL('../public/data/manifest.json', import.meta.url), 'utf8'));
  const context = Object.fromEntries(['fillRect', 'clearRect', 'beginPath', 'moveTo', 'bezierCurveTo',
    'closePath', 'fill', 'save', 'clip', 'ellipse', 'restore', 'quadraticCurveTo', 'stroke']
    .map(name => [name, () => {}]));
  context.createLinearGradient = () => ({ addColorStop() {} });
  const originalDocument = Object.getOwnPropertyDescriptor(globalThis, 'document');
  let bowl;
  try {
    globalThis.document = { createElement(name) { assert.equal(name, 'canvas'); return { getContext: () => context }; } };
    bowl = buildBowl(features, { tier: 'low' });
  } finally {
    if (originalDocument) Object.defineProperty(globalThis, 'document', originalDocument);
    else delete globalThis.document;
  }
  try {
    const seats = generateSeats(features), matrix = new THREE.Matrix4();
    assert.equal(seats.length, bowl.seats.count);
    let maxPositionError = 0, maxFacingError = 0;
    for (let i = 0; i < seats.length; i++) {
      bowl.seats.getMatrixAt(i, matrix);
      const e = matrix.elements, seat = seats[i];
      const distance = Math.hypot(seat.x - e[12], seat.y - e[13], seat.z - e[14]);
      const facing = Math.atan2(e[8], e[10]) * 180 / Math.PI;
      const angleError = Math.abs(((seat.facing_deg - facing + 540) % 360) - 180);
      maxPositionError = Math.max(maxPositionError, distance);
      maxFacingError = Math.max(maxFacingError, angleError);
    }
    console.log(`SOFTWARE seat parity count=${seats.length} max_position_error_m=${maxPositionError} max_facing_error_deg=${maxFacingError}`);
    assert.ok(maxPositionError <= 1e-4, `Seat position difference ${maxPositionError} m exceeds 1e-4 m`);
    assert.ok(maxFacingError <= 1e-4, `Seat facing difference ${maxFacingError} degrees exceeds 1e-4 degrees`);
  } finally {
    bowl.group.traverse(o => { o.geometry?.dispose(); if (Array.isArray(o.material)) o.material.forEach(m => m.dispose()); else o.material?.dispose(); });
  }
});


test('software crowd seat channels survive a binary file round-trip', async () => {
  const seats = await loadCrowdSeats(), fill = .37, width = 390;
  const { fans } = fanLayout(seats), order = occupancyOrder(seats);
  const selected = selectSeats(seats, fill, width, order);
  const cues = [{ name: 'wave', start: 0, duration: 2, params: { speed: 12 } }];
  const exported = exportModule({ module: 'PPL-02', seats, fps: 24, duration: 2, fill, width, cues, pad: padY });
  const out = await mkdtemp(join(tmpdir(), 'talanta-bridge-seat-roundtrip-'));
  await writeExport(out, exported);
  const header = JSON.parse(await readFile(join(out, 'PPL-02.json'), 'utf8'));
  const bytes = await readFile(join(out, header.binary));
  const expected = {
    seat_position: { components: 3, values: seats.flatMap(s => [s.x, s.y, s.z]) },
    seat_facing_deg: { components: 1, values: seats.map(s => s.facing_deg) },
    seat_tier: { components: 1, values: seats.map(s => s.tier) },
    seat_row: { components: 1, values: seats.map(s => s.row) },
    occupancy_order: { components: 1, values: order },
    selected_seats: { components: 1, values: selected },
    fan_phase: { components: 1, values: fans.map(f => f.phase) },
    fan_wave_angle: { components: 1, values: fans.map(f => f.angle) },
    fan_end: { components: 1, values: fans.map(f => f.end) },
    fan_shirt_index: { components: 1, values: fans.map(f => f.shirt) },
  };
  assert.equal(header.static.seat_count, seats.length);
  assert.equal(header.static.selected_count, selected.length);
  assert.equal(header.frame_count, 48); assert.equal(header.fps, 24);
  assert.deepEqual(header.static.reaction_cues, cues);
  assert.ok(Object.entries(header.static).every(([key, value]) => key === 'reaction_cues' || !Array.isArray(value)));
  assert.equal(header.channels.length, Object.keys(expected).length);
  let offset = 0;
  for (const channel of header.channels) {
    const source = expected[channel.name];
    assert.ok(source, `Unexpected channel ${channel.name}`);
    assert.equal(channel.dtype, 'float32'); assert.equal(channel.components, source.components);
    assert.equal(channel.offset, offset); assert.equal(channel.length, source.values.length);
    const actual = unpackChannel(bytes, channel);
    assert.deepEqual(actual, source.values.map(Math.fround));
    if (['occupancy_order', 'selected_seats', 'seat_tier', 'seat_row', 'fan_end', 'fan_shirt_index'].includes(channel.name)) assert.deepEqual(actual, source.values);
    offset += channel.length * 4;
  }
  assert.equal(offset, bytes.length);
  assert.ok(Buffer.byteLength(JSON.stringify(header)) < 10000);
});
