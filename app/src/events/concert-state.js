import { concert_cues, EVENT_FRAME } from './cues.js';
import { cueAt, reactionsAt, seeded } from './state.js';

// EVT-01. Pure and deterministic: no clock, no random global state, no scene access.
// Event frame: pitch-local metres, x across, y up, z south. The stage is at the south end (z > 0) and faces north.
// Illustrative event concept. Installed equipment and operational feasibility are not confirmed.

// Floor crowd areas keep to the pitch (105 x 68 m assumed) and keep a clear aisle at the catwalk.
export const PITCH_HALF = { x: 34, z: 52.5 };
export const STAGE = { width: 60, deckHeight: 1.8, depth: 11, centreZ: 46, backZ: 51.5, frontZ: 40.5 };
export const CATWALK = { halfWidth: 2, fromZ: 35.7, toZ: 16, top: 2.3 };
export const BSTAGE = { halfWidth: 5, centreZ: 12, depth: 8, height: 8.3 };
// Metres kept clear of the floor crowd on each side of the catwalk, and around the B-stage.
export const AISLE = { halfWidth: 4.5, bstageHalfWidth: 7.5, fromZ: 38.5, toZ: 4, bstageFromZ: 18 };
export const FLOOR = { xMin: -31, xMax: 31, zFront: 38.5, zBack: -32, zSplitA: 20, zSplitB: -4, share: [.42, .33, .25] };
// Triangles of each part, from the optimised models and the procedural geometry.
export const PART_COST = {
  stageModel: { draws: 4, triangles: 20760 }, trussModel: { draws: 2, triangles: 24480 }, bstageModel: { draws: 1, triangles: 6452 },
  tile: { triangles: 876 }, fixture: { triangles: 1803 }, beam: { triangles: 12 }, bar: { triangles: 12 }, speaker: { triangles: 12 },
  figureLod1: 82, backdrop: 256, wing: 192,
};

const BUDGETS = {
  high: { floor: 5000, heads: 16, tiles: 48, bars: 24, cabinets: 12 },
  medium: { floor: 2000, heads: 12, tiles: 24, bars: 16, cabinets: 10 },
  low: { floor: 700, heads: 8, tiles: 12, bars: 8, cabinets: 8 },
};
// "crowd" is the standing floor crowd count. It keeps that name for the host and the older tests.
export function concertBudget(tier = 'high', width = 1024) {
  const base = BUDGETS[tier] ?? BUDGETS.low, phone = width < 768;
  return { crowd: phone ? Math.floor(base.floor / 2) : base.floor, heads: phone ? 8 : base.heads, lights: 0,
    tiles: phone ? Math.min(base.tiles, 12) : base.tiles, bars: phone ? Math.min(base.bars, 8) : base.bars,
    cabinets: phone ? Math.min(base.cabinets, 8) : base.cabinets };
}
// Draw calls and triangles the concert adds on top of the bowl. An estimate, not a GPU measurement.
export function concertCost(budget = concertBudget()) {
  const c = PART_COST;
  const draws = c.stageModel.draws + c.trussModel.draws + c.bstageModel.draws + 2 /* tiles: face, frame */ + 2 /* fixtures, beams */
    + 1 /* light bars */ + 1 /* speakers */ + 3 /* backdrop, two wings */ + 4 /* floor crowd zones */ + 1 /* performer */ + 2 /* catwalk, thrust */;
  // Standing fans use the 82 triangle figure only: the people module has no camera hook for standing crowds.
  const triangles = c.stageModel.triangles + c.trussModel.triangles + c.bstageModel.triangles + budget.tiles * c.tile.triangles
    + budget.heads * (c.fixture.triangles + c.beam.triangles) + budget.bars * c.bar.triangles + 2 * budget.cabinets * c.speaker.triangles
    + c.backdrop + 2 * c.wing + (budget.crowd + 1) * c.figureLod1 + 24;
  return { draws, triangles };
}

// Floor crowd zones: dense at the stage, sparser to the back. Polygons are [[x, z], ...] in the event frame.
export function floorZones(count = 0) {
  const { xMin, xMax, zFront, zBack, zSplitA, zSplitB } = FLOOR, a = AISLE;
  const nA = Math.round(count * FLOOR.share[0]), nB = Math.round(count * FLOOR.share[1]), nC = count - nA - nB, nL = Math.floor(nA / 2);
  const area = poly => Math.abs(poly.reduce((s, p, i) => { const q = poly[(i + 1) % poly.length]; return s + p[0] * q[1] - q[0] * p[1]; }, 0)) / 2;
  const zones = [
    { id: 'front-left', count: nL, polygon: [[xMin, zSplitA], [-a.halfWidth, zSplitA], [-a.halfWidth, zFront], [xMin, zFront]] },
    { id: 'front-right', count: nA - nL, polygon: [[a.halfWidth, zSplitA], [xMax, zSplitA], [xMax, zFront], [a.halfWidth, zFront]] },
    // The middle zone wraps the B-stage and keeps the aisle clear down to its end.
    { id: 'middle', count: nB, polygon: [[xMin, zSplitB], [xMax, zSplitB], [xMax, zSplitA], [a.bstageHalfWidth, zSplitA], [a.bstageHalfWidth, a.toZ],
      [-a.bstageHalfWidth, a.toZ], [-a.bstageHalfWidth, zSplitA], [xMin, zSplitA]] },
    { id: 'back', count: nC, polygon: [[xMin, zBack], [xMax, zBack], [xMax, zSplitB], [xMin, zSplitB]] },
  ];
  return zones.map(z => ({ ...z, area: area(z.polygon), density: z.count / area(z.polygon) }));
}

