import { contactShadowBatch } from './contactShadows.js';
import * as THREE from 'three/webgpu';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { uniform, float, vec3, sin, abs, smoothstep, instanceIndex, positionLocal, positionGeometry, color } from 'three/tsl';

// Matchday crowd: Visualization only. Not a validated crowd, safety or evacuation simulation.
// Stylised low-poly figures, no real people, no text, no logos, no security detail.

const SHIRTS = [['#B92332', 0.35], ['#222222', 0.25], ['#18733D', 0.20], ['#E8E4D8', 0.20]];
const SKINS = ['#3a281e', '#4e3426', '#6b4430', '#7d5238', '#93613f', '#c28b62'];
const KENYA = { black: '#111111', red: '#BB0000', green: '#006600', white: '#FFFFFF' };

const rng = (s) => () => { s = (s + 0x6D2B79F5) | 0; let t = Math.imul(s ^ (s >>> 15), 1 | s); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };

// One box with a flat vertex colour, positioned in the figure's local frame (metres).
function part(w, h, d, x, y, z, c) {
  const g = new THREE.BoxGeometry(w, h, d); g.translate(x, y, z);
  const col = new THREE.Color(c), n = g.attributes.position.count, a = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) col.toArray(a, i * 3);
  g.setAttribute('color', new THREE.BufferAttribute(a, 3)); g.deleteAttribute('uv');
  return g;
}

// Seated fan: local +z is the way the seat faces (towards the pitch). Origin is the seat base.
const fanBody = () => mergeGeometries([
  part(0.32, 0.14, 0.42, 0, 0.53, 0.22, '#3a3a44'), // thighs
  part(0.30, 0.46, 0.14, 0, 0.27, 0.42, '#30303a'), // lower legs
  part(0.46, 0.52, 0.26, 0, 0.74, 0.02, '#ffffff'), // torso and arms, takes the shirt colour
]);
const fanHead = () => { const g = new THREE.IcosahedronGeometry(0.12, 0); g.translate(0, 1.13, 0.04); g.deleteAttribute('uv'); return g; };

// Standing player, 1.8 m, +z forward. Three parts so shirt, shorts and skin take separate instance colours.
const playerParts = () => ({
  shirt: mergeGeometries([part(0.42, 0.50, 0.24, 0, 1.2, 0, '#fff'), part(0.09, 0.46, 0.10, -0.26, 1.17, 0, '#fff'), part(0.09, 0.46, 0.10, 0.26, 1.17, 0, '#fff')]),
  shorts: part(0.40, 0.26, 0.26, 0, 0.82, 0, '#fff'),
  skin: mergeGeometries([part(0.13, 0.70, 0.15, -0.1, 0.35, 0, '#fff').toNonIndexed(), part(0.13, 0.70, 0.15, 0.1, 0.35, 0, '#fff').toNonIndexed(), (() => { const g = new THREE.IcosahedronGeometry(0.12, 0); g.translate(0, 1.66, 0); g.deleteAttribute('uv'); const n = g.attributes.position.count; g.setAttribute('color', new THREE.BufferAttribute(new Float32Array(n * 3).fill(1), 3)); return g; })()]),
});

// Kenya flag as five vertex-coloured bands (black, red, green with white fringes), 1 m wide, 2:3.
// Cloth spans x 0..1, y 0..0.667. A stick runs down the left edge when stick > 0.
function flagGeometry(stick) {
  const H = 2 / 3, bands = [[KENYA.black, 0.27], [KENYA.white, 0.04], [KENYA.red, 0.38], [KENYA.white, 0.04], [KENYA.green, 0.27]];
  const pos = [], col = [], idx = []; let y = H;
  for (const [c, f] of bands) {
    const h = f * H, k = new THREE.Color(c), b = pos.length / 3;
    // 8 columns so the wave bends the cloth smoothly
    for (let i = 0; i <= 8; i++) { const x = i / 8; pos.push(x, y, 0, x, y - h, 0); col.push(k.r, k.g, k.b, k.r, k.g, k.b); }
    for (let i = 0; i < 8; i++) { const a = b + i * 2; idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); }
    y -= h;
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3)); g.setIndex(idx); g.computeVertexNormals();
  if (stick <= 0) return g;
  return mergeGeometries([g.toNonIndexed(), part(0.012, stick + H, 0.012, -0.006, (H - stick) / 2, 0, '#8a6a40').toNonIndexed()].map((x) => { x.deleteAttribute('uv'); return x; }));
}

