// Loads the files written by gis/scripts/export_web.py.
const base = './data/';

async function bin(name, Type, onProgress) {
  const r = await fetch(base + name);
  if (!r.ok) throw new Error(`missing ${name}`);
  const buf = await r.arrayBuffer();
  onProgress?.();
  return new Type(buf);
}

export async function loadData(onProgress) {
  const m = await (await fetch(base + 'manifest.json')).json();
  const tick = () => onProgress?.();
  const jobs = {
    terrain: Promise.all(m.terrain.map((t) => bin(t.file, Float32Array, tick))),
    bPos: bin(m.buildings.pos, Float32Array, tick),
    bCol: bin(m.buildings.col, Uint8Array, tick),
    bIdx: bin(m.buildings.idx, Uint32Array, tick),
    rPos: bin(m.roads.pos, Float32Array, tick),
    rW: bin(m.roads.w, Float32Array, tick),
    rIdx: bin(m.roads.idx, Uint32Array, tick),
    trees: bin(m.trees.file, Float32Array, tick),
  };
  const out = { manifest: m };
  for (const [k, p] of Object.entries(jobs)) out[k] = await p;
  return out;
}

export const TOTAL_FILES = 10;
