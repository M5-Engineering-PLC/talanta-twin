// Pitch-local metres: x across, y up, z south. The host applies -pitch_bearing_deg.
export const EVENT_FRAME = 'pitch-local x across, y up, z south, m; origin pitch centre; 105 x 68 m assumed';
export const concert_cues = [
  // pattern: LED content index in concert-led.js (0 wash, 1 rising bars, 2 pulse, 3 sweep, 4 fade). Reactions drive the floor and stands.
  { start: 0, duration: 10, module: 'EVT-01', params: { mode: 'dark intro', bpm: 120, energy: .08, color: [0.12, .16, .8], pattern: 0, reaction: 'phones' } },
  { start: 10, duration: 14, module: 'EVT-01', params: { mode: 'build', bpm: 120, energy: .4, color: [.6, .08, .8], pattern: 1, reaction: 'cheer' } },
  { start: 24, duration: 12, module: 'EVT-01', params: { mode: 'drop', bpm: 120, energy: 1, color: [.08, .75, 1], pattern: 2, reaction: 'cheer' } },
  { start: 36, duration: 16, module: 'EVT-01', params: { mode: 'chorus', bpm: 120, energy: .8, color: [1, .18, .4], pattern: 3, reaction: 'wave' } },
  { start: 52, duration: 8, module: 'EVT-01', params: { mode: 'outro', bpm: 120, energy: .15, color: [.2, .3, .8], pattern: 4, reaction: 'phones' } },
];

const formation = [[0, 48], [-23, 30], [-8, 32], [8, 32], [23, 30], [-22, 12], [-7, 14], [7, 14], [22, 12], [-9, 2], [9, 2]];
// Keyframes use bounded Hermite splines. All timing and path targets live here.
const phases = [
  { start: 0, duration: 8, mode: 'kick-off', advance: 0 },
  { start: 8, duration: 22, mode: 'build-up', advance: 10 },
  { start: 30, duration: 20, mode: 'attack', advance: 20 },
  { start: 50, duration: 10, mode: 'shot', advance: 28 },
  { start: 60, duration: 4, mode: 'goal', advance: 28, reaction: 'goal', end: -1 },
  { start: 64, duration: 12, mode: 'celebration', advance: 30 },
  { start: 76, duration: 14, mode: 'restart', advance: 0 },
];
const playerPaths = Array.from({ length: 22 }, (_, id) => {
  const home = id < 11, slot = id % 11, [x, z] = formation[slot], sign = home ? 1 : -1;
  const keys = phases.map(p => {
    const shift = slot === 0 ? 0 : p.advance * (home ? 1 : .35);
    const celebrating = home && slot > 7 && p.mode === 'celebration';
    return { time: p.start, position: celebrating ? [x * .35, .12, -43 + slot % 3] : [x * sign, .12, sign * z - shift] };
  });
  keys.push({ time: 90, position: keys[0].position.slice() });
  return { id, team: home ? 'home' : 'away', color: home ? '#b92332' : '#18733d', keys };
});
export const match_cues = phases.map((p, i) => ({
  start: p.start, duration: p.duration, module: 'SPT-01',
  params: { mode: p.mode, ...(p.reaction ? { reaction: p.reaction, end: p.end } : {}),
    ...(i === 0 ? { playerPaths, refereePath: [
      { time: 0, position: [-5, .12, 0] }, { time: 30, position: [-10, .12, -10] },
      { time: 60, position: [-12, .12, -28] }, { time: 76, position: [-5, .12, 0] }, { time: 90, position: [-5, .12, 0] },
    ], ballPath: [
      { time: 0, position: [0, .24, 0] }, { time: 4, position: [9, .24, 2] },
      { time: 8, position: [-7, .24, -4] }, { time: 18, position: [-22, .24, -12] },
      { time: 30, position: [7, .24, -20] }, { time: 42, position: [22, .24, -26] },
      { time: 50, position: [9, .24, -32] }, { time: 57, position: [3, .24, -43] },
      { time: 59.7, position: [0, 1.1, -52.4] }, { time: 60, position: [0, 1, -53.4] },
      { time: 64, position: [0, .24, -53.4] }, { time: 76, position: [0, .24, 0] },
      { time: 82, position: [-9, .24, -2] }, { time: 90, position: [0, .24, 0] },
    ], goalTime: 60, ballResetTime: 64, restartTime: 76, goalEnd: -1 } : {}),
  },
}));
