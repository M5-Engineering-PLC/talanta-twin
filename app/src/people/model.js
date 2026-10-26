// Visualization only. These functions describe animation, not human behavior.
export const clampFill = (value) => Number.isFinite(value) ? Math.min(1, Math.max(0, value)) : 0;
export const drawLimit = (count, width) => Math.min(count, width < 768 ? 15000 : count);
export const waveDistance = (time, speed, perimeter) => ((time * speed) % perimeter + perimeter) % perimeter;
export function occupancyOrder(seats) {
  // Nearby seats share a block score. The smaller term breaks ties within blocks.
  return seats.map((seat, i) => {
    const block = Math.floor((Math.atan2(seat.z, seat.x) + Math.PI) * 20) + Math.floor(seat.row / 3) * 131 + seat.tier * 997;
    const hash = (n) => { const v = Math.sin(n * 127.1 + 311.7) * 43758.5453; return v - Math.floor(v); };
    return { i, score: hash(block) * 0.92 + hash(i) * 0.08 };
  }).sort((a, b) => a.score - b.score).map(({ i }) => i);
}
export function selectSeats(seats, fraction, width = 1024, order = occupancyOrder(seats)) {
  const occupied = order.slice(0, Math.round(seats.length * clampFill(fraction)));
  const count = drawLimit(occupied.length, width);
  // Sample across the occupied places rather than removing entire sections on phones.
  return Array.from({ length: count }, (_, i) => occupied[Math.floor(i * occupied.length / count)]);
}

// CPU mirror of people/index.js TSL animation. All values use parent-local metres.
// elapsed=max(0,t-start), active=(elapsed<duration), travel=elapsed*speed/perimeter*2*pi.
// delta=acos(clamp(cos(angle-travel),-1,1)), wave=1-smoothstep(.06,.20,delta).
// lift=max(wave*waveFlag,cheer,goal*step(0,fan.end*end))*active.
// scarf=scarves*active, phone=phones*night, raised=max(lift,scarf).
// bob=.012*sin(t*1.7+phase), turn=.035*sin(t*.7+phase).
export function fanPose(fan, reactionState, t) {
  const u = { start: 0, duration: 8, speed: 12, perimeter: 600, end: 1,
    wave: 0, cheer: 0, goal: 0, scarves: 0, phones: 0, night: 0, ...reactionState };
  const elapsed = Math.max(0, t - u.start), active = +(elapsed < u.duration);
  const delta = Math.acos(Math.max(-1, Math.min(1, Math.cos(fan.angle - elapsed * u.speed / u.perimeter * Math.PI * 2))));
  const x = Math.max(0, Math.min(1, (delta - .06) / .14));
  const wave = (1 - x * x * (3 - 2 * x)) * u.wave;
  const lift = Math.max(wave, u.cheer, u.goal * +(fan.end * u.end >= 0)) * active;
  const scarf = u.scarves * active, phone = u.phones * u.night;
  return { lift, raised: Math.max(lift, scarf), scarf, phone,
    bob: Math.sin(t * 1.7 + fan.phase) * .012, turn: Math.sin(t * .7 + fan.phase) * .035 };
}

// Reproduces accept()'s representative-row arc mapping, including the closing edge.
export function fanLayout(seats) {
  const tau = Math.PI * 2;
  const ring = seats.filter(s => s.tier === seats[0]?.tier && s.row === seats[0]?.row)
    .map(s => ({ ...s, angle: (Math.atan2(s.z, s.x) + tau) % tau })).sort((a, b) => a.angle - b.angle);
  const distances = [0];
  for (let i = 0; i < ring.length; i++) {
    const next = ring[(i + 1) % ring.length];
    distances.push(distances[i] + Math.hypot(next.x - ring[i].x, next.z - ring[i].z));
  }
  const perimeter = distances.at(-1) || 600;
  const waveAngle = angle => {
    if (ring.length < 2) return angle;
    if (angle < ring[0].angle) angle += tau;
    let lo = 0, hi = ring.length;
    while (lo + 1 < hi) { const mid = (lo + hi) >> 1; if (ring[mid].angle <= angle) lo = mid; else hi = mid; }
    const end = hi === ring.length ? ring[0].angle + tau : ring[hi].angle;
    return (distances[lo] + (distances[hi] - distances[lo]) * (angle - ring[lo].angle) / (end - ring[lo].angle)) / perimeter * tau;
  };
  const fans = seats.map((seat, index) => {
    const end = seat.z >= 0 ? 1 : -1;
    const rand = (Math.sin(index * 17.13) * 43758.5 % 1 + 1) % 1;
    return { phase: Math.fround(rand * tau), angle: Math.fround(waveAngle((Math.atan2(seat.z, seat.x) + tau) % tau)), end,
      shirt: rand < .72 ? (end > 0 ? 0 : 1) : rand < .88 ? 2 : 3 };
  });
  return { perimeter, fans };
}

// A cue calls react(name,params) at start. Phones persist until the next phone cue.
// Other reactions replace one another, exactly as react() does in the app.
export function reactionAt(cues, t, { perimeter = 600, night = 0 } = {}) {
  const u = { start: 0, duration: 8, speed: 12, perimeter, night, end: 1, wave: 0, cheer: 0, goal: 0, scarves: 0, phones: 0 };
  for (const cue of cues.map((c, i) => ({ ...c, order: i })).sort((a, b) => a.start - b.start || a.order - b.order)) {
    if (cue.start > t) break;
    const params = cue.params ?? {};
    if (cue.name === 'phones') { u.phones = params.on === false ? 0 : 1; continue; }
    if (!['wave', 'cheer', 'goal', 'scarves'].includes(cue.name)) throw new Error(`Unknown crowd reaction: ${cue.name}`);
    for (const key of ['wave', 'cheer', 'goal', 'scarves']) u[key] = +(key === cue.name);
    u.start = cue.start; u.duration = cue.duration ?? params.duration ?? (cue.name === 'wave' ? 60 : 8);
    u.end = (params.end === 'away' || params.end === -1 || params === -1 || params === 'away') ? -1 : 1;
    u.speed = Number.isFinite(params.speed) ? params.speed : 12;
  }
  return u;
}
