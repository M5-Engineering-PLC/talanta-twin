import { pathAt } from './state.js';

// Fictional match choreography in pitch-local metres. Each carry keeps the ball
// 0.8 m ahead of its carrier; pass endpoints coincide with the next receiver.
const carries = [
  { start: 30, end: 35, owner: 7, from: [7, -20], to: [14, -25] },
  { start: 37, end: 43, owner: 9, from: [5, -28], to: [-5, -34] },
  { start: 45, end: 51, owner: 10, from: [-12, -38], to: [-7, -41] },
  { start: 53, end: 59.2, owner: 9, from: [2, -44], to: [0, -48] },
];
const passes = [
  { start: 35, end: 37, from: [14, -25], to: [5, -28], receiver: 9 },
  { start: 43, end: 45, from: [-5, -34], to: [-12, -38], receiver: 10 },
  { start: 51, end: 53, from: [-7, -41], to: [2, -44], receiver: 9 },
];
const point = (time, x, z) => ({ time, position: [x, .12, z] });
const relative = (path, time) => ({ time, position: pathAt(path, time) });

const pathCache = new WeakMap();
export function attackPaths(data) {
  if (pathCache.has(data)) return pathCache.get(data);
  const paths = new Map();
  const definitions = {
    7: [point(30,7,-19.2), point(35,14,-24.2), point(37,15,-25), point(60,8,-38)],
    9: [point(37,5,-27.2), point(43,-5,-33.2), point(53,2,-43.2), point(59.2,0,-47.2), point(64,1,-47)],
    10: [point(45,-12,-37.2), point(51,-7,-40.2), point(60,-5,-43)],
    14: [point(35,11,-28), point(43,0,-36), point(53,1,-46), point(60,3,-48)],
    16: [point(35,4,-30), point(45,-9,-39), point(53,-4,-44), point(60,-2,-49)],
  };
  for (const [id, keys] of Object.entries(definitions)) {
    const base = data.playerPaths[Number(id)].keys;
    paths.set(Number(id), [relative(base,24), ...keys, relative(base,76)]);
  }
  const referee = [relative(data.refereePath,24), point(30,-4,-12), point(45,-7,-25), point(60,-6,-37), relative(data.refereePath,76)];
  const result = { players: paths, referee }; pathCache.set(data, result); return result;
}
const blend = (a,b,u) => a.map((x,i) => x+(b[i]-x)*u);
const xy = a => [a[0], .24, a[1]];
export function attackBall(time) {
  const carry = carries.find(p => time >= p.start && time < p.end);
  if (carry) {
    const u = (time - carry.start) / (carry.end - carry.start), t = u*u*(3-2*u);
    return { position: xy(blend(carry.from, carry.to, t)), action: 'carry', owner: carry.owner };
  }
  const pass = passes.find(p => time >= p.start && time < p.end);
  if (pass) {
    const u = (time - pass.start) / (pass.end - pass.start);
    const p = xy(blend(pass.from, pass.to, u)); p[1] += .2 * Math.sin(Math.PI*u);
    return { position: p, action: 'pass', owner: null, receiver: pass.receiver };
  }
  if (time >= 59.2 && time < 60) {
    const u=(time-59.2)/.8, p=xy(blend([0,-48],[0,-52.5],u)); p[1]=.24+.86*u;
    return { position:p, action:'shot', owner:null };
  }
  if (time >= 60 && time < 60.5) {
    const u=(time-60)/.5;
    return { position:[0,1.1-.1*u,-52.50001-.89999*u], action:'goal', owner:null };
  }
  return null;
}
