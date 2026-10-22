export const limits = (width = 1024) => ({ drones: width < 768 ? 200 : 480, lights: width < 768 ? 2 : 4 });
export function flagBand(angle) {
  const f = ((angle / (Math.PI * 2)) % 1 + 1) % 1;
  return f < 0.3 ? 'black' : f < 0.35 ? 'white' : f < 0.65 ? 'red' : f < 0.7 ? 'white' : 'green';
}
export const palette = { black: [0.012, 0.012, 0.012], white: [1, 1, 1], red: [1, 0.015, 0.025], green: [0.01, 0.65, 0.08] };
const letters = { T: ['11111','00100','00100','00100','00100','00100','00100'], A: ['01110','10001','10001','11111','10001','10001','10001'], L: ['10000','10000','10000','10000','10000','10000','11111'], N: ['10001','11001','11001','10101','10011','10011','10001'] };
export function shapePoints(shape, count) {
  if (!Number.isInteger(count) || count < 1) throw new Error('Invalid drone count');
  let cells = [];
  if (shape === 'TALANTA') [...shape].forEach((letter, k) => letters[letter].forEach((row, y) => [...row].forEach((v, x) => { if (v === '1') cells.push([(k * 6 + x - 20) * 3.2, 150 - y * 4, -20]); })));
  else if (!['flag', 'shield'].includes(shape)) throw new Error('Unknown drone shape');
  return Array.from({ length: count }, (_, i) => {
    const u = (i + 0.5) / count;
    if (shape === 'TALANTA') return { position: [...cells[Math.floor(u * cells.length)]], color: palette.white };
    if (shape === 'shield') { const a = u * Math.PI * 2; return { position: [27 * Math.sin(a) * Math.abs(Math.sin(a)), 130 + 45 * Math.cos(a), -20], color: Math.abs(Math.sin(a)) < 0.2 ? palette.white : Math.sin(a) > 0 ? palette.red : palette.black }; }
    const cols = Math.ceil(Math.sqrt(count * 1.5)), rows = Math.ceil(count / cols), row = Math.floor(i / cols);
    return { position: [(i % cols) / (cols - 1) * 120 - 60, 160 - row / Math.max(1, rows - 1) * 75, -20], color: palette[flagBand((row / rows) * Math.PI * 2)] };
  });
}
const smooth = x => { x = Math.max(0, Math.min(1, x)); return x * x * (3 - 2 * x); };
// Shapes depend only on the drone count, so build them once per count.
const shapeCache = new Map();
export function droneFrame(time, count, duration = 32) {
  const p = Math.max(0, Math.min(1, time / duration));
  if (!shapeCache.has(count)) shapeCache.set(count, ['flag', 'shield', 'TALANTA'].map(s => shapePoints(s, count)));
  const sets = shapeCache.get(count);
  const phase = p < 0.4 ? 0 : p < 0.65 ? 1 : 2;
  return sets[phase].map((target, i) => {
    const launch = [165 + (i % 20) * 1.7, 1.5, 20 + Math.floor(i / 20) * 1.7];
    let from = launch, to = target.position, t = smooth(p / 0.2);
    if (p >= 0.4 && p < 0.65) { from = sets[0][i].position; t = smooth((p - 0.4) / 0.1); }
    if (p >= 0.65 && p < 0.85) { from = sets[1][i].position; t = smooth((p - 0.65) / 0.1); }
    if (p >= 0.85) { from = sets[2][i].position; to = launch; t = smooth((p - 0.85) / 0.15); }
    return { position: from.map((v, k) => v * (1 - t) + to[k] * t), color: target.color };
  });
}
