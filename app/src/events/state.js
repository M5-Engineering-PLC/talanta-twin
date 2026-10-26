export function durationOf(cues) { return Math.max(0, ...cues.map(c => c.start + c.duration)); }
export function cueAt(cues, seconds) {
  if (!Number.isFinite(seconds)) throw new Error('Invalid event time');
  const duration = durationOf(cues);
  if (!duration) throw new Error('Empty event timeline');
  const time = ((seconds % duration) + duration) % duration;
  const cue = cues.find(c => time >= c.start && time < c.start + c.duration);
  if (!cue) throw new Error('Event timeline has a gap');
  return { time, duration, cue, progress: (time - cue.start) / cue.duration };
}
export function reactionsAt(cues, time) {
  return cues.filter(c => time >= c.start && time < c.start + c.duration && c.params.reaction)
    .map(c => ({ start: c.start, duration: c.duration, name: c.params.reaction,
      params: { duration: c.duration, ...(c.params.end === undefined ? {} : { end: c.params.end }), ...(c.params.reaction === 'phones' ? { on: true } : {}) } }));
}
// Stable hash: no random global state or dependency on sampling order.
export function seeded(index, seed = 713) {
  let v = Math.imul(index + seed, 0x45d9f3b);
  v = Math.imul(v ^ v >>> 16, 0x45d9f3b);
  return ((v ^ v >>> 16) >>> 0) / 4294967296;
}
// Zero-tangent cubic Hermite spline. It cannot overshoot the keyframe bounds.
export function pathAt(keys, t) {
  const i = Math.max(0, keys.findIndex(k => k.time > t) - 1);
  if (t >= keys.at(-1).time) return keys.at(-1).position.slice();
  const a = keys[i], b = keys[i + 1];
  const u = Math.max(0, Math.min(1, (t - a.time) / (b.time - a.time)));
  const s = u * u * (3 - 2 * u);
  return a.position.map((v, axis) => v + (b.position[axis] - v) * s);
}
// Each reaction fires once when a frame crosses its cue, including across loop boundaries.
export function crossedReactions(cues, from, to) {
  if (to < from) return [];
  const duration = durationOf(cues), out = [];
  for (let loop = Math.floor(from / duration); loop <= Math.floor(to / duration); loop++) {
    for (const cue of cues) {
      const at = loop * duration + cue.start;
      if (at > from && at <= to && cue.params.reaction) out.push({ name: cue.params.reaction,
        params: { duration: cue.duration, ...(cue.params.end === undefined ? {} : { end: cue.params.end }), ...(cue.params.reaction === 'phones' ? { on: true } : {}) } });
    }
  }
  return out;
}
