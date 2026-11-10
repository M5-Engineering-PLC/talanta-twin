import { match_cues, EVENT_FRAME } from './cues.js';
import { cueAt, reactionsAt, pathAt } from './state.js';
export function matchState(cues = match_cues, t = 0) {
  const { time, duration, cue } = cueAt(cues, t), data = cues[0].params;
  const actor = (path, id, color) => {
    const position = pathAt(path, time), ahead = pathAt(path, Math.min(duration, time + .05));
    return { id, position, heading: Math.atan2(ahead[0] - position[0], ahead[2] - position[2]),
      phase: time * 9 + id, color, celebrating: cue.params.mode === 'celebration' && id >= 8 && id < 11 };
  };
  // At ballResetTime the ball is placed at centre for the restart, without crossing the field during the celebration.
  const ball = time >= data.ballResetTime && time < data.restartTime ? [0, .24, 0] : pathAt(data.ballPath, time);
  // Keep the shot inside the goal line until the goal cue starts.
  if (time < data.goalTime) ball[2] = Math.max(-52.5, ball[2]);
  return { module: 'SPT-01', frame: EVENT_FRAME, time, duration, phase: cue.params.mode,
    players: data.playerPaths.map(p => ({ ...actor(p.keys, p.id, p.color), team: p.team })),
    referee: actor(data.refereePath, 22, '#111111'), ball: { position: ball, phase: time * 12 },
    score: [time >= data.goalTime ? 1 : 0, 0], goalEnd: data.goalEnd, crowdReactions: reactionsAt(cues, time) };
}