/**
 * Seated crowd and players. Visualization only.
 * @param {object} o
 * @param {THREE.InstancedMesh} o.seats  bowl.seats (per-instance seat matrices; seats face the pitch along local +z)
 * @param {number} [o.occupancy=0.9]    share of seats with a fan
 * @param {number} [o.seed=1]
 * @param {boolean} [o.players=true]    add 22 players, 2 of them goalkeepers, and 3 officials
 * @param {{centre?:THREE.Vector3|number[], bearing?:number, group?:THREE.Object3D}} [o.pitch]  centre in crowd-group space (default 0,0,0), bearing in degrees (as buildPitch)
 * @param {number} [o.fraction=1]       extra thinning for weak devices (0..1); fraction 0.5 draws half the fans
 * @returns {{group:THREE.Group, update:(t:number, night:number)=>void}}
 */
export function buildCrowd({ seats, occupancy = 0.9, seed = 1, players = true, pitch, fraction = 1 } = {}) {
  const group = new THREE.Group(); group.name = 'crowd'; group.userData.claim = 'Visualization';
  const rand = rng(seed >>> 0 || 1);
  const uT = uniform(0), uCheer = uniform(0), uNight = uniform(0);
  const noop = () => {};
  if (fraction <= 0 || occupancy <= 0 || !seats?.instanceMatrix) return { group, update: noop };
  // The crowd sits in the same frame as the seats: follow the bowl group offset (the lead may still set it).
  if (seats.parent) group.position.copy(seats.parent.position);

  // ---------- choose occupied seats ----------
  const src = seats.instanceMatrix.array, nSeats = seats.count, keep = Math.min(1, Math.max(0, occupancy * fraction));
  const pick = new Uint32Array(nSeats); let n = 0;
  for (let i = 0; i < nSeats; i++) if (rand() < keep) pick[n++] = i;
  if (!n) return { group, update: noop };

  const hash = float(instanceIndex).mul(12.9898).sin().mul(43758.5453).fract(); // 0..1 per instance
  const ph = hash.mul(6.2832);

  // ---------- fans: bodies and heads share the matrices, so they bob together ----------
  const bodyGeo = fanBody(), headGeo = fanHead();
  const bob = (heightW) => {
    const calm = sin(uT.mul(hash.mul(1.2).add(1.4)).add(ph)).mul(0.012);
    const jump = abs(sin(uT.mul(hash.mul(3).add(5)).add(ph))).mul(0.10).mul(uCheer).mul(smoothstep(0.55, 0.75, hash));
    return calm.add(jump).mul(heightW);
  };
  const bodyMat = new THREE.MeshStandardNodeMaterial({ vertexColors: true, roughness: 0.9 });
  bodyMat.positionNode = positionLocal.add(vec3(0, bob(smoothstep(0.45, 0.95, positionGeometry.y)), 0));
  const headMat = new THREE.MeshStandardNodeMaterial({ roughness: 0.8 });
  headMat.positionNode = positionLocal.add(vec3(0, bob(float(1)), 0));
  const bodies = new THREE.InstancedMesh(bodyGeo, bodyMat, n), heads = new THREE.InstancedMesh(headGeo, headMat, n);
  bodies.name = 'crowd-bodies'; heads.name = 'crowd-heads';
  const c = new THREE.Color(), tot = SHIRTS.reduce((s, x) => s + x[1], 0);
  for (let j = 0; j < n; j++) {
    const s = pick[j] * 16; bodies.instanceMatrix.array.set(src.subarray(s, s + 16), j * 16);
    let r = rand() * tot, hex = SHIRTS[0][0]; for (const [h, w] of SHIRTS) { if ((r -= w) <= 0) { hex = h; break; } }
    c.set(hex).multiplyScalar(0.85 + rand() * 0.3); bodies.setColorAt(j, c);
    c.set(SKINS[Math.min(SKINS.length - 1, Math.floor(rand() ** 1.6 * SKINS.length))]); heads.setColorAt(j, c);
  }
  heads.instanceMatrix.array.set(bodies.instanceMatrix.array);
  for (const m of [bodies, heads]) { m.instanceMatrix.needsUpdate = true; m.instanceColor.needsUpdate = true; m.frustumCulled = false; m.castShadow = false; m.receiveShadow = false; group.add(m); }

  // ---------- flags ----------
  const flagMat = new THREE.MeshStandardNodeMaterial({ vertexColors: true, roughness: 0.8, side: THREE.DoubleSide });
  flagMat.positionNode = positionLocal.add(vec3(0, sin(positionGeometry.x.mul(7).add(uT.mul(3.5)).add(ph)).mul(positionGeometry.x).mul(0.05), 0));
  const M = new THREE.Matrix4(), T = new THREE.Matrix4(), S = new THREE.Matrix4(), SM = new THREE.Matrix4();
  const flagSet = (geo, count, place) => {
    if (count < 1) return null;
    const mesh = new THREE.InstancedMesh(geo, flagMat, count);
    for (let k = 0; k < count; k++) { SM.fromArray(src, pick[Math.floor(rand() * n)] * 16); place(k, SM); mesh.setMatrixAt(k, M); }
    mesh.instanceMatrix.needsUpdate = true; mesh.frustumCulled = false; group.add(mesh); return mesh;
  };
  // a few large flat flags, held up in front of the lower rows (3 x 2 m)
  const nBig = Math.min(14, Math.round(n / 3500));
  const big = flagSet(flagGeometry(0), nBig, (k, sm) => { M.copy(sm).multiply(T.makeTranslation(-1.5, 1.2 + rand() * 0.5, 0.25)).multiply(S.makeScale(3, 3, 1)); });
  if (big) big.name = 'crowd-flags-large';
  // scattered small hand flags (about 1 in 70 fans)
  const nHand = Math.round(n / 70);
  const hand = flagSet(flagGeometry(0.55), nHand, (k, sm) => { M.copy(sm).multiply(T.makeTranslation(0.18 + rand() * 0.1, 1.0 + rand() * 0.25, 0.12)).multiply(S.makeScale(0.45, 0.45, 0.45)); });
  if (hand) hand.name = 'crowd-flags-hand';

  // ---------- phone lights at night (about 3% of fans) ----------
  const nPh = Math.round(n * 0.03);
  const phoneMat = new THREE.MeshBasicNodeMaterial();
  phoneMat.colorNode = color('#d6ecff').mul(uNight.mul(2.6));
  phoneMat.positionNode = positionLocal.add(vec3(0, bob(float(1)), 0));
  const phones = new THREE.InstancedMesh(new THREE.BoxGeometry(0.07, 0.12, 0.012), phoneMat, Math.max(1, nPh));
  phones.name = 'crowd-phones';
  for (let k = 0; k < nPh; k++) { SM.fromArray(src, pick[Math.floor(rand() * n)] * 16); M.copy(SM).multiply(T.makeTranslation((rand() - 0.5) * 0.16, 0.98 + rand() * 0.2, 0.36)); phones.setMatrixAt(k, M); }
  phones.count = nPh; phones.instanceMatrix.needsUpdate = true; phones.frustumCulled = false; phones.visible = false; group.add(phones);

  // ---------- players and officials ----------
  let roster = [], pm = null;
  if (players && pitch) {
    const centre = pitch.centre ? (Array.isArray(pitch.centre) ? pitch.centre : pitch.centre.toArray()) : [0, 0, 0];
    const bearing = pitch.bearing ?? 0;
    const pg = new THREE.Group(); pg.name = 'crowd-players'; pg.position.set(centre[0], centre[1] + 0.08, centre[2]); pg.rotation.y = -(bearing * Math.PI) / 180;
    // loose 4-4-2; pitch-local x across (68 m), z along (105 m); home defends -z and faces +z
    const form = [[0, -0.47], [-22, -0.31], [-8, -0.33], [8, -0.33], [22, -0.31], [-24, -0.17], [-8, -0.19], [8, -0.19], [24, -0.17], [-7, -0.05], [8, -0.07]];
    const kit = { home: ['#B92332', '#111111'], away: ['#F2F0EA', '#18733D'], gkH: ['#E08A1E', '#111111'], gkA: ['#2F6FB5', '#111111'], off: ['#C9D13A', '#111111'] };
    form.forEach(([x, z], i) => roster.push({ x, z: z * 105, yaw: 0, k: i ? kit.home : kit.gkH }));
    form.forEach(([x, z], i) => roster.push({ x: -x, z: -z * 105, yaw: Math.PI, k: i ? kit.away : kit.gkA }));
    roster.push({ x: 4, z: 3, yaw: 0.6, k: kit.off, o: 1 }, { x: 35.5, z: 10, yaw: -Math.PI / 2, k: kit.off, o: 1 }, { x: -35.5, z: -10, yaw: Math.PI / 2, k: kit.off, o: 1 });
    for (const p of roster) {
      const gk = p.k === kit.gkH || p.k === kit.gkA;
      Object.assign(p, { bx: p.x, bz: p.z, ax: gk ? 1.2 : p.o ? 0.5 : 2.5 + rand() * 3, az: gk ? 2 : p.o ? 8 : 3 + rand() * 5, wx: 0.04 + rand() * 0.05, wz: 0.03 + rand() * 0.05, px: rand() * 6.28, pz: rand() * 6.28, skin: SKINS[Math.floor(rand() * 4)] });
    }
    const parts = playerParts(), mats = () => new THREE.MeshStandardNodeMaterial({ vertexColors: true, roughness: 0.7 });
    pm = {};
    for (const key of ['shirt', 'shorts', 'skin']) {
      const m = new THREE.InstancedMesh(parts[key], mats(), roster.length); m.name = 'player-' + key; m.frustumCulled = false; m.castShadow = true;
      roster.forEach((p, i) => { c.set(key === 'shirt' ? p.k[0] : key === 'shorts' ? p.k[1] : p.skin); m.setColorAt(i, c); });
      m.instanceColor.needsUpdate = true; pg.add(m); pm[key] = m;
    }
    group.add(pg);
  }

  const q = new THREE.Quaternion(), yAx = new THREE.Vector3(0, 1, 0), pv = new THREE.Vector3(), one = new THREE.Vector3(1, 1, 1);
  const sm = (a, b, x) => { const u = Math.min(1, Math.max(0, (x - a) / (b - a))); return u * u * (3 - 2 * u); };
  let fanContact = null, playerContact = null;
  function setContactShadows(enabled) {
    if (enabled && !fanContact) {
      fanContact = contactShadowBatch(n); group.add(fanContact.mesh);
      for (let i = 0; i < n; i++) {
        SM.fromArray(src, pick[i] * 16);
        fanContact.set(i, SM, .55, .65);
      }
      fanContact.finish(n);
      if (pm) {
        playerContact = contactShadowBatch(roster.length);
        pm.shirt.parent.add(playerContact.mesh);
      }
    }
    fanContact?.setEnabled(enabled); playerContact?.setEnabled(enabled);
  }
  function update(t = 0, night = 0) {
    uT.value = t;
    uCheer.value = sm(0.55, 0.9, Math.sin(t * 0.21) * 0.6 + Math.sin(t * 0.073 + 1.3) * 0.5); // now and then the stands lift
    uNight.value = sm(0.5, 0.7, night); phones.visible = night > 0.5 && nPh > 0;
    if (pm) {
      roster.forEach((p, i) => {
        const x = p.bx + Math.sin(t * p.wx + p.px) * p.ax, z = p.bz + Math.cos(t * p.wz + p.pz) * p.az;
        q.setFromAxisAngle(yAx, p.yaw + Math.sin(t * 0.07 + p.px) * 0.4);
        M.compose(pv.set(x, Math.abs(Math.sin(t * 2.2 + p.px)) * 0.03, z), q, one);
        pm.shirt.setMatrixAt(i, M); pm.shorts.setMatrixAt(i, M); pm.skin.setMatrixAt(i, M);
        if (playerContact?.enabled) {
          M.elements[13] = 0; playerContact.set(i, M, .75, .65);
        }
      });
      if (playerContact?.enabled) playerContact.finish(roster.length);
      pm.shirt.instanceMatrix.needsUpdate = pm.shorts.instanceMatrix.needsUpdate = pm.skin.instanceMatrix.needsUpdate = true;
    }
  }
  update(0, 0);
  const calls = 2 + (big ? 1 : 0) + (hand ? 1 : 0) + 1 + (pm ? 3 : 0);
  group.userData.stats = { fans: n, seats: nSeats, largeFlags: nBig, handFlags: nHand, phones: nPh, figures: roster.length, drawCalls: calls };
  return { group, update, setContactShadows };
}
