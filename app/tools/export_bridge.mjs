#!/usr/bin/env node
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { resolve, join, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { fallbackFacadeLines, validFacadeLines, padY } from '../src/shows/geometry.js';
import { exportModule } from '../src/bridge/export.js';
import { generateSeats } from '../src/people/seats.js';

const appDir = resolve(dirname(fileURLToPath(import.meta.url)), '..');
export async function loadGeometry(publicDir = join(appDir, 'public')) {
  try {
    const data = JSON.parse(await readFile(join(publicDir, 'data/facade_lines.json'), 'utf8'));
    if (validFacadeLines(data)) return { data, geometrySource: 'data/facade_lines.json' };
    return { data: fallbackFacadeLines(), geometrySource: 'fallback: invalid data/facade_lines.json (same app validation)' };
  } catch (error) {
    if (error.code !== 'ENOENT' && !(error instanceof SyntaxError)) throw error;
    return { data: fallbackFacadeLines(), geometrySource: `fallback: ${error.code === 'ENOENT' ? 'missing' : 'invalid JSON'} data/facade_lines.json` };
  }
}

// Generate seats without constructing bowl geometry or canvas textures.
// Match people/index.js fromMesh() metadata in the bowl.group parent frame.
export async function loadCrowdSeats() {
  const { features } = JSON.parse(await readFile(join(appDir, 'public/data/manifest.json'), 'utf8'));
  return generateSeats(features).map(seat => ({
    x: Math.fround(seat.x), y: Math.fround(seat.y), z: Math.fround(seat.z),
    facing_deg: ((seat.facing_deg + 540) % 360) - 180,
    tier: 0, row: Math.round(Math.fround(seat.y) * 100),
  }));
}

export function parseArgs(args) {
  const allowed = new Set(['module', 'fps', 'out', 'start', 'duration', 'drones', 'viewer', 'cues', 'fill', 'width', 'night']);
  const parsed = {};
  for (let i = 0; i < args.length; i += 2) {
    const key = args[i].slice(2);
    if (!args[i].startsWith('--') || !allowed.has(key) || args[i + 1] === undefined || parsed[key] !== undefined) throw new Error(`Invalid argument: ${args[i]}`);
    parsed[key] = args[i + 1];
  }
  if (!['SHW-01', 'SHW-02', 'SHW-03', 'PPL-02', 'night_show'].includes(parsed.module) || !parsed.out) throw new Error('Usage: node app/tools/export_bridge.mjs --module SHW-01|SHW-02|SHW-03|PPL-02|night_show --fps 24 --out <dir> [--start s] [--duration s] [--drones N] [--viewer x,y,z] [--cues file.json] [--fill 1] [--width 1024] [--night 0|1]');
  const result = { module: parsed.module, out: resolve(parsed.out), fps: Number(parsed.fps ?? 24), start: Number(parsed.start ?? 0), duration: Number(parsed.duration ?? 60), drones: Number(parsed.drones ?? 480), fill: Number(parsed.fill ?? 1), width: Number(parsed.width ?? 1024), night: parsed.night === '1', cuesFile: parsed.cues };
  if (parsed.night !== undefined && !['0', '1'].includes(parsed.night)) throw new Error('night must be 0 or 1');
  if (!Number.isFinite(result.fill) || result.fill < 0 || result.fill > 1 || !Number.isFinite(result.width) || result.width <= 0) throw new Error('Invalid crowd fill or width');
  if (parsed.viewer) {
    const coords = parsed.viewer.split(',').map(Number);
    if (coords.length !== 3 || !coords.every(Number.isFinite)) throw new Error('viewer must be x,y,z');
    result.viewer = Object.fromEntries(['x', 'y', 'z'].map((k, i) => [k, coords[i]]));
  }
  return result;
}

export async function writeExport(out, exported) {
  await mkdir(out, { recursive: true });
  const { header, bytes } = exported;
  await writeFile(join(out, header.binary), bytes);
  const json = JSON.stringify(header, null, 2) + '\n';
  await writeFile(join(out, `${header.module}.json`), json);
  return { module: header.module, frames: header.frame_count, fps: header.fps, json_bytes: Buffer.byteLength(json), bin_bytes: bytes.length };
}

export async function main(args = process.argv.slice(2)) {
  const options = parseArgs(args), geometry = await loadGeometry();
  let sourceCommit = null;
  try { sourceCommit = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: appDir, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim(); } catch { /* A copied cloud folder can lack Git metadata. */ }
  const cues = options.cuesFile ? JSON.parse(await readFile(options.cuesFile, 'utf8')) : [];
  if (!Array.isArray(cues) || cues.some(c => !['cheer', 'goal', 'wave', 'scarves', 'phones'].includes(c.name) || !Number.isFinite(c.start) || c.start < 0 || !Number.isFinite(c.duration) || c.duration <= 0)) throw new Error('Cues require name, nonnegative start, positive duration, and optional params');
  const seats = options.module === 'PPL-02' ? await loadCrowdSeats() : undefined;
  for (const module of options.module === 'night_show' ? ['SHW-01', 'SHW-02', 'SHW-03'] : [options.module]) {
    const exported = exportModule({ ...options, ...geometry, module, pad: padY, sourceCommit, seats, cues });
    // The commit identifies the base. This worker deliberately leaves code uncommitted.
    exported.header.source_state = 'working-tree; source_commit identifies base only';
    console.log(JSON.stringify(await writeExport(options.out, exported)));
  }
}
if (process.argv[1] && pathToFileURL(resolve(process.argv[1])).href === import.meta.url) main().catch(error => { console.error(error.message); process.exitCode = 1; });