// The flown grid hangs in front of the backdrop. Tiles are 2 m square and face north.
function flownTiles(count) {
  const columns = Math.min(12, Math.max(6, Math.ceil(count / 4))), spacing = 50 / (columns - 1);
  return Array.from({ length: count }, (_, i) => ({
    position: [(i % columns - (columns - 1) / 2) * spacing, 15.2 - Math.floor(i / columns) * 2.35, 44.6], size: [2, 2, .2], phase: seeded(i, 17) }));
}
function lightBars(count) {
  return Array.from({ length: count }, (_, i) => ({ position: [(i % 8 - 3.5) * 7, 16.8 - Math.floor(i / 8) * .6, 43.4], size: [5.5, .35, .35], phase: seeded(i, 31) }));
}
function lineArrays(cabinets) {
  const out = [];
  for (const side of [-1, 1]) for (let i = 0; i < cabinets; i++) {
    out.push({ position: [side * 32.5, 15.8 - i * .62, 43.4], size: [1.3, .58, .9], heading: side * .12, tilt: i * .018 });
  }
  return out;
}

export function concertState(cues = concert_cues, t = 0, budget = concertBudget()) {
  const { time, duration, cue, progress } = cueAt(cues, t);
  const beat = time * cue.params.bpm / 60, pulse = .25 + .75 * Math.exp(-6 * (beat % 1));
  const energy = cue.params.energy * (cue.params.mode === 'outro' ? 1 - progress : 1);
  const lights = Array.from({ length: budget.heads }, (_, i) => ({
    position: [-24 + 48 * i / Math.max(1, budget.heads - 1), 16, 42.6],
    // Beams sweep the floor crowd and the stage. Targets stay inside the pitch.
    target: [Math.sin(beat * .45 + i * .7) * 27, 1, 8 + Math.cos(beat * .3 + i) * 24],
    color: cue.params.color.slice(), intensity: energy * pulse,
    phase: (beat + i / budget.heads) % 1,
  }));
  const tint = (k, scale = 1) => cue.params.color.map((v, c) => v * (c === 0 ? k : c === 1 ? .9 : 1) * scale);
  const intensity = .1 + energy * pulse * 2;
  const stage = { position: [0, .12, STAGE.centreZ], size: [STAGE.width, STAGE.deckHeight, STAGE.depth], heading: Math.PI, backZ: STAGE.backZ };
  const backdrop = { position: [0, STAGE.deckHeight + 7, 49.6], size: [60, 14, .35], heading: Math.PI };
  const wings = [-1, 1].map(side => ({ id: side < 0 ? 'wing-left' : 'wing-right', position: [side * 34, STAGE.deckHeight + 6, 46.5],
    size: [9, 12, .3], radius: 12, arc: .75, yaw: side * .45 }));
  return { module: 'EVT-01', frame: EVENT_FRAME, time, duration, phase: cue.params.mode, beat, pulse,
    stage,
    truss: { position: [0, STAGE.deckHeight + .2, 46.5], width: 56, height: 15.4, depth: 9.4, ceiling: 17.55 },
    catwalk: { position: [0, CATWALK.top / 2, (CATWALK.fromZ + CATWALK.toZ) / 2], size: [CATWALK.halfWidth * 2, CATWALK.top, CATWALK.fromZ - CATWALK.toZ] },
    bstage: { position: [0, 0, BSTAGE.centreZ], size: [BSTAGE.halfWidth * 2, BSTAGE.height, BSTAGE.depth] },
    backdrop, wings,
    // Procedural LED content: the pattern index follows the cue, the rest follows the beat.
    led: { pattern: cue.params.pattern ?? 0, beat, pulse, energy, color: cue.params.color.slice() },
    screens: [
      { id: 'backdrop', position: backdrop.position, size: backdrop.size, color: tint(1), intensity },
      ...wings.map(w => ({ id: w.id, position: w.position, size: w.size, color: tint(.8, .9), intensity: intensity * .9 })),
    ],
    flown: flownTiles(budget.tiles), bars: lightBars(budget.bars), speakers: lineArrays(budget.cabinets),
    floor: { count: budget.crowd, zones: floorZones(budget.crowd), aisle: { ...AISLE }, y: .12 },
    // One generic performer on the thrust. No likeness, name, logo or text.
    performer: { position: [0, CATWALK.top, 37], facing_deg: 180, kind: 'generic' },
    lights, crowdReactions: reactionsAt(cues, time), phones: true };
}
