import { droneFrame, faceDronePoint, palette } from './shapes.js';

// Linear RGB, matching THREE.Color's CSS sRGB conversion without a renderer import.
export function linearColor(value = 'white') {
  if (Array.isArray(value)) return [...value];
  if (value && typeof value === 'object') return [value.r, value.g, value.b];
  const names = { white: 0xffffff, black: 0, red: 0xff0000, green: 0x008000, blue: 0x0000ff, yellow: 0xffff00, cyan: 0x00ffff, magenta: 0xff00ff, orange: 0xffa500 };
  let hex = typeof value === 'number' ? value : names[value.toLowerCase()];
  if (hex === undefined && /^#[0-9a-f]{3}$/i.test(value)) hex = parseInt([...value.slice(1)].map(c => c + c).join(''), 16);
  if (hex === undefined && /^#[0-9a-f]{6}$/i.test(value)) hex = parseInt(value.slice(1), 16);
  if (hex === undefined) throw new Error(`Unsupported bridge colour: ${value}`);
  return [16, 8, 0].map(shift => { const c = (hex >> shift & 255) / 255; return c < 0.04045 ? c * 0.0773993808 : Math.pow(c * 0.9478672986 + 0.0521327014, 2.4); });
}

export function ribAttributes(data) {
  return [...data.ribs, data.fascia, data.opening].map((line, index) => ({ index, angle: ((Math.atan2(line[0][2], line[0][0]) / (2 * Math.PI)) + 1) % 1 }));
}

// TSL formula: step(edge,x) = x >= edge. Flag thresholds: .30,.35,.65,.70.
// color = mix(white, flag(angle), step(.5,mode)).
// movement = mix(1, .1 + .9*step(.65,sin(index*.45-time*4)), step(1.5,mode)).
// pulse = mix(movement, .55 + .45*sin(angle*8*pi-time*2), step(2.5,mode)).
// emissive linear RGB = color * pulse * tint * 5 (identical to the GPU path).
export function ribColor(angle, index, mode, time, tint = [1, 1, 1]) {
  const flag = angle < .3 ? palette.black : angle < .35 ? palette.white : angle < .65 ? palette.red : angle < .7 ? palette.white : palette.green;
  const color = mode >= .5 ? flag : palette.white;
  const movement = mode >= 1.5 ? (Math.sin(index * .45 - time * 4) >= .65 ? 1 : .1) : 1;
  const pulse = mode >= 2.5 ? .55 + .45 * Math.sin(angle * Math.PI * 8 - time * 2) : movement;
  return color.map((v, k) => v * pulse * tint[k] * 5);
}

// cues are active Timeline.sample() results. Options preserve the manual app mode.
export function showState(cues, t, data, budget, { scripted = true, enabled = {}, viewer, colors = {} } = {}) {
  const state = id => {
    if (enabled[id] === false) return null;
    const cue = cues.filter(c => c.module === id).at(-1);
    if (scripted) return cue ?? (id === 'SHW-02' ? { params: { mode: 'rest' }, localTime: t } : null);
    return { params: { mode: id === 'SHW-01' ? 'sequence' : 'rest' }, localTime: id === 'SHW-03' ? t % 32 : t };
  };
  const facade = state('SHW-02'), flood = state('SHW-01'), drone = state('SHW-03');
  const mode = ({ flag: 1, chase: 2, wave: 3 })[facade?.params.mode] ?? 0;
  const tint = colors.facade ?? linearColor(facade?.params.color ?? 'white');
  const lightColor = colors.flood ?? linearColor(flood?.params.color ?? 'white');
  const intensities = data.floodlights.map((_, i) => {
    if (!flood) return 0;
    if (flood.params.mode === 'flash') return Math.sin(flood.localTime * Math.PI * 8) >= 0 ? 1 : 0;
    return flood.params.mode === 'sequence' ? +(i / data.floodlights.length <= Math.min(1, flood.localTime / 8)) : 1;
  });
  const points = drone ? droneFrame(drone.localTime, budget.drones, drone.duration ?? 32) : [];
  return {
    'SHW-01': { visible: !!flood, color: lightColor, intensity: intensities, rgb: intensities.flatMap(v => lightColor.map(c => c * v)) },
    'SHW-02': { visible: !!facade, mode, tint, rgb: ribAttributes(data).flatMap(r => ribColor(r.angle, r.index, mode, t, tint)) },
    'SHW-03': { visible: !!drone, position: points.flatMap(p => faceDronePoint(p.position, viewer)), rgb: points.flatMap(p => p.color) },
  };
}
